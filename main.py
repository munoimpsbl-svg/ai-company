import csv
from datetime import date, datetime
import io
import os
from pathlib import Path
import subprocess
import sys

import streamlit as st

from core.config import load_config
from core.generation_quality import load_generation_quality, update_generation_quality
from core.sns_drive_input import (
    DRIVE_INPUT_LABEL,
    list_drive_csv_files,
    manifest_path,
    read_drive_text,
    result_path as sns_drive_result_path,
    sync_drive_inputs,
    upload_drive_csv,
)
from core.sns_analytics import MIKU_X_TARGET, SocialPlatform, analyze_sns_target


WORKSPACE_ROOT = Path(__file__).resolve().parent
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

INPUTS = {
    "KPI Dashboard": Path("KPI_DASHBOARD.md"),
    "P002 Daily Brief": Path("03_SNS事業部") / "04_Daily" / "DAILY_BRIEF.md",
    "P003 Daily Brief": Path("04_グラビア事業部") / "DAILY_BRIEF.md",
}

P003_PROJECT_DIR = Path("01_グラビア事業部") / "P003_グラビア事業部"
P003_COMMAND_DIR = Path("04_グラビア事業部")
TODAY_POST_PATH = Path("03_SNS事業部") / "04_Daily" / "TODAY_POST.md"
APPROVALS_PATH = P003_COMMAND_DIR / "APPROVALS.md"
COMMAND_BACKLOG_PATH = P003_COMMAND_DIR / "IMPROVEMENT_BACKLOG.md"
COMMAND_BOARD_PATH = P003_COMMAND_DIR / "EXECUTION_BOARD.md"
IMPROVEMENT_BACKLOG_PATH = (
    COMMAND_BACKLOG_PATH
    if (WORKSPACE_ROOT / COMMAND_BACKLOG_PATH).exists()
    else P003_PROJECT_DIR / "IMPROVEMENT_BACKLOG.md"
)
EXECUTION_BOARD_PATH = (
    COMMAND_BOARD_PATH
    if (WORKSPACE_ROOT / COMMAND_BOARD_PATH).exists()
    else P003_PROJECT_DIR / "EXECUTION_BOARD.md"
)
IMPROVEMENT_INPUTS = {
    "Improvement Backlog": IMPROVEMENT_BACKLOG_PATH,
    "Execution Board": EXECUTION_BOARD_PATH,
    "P003 Task": P003_PROJECT_DIR / "TASK.md",
    "Approvals": APPROVALS_PATH,
}


def main() -> None:
    st.set_page_config(page_title="Editor Dashboard", page_icon=None, layout="wide")
    _inject_styles()
    _require_dashboard_auth()

    page = st.radio(
        "画面",
        ("Command Center", "SNS Today", "SNS Input Manager", "SNS Analytics", "GPT Image Quality"),
        horizontal=True,
        label_visibility="collapsed",
    )
    if page == "SNS Today":
        _render_sns_today_page()
        return
    if page == "SNS Input Manager":
        _render_sns_input_manager_page()
        return
    if page == "SNS Analytics":
        _render_sns_analytics_page()
        return
    if page == "GPT Image Quality":
        _render_generation_quality_page()
        return

    latest_daily_dir = _latest_daily_output_dir()
    ceo_path = _latest_artifact("CEO_REPORT.md", latest_daily_dir)
    run_path = _latest_artifact("RUN_REPORT.md", latest_daily_dir)
    paths = {
        **INPUTS,
        **IMPROVEMENT_INPUTS,
        "CEO Report": ceo_path,
        "Run Report": run_path,
    }
    docs = {name: _read_text(path) for name, path in paths.items()}
    dashboard = _build_dashboard_data(docs, paths, latest_daily_dir)

    st.markdown("# AI COMPANY")
    st.caption("表示専用。更新、投稿、削除は行いません。")

    with st.sidebar:
        _render_notification_center(dashboard)
        _render_action_center(paths)

    _render_system_cards(dashboard)
    _render_kpi_cards(dashboard["kpi"])

    _render_top3(dashboard["top3"])
    _render_improvement_board(dashboard["improvements"])

    left, right = st.columns([1, 1], gap="large")
    with left:
        _render_blockers(dashboard["blockers"])
    with right:
        _render_ceo_comment(dashboard["ceo_comment"])

    _render_image_candidates(dashboard["images"])

    _render_detail_reports(docs, paths)
    _render_approval_history(docs["Approvals"], paths["Approvals"])


def _build_dashboard_data(docs, paths, latest_daily_dir):
    return {
        "paths": paths,
        "latest_daily_dir": latest_daily_dir,
        "kpi": _extract_kpi_cards(docs["KPI Dashboard"]),
        "top3": _extract_top3(docs["CEO Report"]),
        "blockers": _extract_blockers(docs["CEO Report"]),
        "ceo_comment": _extract_section(docs["CEO Report"], "CTOコメント") or "未取得",
        "improvements": _extract_improvements(
            docs["Improvement Backlog"],
            docs["Execution Board"],
            docs["P003 Task"],
            docs["Approvals"],
            {
                "backlog": paths["Improvement Backlog"],
                "board": paths["Execution Board"],
                "approvals": paths["Approvals"],
            },
        ),
        "system": _build_system_state(docs, paths),
        "images": {
            "MIKU": _find_character_images("MIKU", latest_daily_dir),
            "RIO": _find_character_images("RIO", latest_daily_dir),
        },
        "notifications": _build_notifications(
            docs,
            _extract_kpi_cards(docs["KPI Dashboard"]),
            _extract_blockers(docs["CEO Report"]),
            latest_daily_dir,
        ),
    }


def _render_notification_center(dashboard) -> None:
    st.markdown("## 通知センター")
    cols = st.columns(len(dashboard["notifications"]))
    for column, item in zip(cols, dashboard["notifications"]):
        column.markdown(
            f"""
            <div class="notice {item["tone"]}">
              <div class="notice-title">{item["icon"]} {item["title"]}</div>
              <div class="notice-body">{item["body"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_action_center(paths) -> None:
    st.markdown("## 操作")
    action_cols = st.columns(6)
    actions = [
        ("Runner実行", [sys.executable, "06_AI_COMPANY_Runner/main.py"]),
        ("KPI更新", [sys.executable, "generate_kpi_dashboard.py"]),
        ("CEO_REPORT再生成", [sys.executable, "05_AI社長/main.py"]),
    ]
    for column, (label, command) in zip(action_cols[:3], actions):
        if column.button(label, width="stretch"):
            st.session_state["action_result"] = _run_local_command(command)

    report_buttons = [
        ("RUN_REPORTを開く", "Run Report"),
        ("KPI_DASHBOARDを開く", "KPI Dashboard"),
        ("CEO_REPORTを開く", "CEO Report"),
    ]
    for column, (label, report_name) in zip(action_cols[3:], report_buttons):
        if column.button(label, width="stretch"):
            st.session_state["detail_focus"] = report_name

    if st.session_state.get("action_result"):
        result = st.session_state["action_result"]
        if result["success"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
        with st.expander("実行ログ"):
            st.code(result["output"] or "なし", language="text")

    link_cols = st.columns(2)
    wordpress_url = _wordpress_url()
    admin_url = _wordpress_admin_url(wordpress_url)
    link_cols[0].link_button(
        "WordPressサイトを開く",
        wordpress_url or "https://example.com",
        disabled=not bool(wordpress_url),
        width="stretch",
    )
    link_cols[1].link_button(
        "WordPress管理画面を開く",
        admin_url or "https://example.com",
        disabled=not bool(admin_url),
        width="stretch",
    )


def _render_sns_today_page() -> None:
    st.markdown("# SNS Today")
    st.caption("手動投稿の確認・記録画面です。自動投稿やSNSログイン操作は行いません。")

    content = _read_text(TODAY_POST_PATH)
    posts = _parse_today_posts(content)
    output_date = _today_post_date(content)
    result_path = Path("02_Daily_Output") / output_date / "POST_RESULT.md"
    results = _parse_post_results(_read_text(result_path))

    with st.sidebar:
        st.markdown("## 投稿補助")
        st.caption(f"素材日: {output_date}")
        st.caption(f"結果: {result_path}")
        if st.button("表示を更新", width="stretch"):
            st.rerun()

    if not posts:
        st.warning("TODAY_POST.mdを取得できません。P002を実行してください。")
        with st.expander("TODAY_POST.md"):
            st.caption(str(TODAY_POST_PATH))
            st.markdown(content or "未取得")
        return

    character_tabs = st.tabs(("MIKU", "RIO"))
    for tab, character in zip(character_tabs, ("MIKU", "RIO")):
        with tab:
            character_posts = [post for post in posts if post["character"] == character]
            if not character_posts:
                st.info(f"{character}の当日素材は未取得です。")
                continue
            for post in character_posts:
                _render_sns_post(post, output_date, result_path, results)

    st.markdown("## 投稿結果")
    st.caption(str(result_path))
    result_content = _read_text(result_path)
    if result_content:
        with st.container(border=True):
            st.markdown(result_content)
    else:
        st.info("投稿結果はまだ記録されていません。")

    with st.expander("TODAY_POST.md"):
        st.caption(str(TODAY_POST_PATH))
        st.markdown(content)


def _render_sns_input_manager_page() -> None:
    st.markdown("# SNS Input Manager")
    st.caption("Google Driveを正データとして扱います。ローカルCSVはDrive同期済みmanifestに載ったものだけ分析対象です。")

    try:
        listing = list_drive_csv_files(WORKSPACE_ROOT)
        folder = listing["folder"]
        files = listing["files"]
        folder_error = ""
    except Exception as exc:
        folder = {}
        files = []
        folder_error = str(exc)

    with st.sidebar:
        st.markdown("## Google Drive")
        st.caption(DRIVE_INPUT_LABEL)
        if folder.get("id"):
            st.link_button(
                "Driveフォルダを開く",
                f"https://drive.google.com/drive/folders/{folder['id']}",
                width="stretch",
            )
        if st.button("Driveから同期", width="stretch"):
            result = sync_drive_inputs(WORKSPACE_ROOT)
            st.session_state["sns_drive_sync"] = result
            st.rerun()

    if folder_error:
        st.error(f"Google Drive入力フォルダを取得できません: {folder_error}")
        return

    sync_result = st.session_state.get("sns_drive_sync")
    if sync_result:
        if sync_result["success"]:
            st.success(f"Drive同期完了: {sum(1 for item in sync_result['rows'] if item['success'])}件")
        else:
            st.error(f"Drive同期失敗: {sync_result['error']}")

    metric_cols = st.columns(4)
    metric_cols[0].metric("正データ", "Google Drive")
    metric_cols[1].metric("Drive CSV", len(files))
    metric_cols[2].metric("削除", "無効")
    metric_cols[3].metric("分析対象", "Manifestのみ")

    st.markdown("## Drive CSV一覧")
    if files:
        st.dataframe(
            [
                {
                    "name": item.get("name", ""),
                    "modifiedTime": item.get("modifiedTime", "未取得"),
                    "mimeType": item.get("mimeType", "未取得"),
                    "driveId": item.get("id", ""),
                }
                for item in files
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Drive入力フォルダにCSVがありません。")

    st.markdown("## CSVを登録 / 上書き")
    uploaded = st.file_uploader("CSVファイル", type=["csv"])
    default_name = uploaded.name if uploaded else f"x_metrics_{date.today().isoformat()}.csv"
    filename = st.text_input("Drive保存ファイル名", value=default_name)
    overwrite = st.checkbox("同名CSVを上書きする", value=False)
    if uploaded:
        content = _decode_uploaded_csv(uploaded.getvalue())
        preview_rows = _csv_preview_rows(content, limit=8)
        if preview_rows:
            st.dataframe(preview_rows, width="stretch", hide_index=True)
        else:
            st.code(content[:2000], language="text")

        if st.button("Google Driveへ保存", width="stretch"):
            try:
                file_data = upload_drive_csv(WORKSPACE_ROOT, filename, content, overwrite=overwrite)
                st.success(f"Driveへ保存しました: {file_data.get('name', filename)}")
                st.rerun()
            except Exception as exc:
                st.error(f"Drive保存に失敗しました: {exc}")

    st.markdown("## CSVプレビュー")
    if files:
        options = {item["name"]: item for item in files}
        selected_name = st.selectbox("プレビュー対象", list(options))
        selected = options[selected_name]
        try:
            content = read_drive_text(selected["id"], selected.get("mimeType", "text/csv"))
            rows = _csv_preview_rows(content, limit=50)
            if rows:
                st.dataframe(rows, width="stretch", hide_index=True)
            else:
                st.code(content[:4000], language="text")
            st.download_button(
                "CSVをダウンロード",
                data=content.encode("utf-8"),
                file_name=selected_name,
                mime="text/csv",
                width="stretch",
            )
        except Exception as exc:
            st.error(f"CSVを読み込めません: {exc}")
    else:
        st.info("プレビュー対象はありません。")

    st.markdown("## 削除")
    st.button("Drive CSVを削除", disabled=True, width="stretch")
    st.caption("削除は運用事故防止のため無効です。不要ファイルはGoogle Drive側で手動整理してください。")

    with st.expander("同期結果 / Manifest"):
        st.markdown("### DRIVE_INPUT_SYNC_RESULT.md")
        st.caption(str(sns_drive_result_path(WORKSPACE_ROOT).relative_to(WORKSPACE_ROOT)))
        st.markdown(_read_text(sns_drive_result_path(WORKSPACE_ROOT).relative_to(WORKSPACE_ROOT)) or "未取得")
        st.markdown("### DRIVE_INPUT_MANIFEST.json")
        st.caption(str(manifest_path(WORKSPACE_ROOT).relative_to(WORKSPACE_ROOT)))
        st.code(_read_text(manifest_path(WORKSPACE_ROOT).relative_to(WORKSPACE_ROOT)) or "未取得", language="json")


def _render_sns_analytics_page() -> None:
    analysis = analyze_sns_target(WORKSPACE_ROOT, MIKU_X_TARGET)
    totals = analysis.totals

    st.markdown("# SNS Analytics")
    st.caption("分析対象はMIKUのXのみです。RIO/Threads分析は現段階では実行しません。")

    with st.sidebar:
        st.markdown("## 対象")
        st.caption(f"キャラクター: {analysis.target.character}")
        st.caption(f"SNS: {analysis.target.platform.value}")
        st.caption(f"入力: {_display_path(analysis.source_dir)}")
        if st.button("表示を更新", width="stretch"):
            st.rerun()

    st.markdown("## MIKU / X")
    status_cols = st.columns(4)
    status_cols[0].metric("状態", analysis.status)
    status_cols[1].metric("読込CSV", len(analysis.source_files))
    status_cols[2].metric("投稿数", int(totals["posts"]))
    status_cols[3].metric("対象外", "RIO / Threads")

    kpi_cols = st.columns(6)
    kpi_cols[0].metric("フォロワー", _format_metric(totals["followers"]))
    kpi_cols[1].metric("インプレッション", _format_metric(totals["impressions"]))
    kpi_cols[2].metric("エンゲージメント", _format_metric(totals["engagement"]))
    kpi_cols[3].metric("ER", f"{totals['engagement_rate']}%")
    kpi_cols[4].metric("リンククリック", _format_metric(totals["link_clicks"]))
    kpi_cols[5].metric("CTR", f"{totals['ctr']}%")

    if analysis.blockers:
        st.warning("\n".join(f"- {blocker}" for blocker in analysis.blockers))

    with st.container(border=True):
        st.markdown("### 入力ファイル")
        if analysis.source_files:
            for source_file in analysis.source_files:
                st.caption(_display_path(source_file))
        else:
            st.info(
                "Google Driveの`AI_COMPANY_INPUT/03_SNS事業部/03_Analytics/MIKU/X/`にXのCSVエクスポートを置いてください。"
            )

    if analysis.best_post:
        best = analysis.best_post
        with st.container(border=True):
            st.markdown("### 反応が強い投稿")
            st.markdown(best.text or best.url or best.post_id or "本文未取得")
            st.caption(
                f"impressions={best.impressions} / engagement={best.engagements} / "
                f"likes={best.likes} / replies={best.replies} / reposts={best.reposts}"
            )
            if best.url:
                st.link_button("投稿を開く", best.url, width="stretch")

    st.markdown("## 投稿別データ")
    if analysis.posts:
        st.dataframe(
            [
                {
                    "date": post.date,
                    "text": post.text,
                    "impressions": post.impressions,
                    "engagement": post.engagements,
                    "likes": post.likes,
                    "replies": post.replies,
                    "reposts": post.reposts,
                    "bookmarks": post.bookmarks,
                    "profile_clicks": post.profile_clicks,
                    "link_clicks": post.link_clicks,
                    "url": post.url,
                }
                for post in analysis.posts
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("投稿別データは未取得です。")

    with st.expander("将来拡張メモ"):
        st.markdown(
            "\n".join(
                [
                    "- 現在の有効ターゲット: MIKU / X",
                    "- SNS種別は `SocialPlatform` で分離済み",
                    f"- 将来候補: RIO / {SocialPlatform.THREADS.value}",
                    "- 現段階ではThreads CSVを読み込まない",
                ]
            )
        )


def _decode_uploaded_csv(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _csv_preview_rows(content: str, limit: int = 20):
    if not content.strip():
        return []
    try:
        sample = content[:4096]
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel
    try:
        reader = csv.DictReader(io.StringIO(content), dialect=dialect)
        if not reader.fieldnames:
            return []
        return [
            {key or "未取得": value for key, value in row.items()}
            for _, row in zip(range(limit), reader)
        ]
    except csv.Error:
        return []


def _render_generation_quality_page() -> None:
    summary = load_generation_quality(WORKSPACE_ROOT)

    st.markdown("# GPT Image Quality")
    st.caption("GPT画像生成候補の品質履歴です。自動採用、自動投稿、画像削除は行いません。")

    with st.sidebar:
        st.markdown("## 品質DB")
        st.caption(_display_path(summary.db_path))
        st.caption(_display_path(summary.report_path))
        if st.button("品質DBを更新", width="stretch"):
            update_generation_quality(WORKSPACE_ROOT)
            st.rerun()

    metric_cols = st.columns(5)
    metric_cols[0].metric("状態", summary.status)
    metric_cols[1].metric("画像候補", summary.scanned_assets)
    metric_cols[2].metric("試行数", summary.experiments)
    metric_cols[3].metric("平均スコア", summary.average_score)
    metric_cols[4].metric("要確認", len(summary.warning_assets))

    if summary.blockers:
        st.warning("\n".join(f"- {blocker}" for blocker in summary.blockers))

    st.markdown("## 要確認候補")
    _render_quality_table(summary.warning_assets)

    st.markdown("## 上位候補")
    _render_quality_table(summary.top_assets)

    with st.expander("評価仕様"):
        st.markdown(
            "\n".join(
                [
                    "- 現段階は軽量評価: 画像読込、解像度、画角、EXIF、prompt/report有無、report内NG記録を採点",
                    "- 評価対象はGPTの画像生成結果のみ",
                    "- 外部画像生成UI、外部画像ストアは今回の対象外",
                    "- 本人感、体型、最終採用、安全判定は社長判断を優先",
                    "- DB: `03_SNS事業部/03_Analytics/generation_quality.sqlite3`",
                    "- レポート: `03_SNS事業部/03_Analytics/GENERATION_QUALITY_REPORT.md`",
                ]
            )
        )


def _render_quality_table(assets) -> None:
    if not assets:
        st.info("対象なし")
        return

    st.dataframe(
        [
            {
                "score": asset.score,
                "status": asset.status,
                "engine": asset.engine,
                "date": asset.output_date,
                "character": asset.character,
                "slot": asset.slot,
                "image": _display_path(asset.path),
                "size": f"{asset.width}x{asset.height}",
                "exif_cleaned": asset.exif_cleaned,
                "adopted_hint": asset.adopted_hint,
                "warnings": " / ".join(asset.warnings),
            }
            for asset in assets
        ],
        width="stretch",
        hide_index=True,
    )


def _render_sns_post(post, output_date: str, result_path: Path, results) -> None:
    slot_label = {
        "morning": "朝",
        "afternoon": "昼",
        "night": "夜",
        "default": "本日",
    }.get(post["slot"], post["slot"])
    st.markdown(f"## {slot_label}の投稿")
    st.markdown(
        f"""
        <div class="sns-theme">
          <div class="sns-theme-label">{post["character"]} / {slot_label}</div>
          <div class="sns-theme-title">{post["theme"]}</div>
          <div class="sns-theme-path">{post["image_folder"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if post["images"]:
        image_cols = st.columns(min(3, len(post["images"])))
        for index, image in enumerate(post["images"]):
            image_path = _safe_workspace_path(image)
            column = image_cols[index % len(image_cols)]
            if image_path and image_path.exists():
                column.image(str(image_path), width="stretch")
                column.caption(image_path.name)
            else:
                column.warning(f"画像未取得: {image}")
    else:
        st.warning("採用画像は未取得です。")

    platform_tabs = st.tabs(("Instagram", "X", "Threads"))
    platform_urls = {
        "Instagram": "https://www.instagram.com/",
        "X": "https://x.com/compose/post",
        "Threads": "https://www.threads.net/",
    }
    for platform_tab, platform in zip(platform_tabs, ("Instagram", "X", "Threads")):
        with platform_tab:
            text = post["post_texts"].get(platform, "未取得")
            st.code(text, language=None, wrap_lines=True)
            st.link_button(
                f"{platform}を開く",
                platform_urls[platform],
                width="stretch",
            )

            record_key = (post["character"], post["slot"], platform)
            recorded = record_key in results
            completed = st.checkbox(
                f"{platform} 投稿完了",
                value=recorded,
                key=f"posted-{post['character']}-{post['slot']}-{platform}",
                disabled=text == "未取得",
            )
            post_url = st.text_input(
                "投稿URL",
                value=results.get(record_key, {}).get("投稿URL", ""),
                key=f"post-url-{post['character']}-{post['slot']}-{platform}",
                placeholder="投稿後のURL",
                disabled=text == "未取得",
            )
            memo = st.text_area(
                "メモ",
                value=results.get(record_key, {}).get("メモ", ""),
                key=f"post-memo-{post['character']}-{post['slot']}-{platform}",
                height=80,
                disabled=text == "未取得",
            )
            if st.button(
                "POST_RESULTへ記録",
                key=f"save-post-{post['character']}-{post['slot']}-{platform}",
                disabled=not completed or text == "未取得",
                width="stretch",
            ):
                result = _save_post_result(
                    result_path=result_path,
                    output_date=output_date,
                    character=post["character"],
                    slot=post["slot"],
                    platform=platform,
                    post_url=post_url,
                    images=post["images"],
                    memo=memo,
                )
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])


def _render_system_cards(dashboard) -> None:
    st.markdown("## システム状態")
    cols = st.columns(5)
    for column, item in zip(cols, dashboard["system"]):
        tone = _status_tone(item["status"])
        column.markdown(
            f"""
            <div class="status-card {tone}">
              <div class="status-icon">{item["icon"]}</div>
              <div class="status-label">{item["label"]}</div>
              <div class="status-value">{item["status"]}</div>
              <div class="status-detail">{item["detail"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_kpi_cards(kpi) -> None:
    st.markdown("## KPI")
    cards = [
        ("WordPress", "記事", kpi.get("posts", "未取得"), "公開記事", kpi.get("published", "未取得"), "green"),
        ("WordPress", "カテゴリ", kpi.get("categories", "未取得"), "タグ", kpi.get("tags", "未取得"), "green"),
        ("Search Console", "クリック", kpi.get("clicks", "未取得"), "表示回数", kpi.get("impressions", "未取得"), "yellow"),
        ("Search Console", "CTR", kpi.get("ctr", "未取得"), "平均順位", kpi.get("position", "未取得"), "yellow"),
        ("GA4", "ユーザー", kpi.get("users", "未取得"), "セッション", kpi.get("sessions", "未取得"), "red"),
        ("GA4", "PV", kpi.get("page_views", "未取得"), "Engagement", kpi.get("engagement_time", "未取得"), "red"),
    ]
    cols = st.columns(6)
    for column, (source, label1, value1, label2, value2, tone) in zip(cols, cards):
        column.markdown(
            f"""
            <div class="kpi-card {tone}">
              <div class="kpi-source">{source}</div>
              <div class="kpi-row"><span>{label1}</span><strong>{value1}</strong></div>
              <div class="kpi-row"><span>{label2}</span><strong>{value2}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_top3(items) -> None:
    st.markdown("## 今日やること TOP3")
    if not items:
        st.info("未取得")
        return

    for index, item in enumerate(items, start=1):
        st.markdown(
            f"""
            <div class="task-card">
              <div class="task-rank">Priority {index}</div>
              <div class="task-dept">{item["department"]}</div>
              <div class="task-title">{item["title"]}</div>
              <div class="task-meta">期待ROI: {item["roi"]}</div>
              <div class="task-approval">承認: {item["approval"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_improvement_board(items) -> None:
    st.markdown("## 今日の改善案件")
    if not items:
        st.info("未取得")
        return

    cols = st.columns(min(3, len(items)))
    for index, item in enumerate(items):
        column = cols[index % len(cols)]
        with column:
            st.markdown(
                f"""
                <div class="improvement-card">
                  <div class="improvement-head">
                    <div class="improvement-stars">{item["priority_stars"]}</div>
                    <span class="state-badge {item["state_tone"]}">{item["state"]}</span>
                  </div>
                  <div class="improvement-title">{item["task"]}</div>
                  <div class="improvement-row"><span>承認状態</span><strong>{item["approval_state"]}</strong></div>
                  <div class="improvement-row"><span>推定時間</span><strong>{item["time"]}</strong></div>
                  <div class="improvement-row"><span>期待ROI</span><strong>{item["roi_stars"]}</strong></div>
                  <div class="improvement-updated">最終更新: {item["updated_at"]}</div>
                  {f'<div class="go-reflected">GO反映済み</div>' if item["go_reflected"] else ""}
                  <div class="improvement-effect">{item["effect"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            comment = st.text_input(
                "コメント",
                value=item["comment"],
                key=f"approval-comment-{item['id']}",
                label_visibility="collapsed",
                placeholder="コメント",
            )
            button_cols = st.columns(3)
            for button_column, decision in zip(button_cols, ("GO", "STOP", "要確認")):
                if button_column.button(
                    decision,
                    key=f"approval-{decision}-{item['id']}",
                    help="承認状態の記録のみ。WordPress更新は行いません。",
                    width="stretch",
                ):
                    result = _save_approval(item["id"], item["task"], decision, comment)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])


def _render_image_candidates(images) -> None:
    st.markdown("## 採用候補画像")
    for character, data in images.items():
        with st.container(border=True):
            st.markdown(f"### {character}")
            st.caption(data["label"])
            if not data["paths"]:
                st.warning("画像未取得")
                continue
            cols = st.columns(min(3, len(data["paths"])))
            for column, image_path in zip(cols, data["paths"][:6]):
                column.image(str(image_path), width="stretch")


def _render_blockers(blockers) -> None:
    st.markdown("## Blocker")
    if not blockers:
        st.markdown('<div class="blocker ok">🟢 なし</div>', unsafe_allow_html=True)
        return

    for blocker in blockers:
        st.markdown(
            f'<div class="blocker danger">🔴 {blocker}</div>',
            unsafe_allow_html=True,
        )


def _render_ceo_comment(comment) -> None:
    st.markdown("## AI社長コメント")
    st.markdown(f'<div class="ceo-comment">{comment}</div>', unsafe_allow_html=True)


def _render_detail_reports(docs, paths) -> None:
    st.markdown("## 詳細レポート")
    focus = st.session_state.get("detail_focus")
    for name in (
        "CEO Report",
        "Run Report",
        "KPI Dashboard",
        "P002 Daily Brief",
        "P003 Daily Brief",
        "Improvement Backlog",
        "Execution Board",
        "P003 Task",
        "Approvals",
    ):
        with st.expander(name, expanded=(focus == name)):
            st.caption(str(paths[name]))
            content = docs.get(name) or "未取得"
            st.markdown(content)


def _render_approval_history(content: str, path: Path) -> None:
    st.markdown("## APPROVALS.md 承認履歴")
    st.caption(str(path))
    if not _parse_approvals(content):
        st.info("承認記録はありません。")
        return
    with st.container(border=True):
        st.markdown(content)


def _build_notifications(docs, kpi, blockers, latest_daily_dir):
    notifications = []
    ga4_values = [kpi.get(key, "未取得") for key in ("users", "sessions", "page_views")]
    if any(value == "未取得" for value in ga4_values) or all(_as_number(value) == 0 for value in ga4_values):
        notifications.append(
            {
                "title": "GA4認証待ち",
                "body": "GA4 KPIが未取得または0です。",
                "icon": "🟡",
                "tone": "warn",
            }
        )
    else:
        notifications.append(
            {
                "title": "GA4取得済み",
                "body": "GA4 KPIを取得しています。",
                "icon": "🟢",
                "tone": "ok",
            }
        )

    if _as_number(kpi.get("clicks")) == 0 and _as_number(kpi.get("impressions")) == 0:
        notifications.append(
            {
                "title": "Search Consoleデータ0件",
                "body": "クリック数・表示回数が0です。",
                "icon": "🟡",
                "tone": "warn",
            }
        )
    else:
        notifications.append(
            {
                "title": "Search Console取得済み",
                "body": "検索KPIを取得しています。",
                "icon": "🟢",
                "tone": "ok",
            }
        )

    run_report = docs.get("Run Report", "")
    runner_ok = "## 失敗\n\n- なし" in run_report
    notifications.append(
        {
            "title": "Runner正常終了" if runner_ok else "Runner要確認",
            "body": "失敗なし" if runner_ok else "RUN_REPORTを確認してください。",
            "icon": "🟢" if runner_ok else "🔴",
            "tone": "ok" if runner_ok else "bad",
        }
    )

    image_status = _image_completion_status(latest_daily_dir)
    notifications.append(image_status)

    notifications.append(
        {
            "title": "Blockerあり" if blockers else "Blockerなし",
            "body": f"{len(blockers)}件" if blockers else "進行阻害なし",
            "icon": "🔴" if blockers else "🟢",
            "tone": "bad" if blockers else "ok",
        }
    )
    return notifications


def _image_completion_status(latest_daily_dir):
    counts = {}
    for character in ("MIKU", "RIO"):
        if latest_daily_dir:
            counts[character] = len(_image_files(latest_daily_dir / character))
        else:
            counts[character] = 0
    if all(count > 0 for count in counts.values()):
        return {
            "title": "画像生成完了",
            "body": f"MIKU {counts['MIKU']}枚 / RIO {counts['RIO']}枚",
            "icon": "🟢",
            "tone": "ok",
        }
    return {
        "title": "画像生成未完了",
        "body": f"MIKU {counts['MIKU']}枚 / RIO {counts['RIO']}枚",
        "icon": "🟡",
        "tone": "warn",
    }


def _build_system_state(docs, paths):
    items = []
    for name, path in paths.items():
        absolute = _absolute(path)
        content = docs.get(name)
        status, icon = _document_status(name, content)
        items.append(
            {
                "label": name,
                "status": status,
                "icon": icon,
                "detail": str(path) if absolute.exists() else "ファイルなし",
            }
        )
    return items


def _extract_kpi_cards(content):
    rows = _parse_source_kpi_table(content)
    wordpress = rows.get("wordpress", {})
    search_console = rows.get("search_console", {})
    ga4 = rows.get("ga4", {})
    values = {}
    values.update(_pick(wordpress, ("posts", "published", "categories", "tags")))
    values.update(_pick(search_console, ("clicks", "impressions", "ctr", "position")))
    values.update(_pick(ga4, ("users", "sessions", "page_views", "engagement_time")))
    return values


def _pick(values, keys):
    return {key: values.get(key, "未取得") for key in keys}


def _extract_top3(content):
    items = []
    for heading in ("Priority 1", "Priority 2", "Priority 3"):
        section = _extract_section(content, heading)
        if not section:
            continue
        reason = _extract_label_value(section, "理由")
        items.append(
            {
                "department": _extract_label_value(section, "担当"),
                "title": reason,
                "reason": reason,
                "roi": _extract_label_value(section, "期待ROI"),
                "approval": _extract_label_value(section, "承認（GO / STOP）"),
            }
        )
    return items


def _parse_today_posts(content: str):
    posts = []
    character = ""
    slot = ""
    block = []

    def append_block():
        if not character or not slot:
            return
        post_texts = {
            platform: _extract_fenced_post_text(block, platform)
            for platform in ("Instagram", "X", "Threads")
        }
        posts.append(
            {
                "character": character,
                "slot": slot,
                "theme": _extract_list_value(block, "今日のテーマ") or "未取得",
                "image_folder": _extract_list_value(block, "採用画像フォルダ") or "未取得",
                "images": _extract_image_list(block),
                "post_texts": {
                    platform: text
                    for platform, text in post_texts.items()
                    if text and text != "未取得"
                },
            }
        )

    for line in content.splitlines():
        if line.startswith("## ") and line[3:].strip() in {"MIKU", "RIO"}:
            append_block()
            character = line[3:].strip()
            slot = ""
            block = []
            continue
        if line.startswith("### ") and character:
            append_block()
            slot = line[4:].strip()
            block = []
            continue
        if slot:
            block.append(line)
    append_block()
    return [post for post in posts if post["slot"] != "未取得"]


def _extract_list_value(lines, label: str) -> str:
    prefix = f"- {label}:"
    for line in lines:
        if line.strip().startswith(prefix):
            return line.strip()[len(prefix) :].strip().strip("`")
    return ""


def _extract_image_list(lines):
    images = []
    in_images = False
    for line in lines:
        clean = line.strip()
        if clean == "- 採用画像一覧:":
            in_images = True
            continue
        if not in_images:
            continue
        if line.startswith("  - "):
            value = line[4:].strip().strip("`")
            if value and value != "未取得":
                images.append(value)
            continue
        if clean:
            break
    return images


def _extract_fenced_post_text(lines, platform: str) -> str:
    heading = f"- {platform}投稿文"
    capture = False
    in_fence = False
    captured = []
    for line in lines:
        clean = line.strip()
        if clean == heading:
            capture = True
            continue
        if not capture:
            continue
        if clean.startswith("```"):
            if not in_fence:
                in_fence = True
                continue
            break
        if in_fence:
            captured.append(line)
        elif clean.startswith("- "):
            break
    return "\n".join(captured).strip()


def _today_post_date(content: str) -> str:
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "日付":
            continue
        for value in lines[index + 1 :]:
            clean = value.strip()
            if clean:
                try:
                    return date.fromisoformat(clean).isoformat()
                except ValueError:
                    break
    return date.today().isoformat()


def _safe_workspace_path(value: str):
    try:
        candidate = (WORKSPACE_ROOT / value).resolve()
        candidate.relative_to(WORKSPACE_ROOT)
        return candidate
    except (OSError, ValueError):
        return None


def _parse_post_results(content: str):
    results = {}
    rows = _parse_any_markdown_table(content)
    for row in rows:
        key = (
            row.get("キャラクター", ""),
            row.get("時間帯", ""),
            row.get("投稿先", ""),
        )
        if all(key):
            results[key] = row
    return results


def _save_post_result(
    result_path: Path,
    output_date: str,
    character: str,
    slot: str,
    platform: str,
    post_url: str,
    images,
    memo: str,
):
    try:
        absolute = _absolute(result_path)
        absolute.parent.mkdir(parents=True, exist_ok=True)
        results = _parse_post_results(_read_text(result_path))
        results[(character, slot, platform)] = {
            "投稿日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "キャラクター": character,
            "時間帯": slot,
            "投稿先": platform,
            "投稿URL": _clean_table_cell(post_url) or "未取得",
            "使用画像": ", ".join(Path(image).name for image in images) or "未取得",
            "メモ": _clean_table_cell(memo),
        }
        absolute.write_text(
            _format_post_results(output_date, results),
            encoding="utf-8",
        )
        return {"success": True, "message": f"{platform}の投稿結果を記録しました。"}
    except (OSError, ValueError) as exc:
        return {"success": False, "message": f"投稿結果を保存できませんでした: {exc}"}


def _format_post_results(output_date: str, results) -> str:
    lines = [
        "# POST RESULT",
        "",
        "日付",
        "",
        output_date,
        "",
        "| 投稿日時 | キャラクター | 時間帯 | 投稿先 | 投稿URL | 使用画像 | メモ |",
        "|---|---|---|---|---|---|---|",
    ]
    for key in sorted(results):
        row = results[key]
        lines.append(
            "| {投稿日時} | {キャラクター} | {時間帯} | {投稿先} | {投稿URL} | {使用画像} | {メモ} |".format(
                **{
                    field: _clean_table_cell(row.get(field, ""))
                    for field in (
                        "投稿日時",
                        "キャラクター",
                        "時間帯",
                        "投稿先",
                        "投稿URL",
                        "使用画像",
                        "メモ",
                    )
                }
            )
        )
    lines.extend(
        [
            "",
            "## 制約確認",
            "",
            "- 自動投稿: 未実行",
            "- SNSログイン操作: 未実行",
            "- ファイル削除: 未実行",
            "",
        ]
    )
    return "\n".join(lines)


def _parse_any_markdown_table(content: str):
    rows = []
    headers = []
    for line in content.splitlines():
        clean = line.strip()
        if not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if not headers:
            headers = cells
            continue
        if len(cells) == len(headers):
            rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def _extract_improvements(
    backlog_content,
    board_content,
    task_content,
    approvals_content,
    source_paths=None,
):
    rows = _parse_markdown_table(backlog_content, "改善バックログ")
    if not rows:
        return []

    board_states = _board_states(board_content)
    approval_ids = _ids_in_section(board_content, "承認待ち")
    approvals = _parse_approvals(approvals_content)
    source_updated_at = _latest_source_update(source_paths or {})
    task_text = task_content or ""
    cards = []
    for row in rows:
        item_id = row.get("ID", "").strip()
        if item_id not in {"101", "102", "103"}:
            continue
        state = row.get("状態", "未取得").strip() or "未取得"
        if item_id in board_states:
            state = board_states[item_id]
        elif item_id in approval_ids and state == "提案":
            state = "承認待ち"
        approval = approvals.get(item_id, {})
        approval_decision = approval.get("承認状態", "").strip()
        if approval_decision == "GO" and state not in {"実装中", "完了"}:
            state = "実装待ち"
        display_state = _display_improvement_state(state)
        approval_state = "GO済み" if approval_decision == "GO" else (approval_decision or "未承認")
        cards.append(
            {
                "id": item_id,
                "task": row.get("タスク", "未取得").strip() or "未取得",
                "state": display_state,
                "state_tone": _improvement_state_tone(display_state),
                "approval_state": approval_state,
                "comment": approval.get("コメント", ""),
                "updated_at": approval.get("承認日時", "").strip() or source_updated_at,
                "go_reflected": approval_decision == "GO",
                "effect": row.get("効果", "未取得").strip() or "未取得",
                "priority_stars": _improvement_priority_stars(item_id, row.get("優先度")),
                "roi_stars": _improvement_roi_stars(item_id, row.get("効果")),
                "time": _improvement_time(item_id, task_text),
                "sort": _improvement_sort_key(item_id, state),
            }
        )
    return sorted(cards, key=lambda item: item["sort"])


def _parse_approvals(content: str):
    approvals = {}
    headers = []
    for line in content.splitlines():
        clean = line.strip()
        if not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or cells[0].startswith("---"):
            continue
        if cells[0] == "ID":
            headers = cells
            continue
        if headers and len(cells) == len(headers):
            row = {headers[index]: cells[index] for index in range(len(headers))}
            approvals[row.get("ID", "")] = row
    return approvals


def _save_approval(item_id: str, task: str, decision: str, comment: str):
    try:
        approval_path = _absolute(APPROVALS_PATH)
        approval_path.parent.mkdir(parents=True, exist_ok=True)
        approvals = _parse_approvals(_read_text(APPROVALS_PATH))
        approvals[item_id] = {
            "ID": item_id,
            "タスク": task,
            "承認状態": decision,
            "承認日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "コメント": _clean_table_cell(comment),
        }
        approval_path.write_text(_format_approvals(approvals), encoding="utf-8")
        return {
            "success": True,
            "message": f"{task} を {decision} として記録しました。",
        }
    except OSError as exc:
        return {
            "success": False,
            "message": f"承認状態を保存できませんでした: {exc}",
        }


def _format_approvals(approvals) -> str:
    lines = [
        "| ID | タスク | 承認状態 | 承認日時 | コメント |",
        "|---|---|---|---|---|",
    ]
    for item_id in sorted(approvals, key=lambda value: int(value) if value.isdigit() else 999):
        row = approvals[item_id]
        lines.append(
            "| {ID} | {タスク} | {承認状態} | {承認日時} | {コメント} |".format(
                ID=_clean_table_cell(row.get("ID", "")),
                タスク=_clean_table_cell(row.get("タスク", "")),
                承認状態=_clean_table_cell(row.get("承認状態", "")),
                承認日時=_clean_table_cell(row.get("承認日時", "")),
                コメント=_clean_table_cell(row.get("コメント", "")),
            )
        )
    return "\n".join(lines) + "\n"


def _clean_table_cell(value: str) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _parse_markdown_table(content: str, section_heading: str):
    rows = []
    lines = content.splitlines()
    in_section = False
    headers = []
    target = _normalize_heading(f"## {section_heading}")
    for line in lines:
        clean = line.strip()
        if _normalize_heading(clean) == target:
            in_section = True
            continue
        if in_section and clean.startswith("## "):
            break
        if not in_section or not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or cells[0].startswith("---"):
            continue
        if cells[0] == "ID":
            headers = cells
            continue
        if headers and len(cells) == len(headers):
            rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def _ids_in_section(content: str, heading: str):
    section = _extract_section(content, heading)
    ids = set()
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0].isdigit():
            ids.add(cells[0])
    return ids


def _board_states(content: str):
    states = {}
    section_states = {
        "今日実行": "実装待ち",
        "承認待ち": "承認待ち",
        "効果測定中": "実装中",
        "完了": "完了",
    }
    for heading, fallback_state in section_states.items():
        section = _extract_section(content, heading)
        for line in section.splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or not cells[0].isdigit():
                continue
            state = cells[3] if len(cells) > 3 else fallback_state
            states[cells[0]] = state if state not in {"-", ""} else fallback_state
    return states


def _display_improvement_state(state: str) -> str:
    if state == "提案":
        return "提案中"
    if state in {"実装済み", "効果測定中"}:
        return "実装中"
    if state == "GO":
        return "GO済み"
    return state or "未取得"


def _improvement_state_tone(state: str) -> str:
    if state == "完了":
        return "complete"
    if state in {"実装待ち", "実装中", "GO済み"}:
        return "active"
    if state == "承認待ち":
        return "waiting"
    return "proposal"


def _latest_source_update(source_paths) -> str:
    timestamps = []
    for path in source_paths.values():
        absolute = _absolute(path)
        if absolute.exists():
            timestamps.append(absolute.stat().st_mtime)
    if not timestamps:
        return "未取得"
    return datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d %H:%M")


def _improvement_priority_stars(item_id: str, priority: str) -> str:
    explicit = {"101": "★★★★★", "102": "★★★★☆", "103": "★★★★☆"}
    if item_id in explicit:
        return explicit[item_id]
    if priority == "高":
        return "★★★★★"
    if priority == "中":
        return "★★★★☆"
    return "★★★☆☆"


def _improvement_roi_stars(item_id: str, effect: str) -> str:
    explicit = {"101": "★★★★★", "102": "★★★★☆", "103": "★★★★☆"}
    if item_id in explicit:
        return explicit[item_id]
    if "CTR" in (effect or "") or "SEO" in (effect or ""):
        return "★★★★☆"
    return "★★★☆☆"


def _improvement_time(item_id: str, task_text: str) -> str:
    times = {"101": "5分", "102": "15分", "103": "10分"}
    return times.get(item_id, "未取得" if not task_text else "10分")


def _improvement_sort_key(item_id: str, state: str):
    state_rank = {
        "実装待ち": 0,
        "承認待ち": 1,
        "提案": 2,
        "実装済み": 3,
        "効果測定中": 4,
        "完了": 5,
    }
    return (state_rank.get(state, 9), int(item_id) if item_id.isdigit() else 999)


def _extract_blockers(content):
    section = _extract_section(content, "Blocker")
    if not section:
        return []
    blockers = []
    ignored = {"止まっていること", "- なし。", "なし。"}
    for line in section.splitlines():
        clean = line.strip()
        if not clean or clean in ignored:
            continue
        if "止まっていること" in clean:
            continue
        if clean.startswith("- ") and "なし" not in clean:
            blockers.append(clean[2:])
        elif clean.startswith("・"):
            blockers.append(clean)
    return blockers


def _find_character_images(character: str, latest_daily_dir):
    if latest_daily_dir:
        today_dir = latest_daily_dir / character
        today_images = _image_files(today_dir)
        if today_images:
            return {"label": f"{today_dir.relative_to(WORKSPACE_ROOT)}", "paths": today_images}

    output_root = WORKSPACE_ROOT / "02_Daily_Output"
    if not output_root.exists():
        return {"label": "未取得", "paths": []}

    for daily_dir in sorted((path for path in output_root.iterdir() if path.is_dir()), reverse=True):
        character_dir = daily_dir / character
        images = _image_files(character_dir)
        if images:
            return {
                "label": f"直近候補: {character_dir.relative_to(WORKSPACE_ROOT)}",
                "paths": images,
            }
    return {"label": "未取得", "paths": []}


def _image_files(directory: Path):
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def _parse_source_kpi_table(content):
    sources = {}
    headers = []
    in_section = False
    for line in content.splitlines():
        clean = line.strip()
        if clean == "## Source KPI":
            in_section = True
            continue
        if in_section and clean.startswith("## "):
            break
        if not in_section or not clean.startswith("|"):
            continue

        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or cells[0].startswith("---"):
            continue
        if cells[0] == "source":
            headers = cells
            continue
        if not headers or len(cells) != len(headers):
            continue
        sources[cells[0]] = {
            headers[index]: cells[index] for index in range(1, len(headers))
        }
    return sources


def _extract_section(content: str, heading: str) -> str:
    lines = content.splitlines()
    capture = False
    captured = []
    target = _normalize_heading(f"## {heading}")
    for line in lines:
        if _normalize_heading(line) == target:
            capture = True
            continue
        if capture and (line.startswith("## ") or line.strip() == "---"):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def _extract_label_value(text: str, label: str) -> str:
    lines = text.splitlines()
    labels = {"担当", "理由", "期待ROI", "作業時間", "承認（GO / STOP）"}
    for index, line in enumerate(lines):
        if line.strip() != label:
            continue
        for value_line in lines[index + 1 :]:
            clean = value_line.strip()
            if not clean:
                continue
            if clean in labels:
                return "未取得"
            return clean
    return "未取得"


def _read_text(path: Path) -> str:
    absolute = _absolute(path)
    if not absolute.exists():
        return ""
    try:
        return absolute.read_text(encoding="utf-8")
    except OSError:
        return ""


def _latest_daily_output_dir():
    output_root = WORKSPACE_ROOT / "02_Daily_Output"
    if not output_root.exists():
        return None
    daily_dirs = [path for path in output_root.iterdir() if path.is_dir()]
    return sorted(daily_dirs, key=lambda path: path.name)[-1] if daily_dirs else None


def _latest_artifact(filename: str, latest_daily_dir):
    if latest_daily_dir:
        candidate = latest_daily_dir / filename
        if candidate.exists():
            return candidate.relative_to(WORKSPACE_ROOT)

    if filename == "RUN_REPORT.md":
        fallback = WORKSPACE_ROOT / "06_AI_COMPANY_Runner" / "RUN_REPORT.md"
        if fallback.exists():
            return fallback.relative_to(WORKSPACE_ROOT)

    return Path("02_Daily_Output") / date.today().isoformat() / filename


def _status_tone(status: str) -> str:
    if status == "正常":
        return "ok"
    if status == "注意":
        return "warn"
    return "bad"


def _document_status(name: str, content: str):
    if not content:
        return "未取得", "🔴"
    if name == "Run Report" and "## 失敗\n\n- なし" not in content:
        return "注意", "🟡"
    if name in ("KPI Dashboard", "CEO Report") and "未取得" in content:
        return "注意", "🟡"
    return "正常", "🟢"


def _run_local_command(command):
    try:
        completed = subprocess.run(
            command,
            cwd=str(WORKSPACE_ROOT),
            text=True,
            capture_output=True,
            timeout=300,
        )
    except Exception as exc:
        return {
            "success": False,
            "message": f"実行失敗: {exc}",
            "output": "",
        }

    output = "\n".join(
        part
        for part in (
            f"$ {' '.join(command)}",
            completed.stdout.strip(),
            completed.stderr.strip(),
        )
        if part
    )
    return {
        "success": completed.returncode == 0,
        "message": "実行完了" if completed.returncode == 0 else "実行エラー",
        "output": output,
    }


def _require_dashboard_auth() -> None:
    load_config()
    password = os.getenv("DASHBOARD_PASSWORD", "").strip()
    if not password or st.session_state.get("dashboard_authenticated"):
        return

    st.markdown("# AI COMPANY")
    st.caption("外部公開用ログイン")
    with st.form("dashboard_login"):
        entered = st.text_input("Password", type="password")
        submitted = st.form_submit_button("ログイン", width="stretch")

    if submitted:
        if entered == password:
            st.session_state["dashboard_authenticated"] = True
            st.rerun()
        st.error("パスワードが違います。")
    st.stop()


def _wordpress_url():
    load_config()
    return os.getenv("P003_WORDPRESS_URL", "").strip()


def _wordpress_admin_url(site_url):
    explicit = (
        os.getenv("P003_WORDPRESS_ADMIN_URL", "").strip()
        or os.getenv("WORDPRESS_ADMIN_URL", "").strip()
    )
    if explicit:
        return explicit
    if not site_url:
        return ""
    return site_url.rstrip("/") + "/wp-admin/"


def _as_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _format_metric(value) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:,.2f}"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(WORKSPACE_ROOT))
    except (OSError, ValueError):
        return str(path)


def _normalize_heading(line: str) -> str:
    return line.strip().replace(" ", "").replace("　", "")


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else WORKSPACE_ROOT / path


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; }
        div[data-testid="stVerticalBlock"] { gap: 0.7rem; }
        .status-card, .kpi-card, .task-card, .improvement-card, .blocker, .ceo-comment {
          border-radius: 10px;
          padding: 14px;
          border: 1px solid rgba(49, 51, 63, 0.15);
          box-shadow: 0 1px 8px rgba(0,0,0,0.06);
          background: #ffffff;
        }
        .status-card.ok { border-left: 6px solid #16a34a; }
        .status-card.warn { border-left: 6px solid #f59e0b; background: #fffbeb; }
        .status-card.bad { border-left: 6px solid #dc2626; }
        .status-icon { font-size: 1.2rem; }
        .status-label { font-size: 0.78rem; color: #475569; margin-top: 4px; }
        .status-value { font-weight: 800; font-size: 1.1rem; color: #0f172a; }
        .status-detail { font-size: 0.68rem; color: #64748b; overflow-wrap: anywhere; }
        .kpi-card.green { background: #ecfdf5; border-color: #86efac; }
        .kpi-card.yellow { background: #fffbeb; border-color: #fde68a; }
        .kpi-card.red { background: #fef2f2; border-color: #fecaca; }
        .kpi-source { font-size: 0.72rem; font-weight: 800; color: #475569; margin-bottom: 8px; }
        .kpi-row { display: flex; justify-content: space-between; gap: 8px; margin: 6px 0; }
        .kpi-row span { color: #475569; font-size: 0.76rem; }
        .kpi-row strong { color: #0f172a; font-size: 1.1rem; }
        .task-card { margin-bottom: 10px; border-left: 6px solid #2563eb; }
        .task-rank { font-size: 0.72rem; color: #2563eb; font-weight: 800; }
        .task-dept { font-size: 0.82rem; color: #475569; font-weight: 700; }
        .task-title { font-weight: 800; color: #0f172a; margin: 8px 0; }
        .task-meta, .task-approval { font-size: 0.76rem; color: #475569; }
        .improvement-card {
          min-height: 210px;
          margin-bottom: 8px;
          border-left: 6px solid #0f766e;
          background: #f8fafc;
        }
        .improvement-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .improvement-stars {
          color: #b45309;
          font-size: 1.05rem;
          font-weight: 900;
          letter-spacing: 0;
        }
        .state-badge {
          display: inline-flex;
          align-items: center;
          min-height: 26px;
          padding: 3px 9px;
          border-radius: 999px;
          font-size: 0.72rem;
          font-weight: 800;
          white-space: nowrap;
        }
        .state-badge.proposal { color: #475569; background: #e2e8f0; }
        .state-badge.waiting { color: #92400e; background: #fef3c7; }
        .state-badge.active { color: #1d4ed8; background: #dbeafe; }
        .state-badge.complete { color: #166534; background: #dcfce7; }
        .improvement-title {
          font-size: 1.08rem;
          font-weight: 900;
          color: #0f172a;
          margin: 8px 0 10px;
        }
        .improvement-row {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          padding: 4px 0;
          border-top: 1px solid rgba(15, 23, 42, 0.07);
        }
        .improvement-row span { color: #475569; font-size: 0.78rem; }
        .improvement-row strong { color: #0f172a; font-size: 0.86rem; text-align: right; }
        .improvement-updated {
          margin-top: 10px;
          color: #64748b;
          font-size: 0.7rem;
        }
        .go-reflected {
          margin-top: 8px;
          padding: 7px 9px;
          color: #166534;
          background: #dcfce7;
          border: 1px solid #86efac;
          border-radius: 6px;
          font-size: 0.78rem;
          font-weight: 800;
          text-align: center;
        }
        .sns-theme {
          margin: 6px 0 14px;
          padding: 14px;
          border-left: 6px solid #0f766e;
          background: #f0fdfa;
          border-radius: 8px;
        }
        .sns-theme-label {
          color: #0f766e;
          font-size: 0.74rem;
          font-weight: 800;
        }
        .sns-theme-title {
          margin-top: 4px;
          color: #0f172a;
          font-size: 1.05rem;
          font-weight: 900;
        }
        .sns-theme-path {
          margin-top: 5px;
          color: #64748b;
          font-size: 0.7rem;
          overflow-wrap: anywhere;
        }
        .improvement-effect {
          margin-top: 10px;
          color: #334155;
          font-size: 0.78rem;
          line-height: 1.45;
        }
        .blocker { margin-bottom: 8px; font-weight: 800; }
        .blocker.danger { background: #fef2f2; border-left: 6px solid #dc2626; color: #7f1d1d; }
        .blocker.ok { background: #ecfdf5; border-left: 6px solid #16a34a; color: #14532d; }
        .ceo-comment { background: #eff6ff; border-left: 6px solid #2563eb; white-space: pre-wrap; }
        .notice {
          border-radius: 10px;
          padding: 12px;
          border: 1px solid rgba(49, 51, 63, 0.15);
          min-height: 94px;
          box-shadow: 0 1px 8px rgba(0,0,0,0.05);
        }
        .notice.ok { background: #ecfdf5; border-left: 6px solid #16a34a; }
        .notice.warn { background: #fffbeb; border-left: 6px solid #f59e0b; }
        .notice.bad { background: #fef2f2; border-left: 6px solid #dc2626; }
        .notice-title { font-weight: 900; color: #0f172a; margin-bottom: 6px; }
        .notice-body { font-size: 0.78rem; color: #475569; }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

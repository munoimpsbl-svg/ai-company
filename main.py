import csv
from datetime import date, datetime
import html
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import uuid

import streamlit as st
import streamlit.components.v1 as components

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
    "P004 Daily Brief": Path("04_アダルト事業部") / "DAILY_BRIEF.md",
}

P003_PROJECT_DIR = Path("01_グラビア事業部") / "P003_グラビア事業部"
P003_COMMAND_DIR = Path("04_グラビア事業部")
TODAY_POST_PATH = Path("03_SNS事業部") / "04_Daily" / "TODAY_POST.md"
AI_VQC_PATH = Path("03_SNS事業部") / "AI_VQC.md"
GENERATION_QUALITY_REPORT_PATH = (
    Path("03_SNS事業部") / "03_Analytics" / "GENERATION_QUALITY_REPORT.md"
)
WARDROBE_ROTATION_REPORT_PATH = (
    Path("03_SNS事業部") / "03_Analytics" / "WARDROBE_ROTATION_REPORT.md"
)
MIKU_FIXED_RULES_PATH = (
    Path("03_SNS事業部") / "01_Characters" / "MIKU" / "MIKU_FIXED_RULES.md"
)
RIO_BASE_REFERENCE_PATH = (
    Path("03_SNS事業部") / "01_Characters" / "RIO" / "RIO_BASE_REFERENCE.md"
)
SELFIE_PHONE_RULES_PATH = Path("03_SNS事業部") / "SELFIE_PHONE_RULES.md"
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
X_RESULT_DIR = Path("03_SNS事業部") / "03_Analytics" / "X_RESULTS"
X_RESULT_LOG_PATH = X_RESULT_DIR / "X_RESULT_LOG.md"
X_RESULT_CSV_PATH = X_RESULT_DIR / "x_results.csv"
RUNNER_JOB_DIR = Path(".dashboard_jobs")
RUNNER_JOB_PATH = RUNNER_JOB_DIR / "runner_job.json"
RUNNER_PROGRESS_PATH = RUNNER_JOB_DIR / "runner_progress.json"
RUNNER_STDOUT_PATH = RUNNER_JOB_DIR / "runner_stdout.log"
RUNNER_STDERR_PATH = RUNNER_JOB_DIR / "runner_stderr.log"
BRIEF_JOB_PATH = RUNNER_JOB_DIR / "daily_brief_job.json"
BRIEF_PROGRESS_PATH = RUNNER_JOB_DIR / "daily_brief_progress.json"
BRIEF_STDOUT_PATH = RUNNER_JOB_DIR / "daily_brief_stdout.log"
BRIEF_STDERR_PATH = RUNNER_JOB_DIR / "daily_brief_stderr.log"


def main() -> None:
    st.set_page_config(page_title="Editor Dashboard", page_icon=None, layout="wide")
    _inject_styles()
    _require_dashboard_auth()

    page = st.radio(
        "画面",
        (
            "Command Center",
            "Company Hub",
            "成果物",
            "SNS Today",
            "SNS Input Manager",
            "SNS Analytics",
            "GPT Image Quality",
        ),
        horizontal=True,
        label_visibility="collapsed",
    )
    if page == "Company Hub":
        _render_company_hub_page()
        return
    if page == "成果物":
        _render_artifacts_page()
        return
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
        "AI-VQC": AI_VQC_PATH,
        "Generation Quality": GENERATION_QUALITY_REPORT_PATH,
        "Wardrobe Rotation": WARDROBE_ROTATION_REPORT_PATH,
        "MIKU Fixed Rules": MIKU_FIXED_RULES_PATH,
        "RIO Base Reference": RIO_BASE_REFERENCE_PATH,
        "Selfie Phone Rules": SELFIE_PHONE_RULES_PATH,
    }
    docs = {name: _read_text(path) for name, path in paths.items()}
    dashboard = _build_dashboard_data(docs, paths, latest_daily_dir)

    _render_console_header(
        "AI COMPANY",
        "Command Center",
        "毎朝の判断、改善案件、KPI、SNS素材をここで確認します。",
        dashboard,
    )
    _render_momentum_strip(dashboard)
    _render_ai_employee_run(dashboard["runner_job"])
    _render_daily_brief_factory(dashboard["daily_brief"])
    _render_visual_highlights(dashboard["images"])
    _render_x_input_guide()

    with st.sidebar:
        _render_live_sync_toggle()
        _render_notification_center(dashboard)
        _render_action_center(paths)

    _render_system_cards(dashboard)
    _render_kpi_cards(dashboard["kpi"])

    _render_top3(dashboard["top3"])
    _render_ai_beauty_guard(dashboard["ai_beauty"])
    _render_wardrobe_rotation(dashboard["wardrobe"])
    _render_improvement_board(dashboard["improvements"])

    left, right = st.columns([1, 1], gap="large")
    with left:
        _render_blockers(dashboard["blockers"])
    with right:
        _render_ceo_comment(dashboard["ceo_comment"])

    _render_image_candidates(dashboard["images"])

    _render_detail_reports(docs, paths)
    _render_approval_history(docs["Approvals"], paths["Approvals"])


def _render_company_hub_page() -> None:
    latest_daily_dir = _latest_daily_output_dir()
    ceo_path = _latest_artifact("CEO_REPORT.md", latest_daily_dir)
    run_path = _latest_artifact("RUN_REPORT.md", latest_daily_dir)
    paths = {
        **INPUTS,
        **IMPROVEMENT_INPUTS,
        "CEO Report": ceo_path,
        "Run Report": run_path,
        "P004 Daily Brief": Path("04_アダルト事業部") / "DAILY_BRIEF.md",
        "SNS Report": Path("03_SNS事業部") / "SNS_REPORT.md",
        "P003 Report": P003_PROJECT_DIR / "REPORT.md",
        "P004 Report": Path("04_アダルト事業部") / "REPORT.md",
        "AI-VQC": AI_VQC_PATH,
        "Generation Quality": GENERATION_QUALITY_REPORT_PATH,
        "Wardrobe Rotation": WARDROBE_ROTATION_REPORT_PATH,
        "MIKU Fixed Rules": MIKU_FIXED_RULES_PATH,
        "RIO Base Reference": RIO_BASE_REFERENCE_PATH,
        "Selfie Phone Rules": SELFIE_PHONE_RULES_PATH,
    }
    docs = {name: _read_text(path) for name, path in paths.items()}
    dashboard = _build_dashboard_data(docs, paths, latest_daily_dir)
    x_rows = _load_x_result_rows()

    _render_console_header(
        "AI COMPANY HUB",
        "Company Hub",
        "X結果の蓄積、部署状況、経営レポートをまとめて見る画面です。",
        dashboard,
    )

    _render_mobile_command_strip(dashboard)
    _render_momentum_strip(dashboard)
    _render_ai_employee_run(dashboard["runner_job"])
    _render_daily_brief_factory(dashboard["daily_brief"])
    _render_company_overview(dashboard, docs, x_rows)
    _render_ai_beauty_guard(dashboard["ai_beauty"])
    _render_wardrobe_rotation(dashboard["wardrobe"])
    _render_company_flow(dashboard)

    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        _render_x_result_paste()
    with right:
        _render_x_result_history(x_rows)

    _render_company_knowledge_base(docs, paths)


def _render_artifacts_page() -> None:
    latest_daily_dir = _latest_daily_output_dir()
    artifacts = _artifact_items(latest_daily_dir)
    st.markdown("# 成果物")
    st.caption("生成されたレポート、Daily Brief、改善計画を確認するページです。投稿、更新、削除は行いません。")

    summary = {
        "最新日": latest_daily_dir.name if latest_daily_dir else "未取得",
        "成果物": len(artifacts),
        "取得済み": sum(1 for item in artifacts if item["exists"]),
        "未取得": sum(1 for item in artifacts if not item["exists"]),
    }
    cols = st.columns(4)
    for column, (label, value) in zip(cols, summary.items()):
        column.markdown(
            f"""
            <div class="artifact-summary-card">
              <div class="artifact-summary-label">{label}</div>
              <div class="artifact-summary-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    category_names = ["すべて"] + sorted({item["category"] for item in artifacts})
    tabs = st.tabs(category_names)
    for tab, category in zip(tabs, category_names):
        with tab:
            filtered = artifacts if category == "すべて" else [item for item in artifacts if item["category"] == category]
            _render_artifact_grid(filtered)


def _render_console_header(title: str, label: str, subtitle: str, dashboard) -> None:
    kpi = dashboard.get("kpi", {})
    blocker_count = len(dashboard.get("blockers", []))
    latest_dir = dashboard.get("latest_daily_dir")
    latest_label = latest_dir.name if latest_dir else "未取得"
    st.markdown(
        f"""
        <div class="console-hero">
          <div class="hero-glow one"></div>
          <div class="hero-glow two"></div>
          <div class="hero-content">
            <div class="hero-label">{label}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
            <div class="hero-pills">
              <span><b>KPI</b> {kpi.get("posts", "未取得")} posts</span>
              <span><b>PV</b> {kpi.get("page_views", "未取得")}</span>
              <span><b>Blocker</b> {blocker_count}</span>
              <span><b>Output</b> {latest_label}</span>
            </div>
          </div>
          <div class="hero-status">
            <div class="radar">
              <span></span><span></span><span></span>
              <strong>AI</strong>
            </div>
            <div class="hero-status-text">Operating</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_console_nav_cards()


def _render_console_nav_cards() -> None:
    cards = [
        ("KPI", "流入とPV", "graph"),
        ("SNS", "投稿素材", "social"),
        ("X", "結果蓄積", "x"),
        ("SEO", "改善案件", "seo"),
        ("CEO", "経営判断", "ceo"),
        ("Drive", "同期成果物", "drive"),
    ]
    cols = st.columns(6)
    for column, (title, body, tone) in zip(cols, cards):
        column.markdown(
            f"""
            <div class="nav-tile {tone}">
              <div class="nav-icon">{title[:1]}</div>
              <div class="nav-title">{title}</div>
              <div class="nav-body">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_visual_highlights(images) -> None:
    preview_paths = []
    for character in ("MIKU", "RIO"):
        preview_paths.extend(images.get(character, {}).get("paths", [])[:2])
    if not preview_paths:
        return

    st.markdown("## Creative Deck")
    cols = st.columns(min(4, len(preview_paths)))
    for index, (column, image_path) in enumerate(zip(cols, preview_paths[:4]), start=1):
        with column:
            st.markdown(
                f"""
                <div class="visual-card-head">
                  <span>SHOT {index:02d}</span>
                  <strong>{image_path.parent.parent.name.upper()}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(str(image_path), width="stretch")
            st.markdown(
                f'<div class="visual-file-name">{_html_escape(image_path.name)}</div>',
                unsafe_allow_html=True,
            )


def _render_x_input_guide() -> None:
    drive_url = ""
    drive_error = ""
    try:
        listing = list_drive_csv_files(WORKSPACE_ROOT)
        folder_id = listing.get("folder", {}).get("id", "")
        if folder_id:
            drive_url = f"https://drive.google.com/drive/folders/{folder_id}"
    except Exception as exc:
        drive_error = str(exc)

    st.markdown(
        """
        <div class="x-input-guide">
          <div>
            <div class="x-input-guide-label">X数値入力</div>
            <div class="x-input-guide-title">上部タブの Company Hub → X結果を貼って蓄積</div>
            <div class="x-input-guide-body">投稿URL、インプレッション、いいね、リポスト、返信、プロフィールクリック、リンククリックを保存できます。</div>
          </div>
          <div class="x-input-guide-pill">手入力 / CSV対応</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    link_cols = st.columns([1, 1, 2])
    if drive_url:
        link_cols[0].link_button("Drive CSVフォルダを開く", drive_url, width="stretch")
        link_cols[1].button("CSV削除は無効", disabled=True, width="stretch")
        link_cols[2].caption(f"Drive保存先: {DRIVE_INPUT_LABEL}")
    else:
        link_cols[0].button("Drive CSVフォルダ未取得", disabled=True, width="stretch")
        link_cols[1].button("CSV削除は無効", disabled=True, width="stretch")
        link_cols[2].caption(f"Drive取得エラー: {drive_error or '未取得'}")


def _render_momentum_strip(dashboard) -> None:
    kpi = dashboard["kpi"]
    ai_guard = dashboard["ai_beauty"]
    images = dashboard["images"]
    image_count = sum(len(data.get("paths", [])) for data in images.values())
    improvements = dashboard["improvements"]
    go_count = sum(1 for item in improvements if item.get("go_reflected") or item.get("approval_state") == "GO")
    blocker_count = len(dashboard["blockers"])
    top_task = dashboard["top3"][0]["title"] if dashboard["top3"] else "未取得"
    search_live = _as_number(kpi.get("clicks")) > 0 or _as_number(kpi.get("impressions")) > 0
    ga_live = _as_number(kpi.get("page_views")) > 0 or _as_number(kpi.get("users")) > 0
    quality_tone = {"正常": "ok", "注意": "warn", "要確認": "bad"}.get(ai_guard["status"], "warn")
    cards = [
        {
            "title": "SEO Engine",
            "value": f"{kpi.get('published', '未取得')}公開",
            "detail": f"改善GO {go_count}件 / 今日: {_shorten_text(top_task, 24)}",
            "icon": "SEO",
            "tone": "green",
            "progress": _bounded_percent(_as_number(kpi.get("published")) * 8),
        },
        {
            "title": "SNS Studio",
            "value": f"{image_count}素材",
            "detail": "MIKU / RIO 投稿候補を表示中",
            "icon": "SNS",
            "tone": "pink",
            "progress": _bounded_percent(image_count * 5),
        },
        {
            "title": "Data Pulse",
            "value": "LIVE" if search_live or ga_live else "待機",
            "detail": f"SC {'OK' if search_live else '0'} / GA4 {'OK' if ga_live else '0'}",
            "icon": "KPI",
            "tone": "blue",
            "progress": 84 if search_live or ga_live else 34,
        },
        {
            "title": "Quality Guard",
            "value": ai_guard["status"],
            "detail": f"本人感未確認 {ai_guard['identity_missing']}件",
            "icon": "QC",
            "tone": quality_tone,
            "progress": 92 if ai_guard["status"] == "正常" else 58 if ai_guard["status"] == "注意" else 28,
        },
        {
            "title": "Blocker Watch",
            "value": f"{blocker_count}件",
            "detail": "止まりどころを即チェック",
            "icon": "CEO",
            "tone": "red" if blocker_count else "green",
            "progress": 22 if blocker_count else 96,
        },
    ]
    html_parts = ['<div class="momentum-board">']
    for card in cards:
        html_parts.append(
            f'<div class="momentum-card {card["tone"]}">'
            '<div class="momentum-scan"></div>'
            '<div class="momentum-top">'
            f'<div class="momentum-icon">{card["icon"]}</div>'
            f'<div class="momentum-title">{card["title"]}</div>'
            '</div>'
            f'<div class="momentum-value">{card["value"]}</div>'
            f'<div class="momentum-detail">{_html_escape(card["detail"])}</div>'
            f'<div class="momentum-meter"><span style="width:{card["progress"]}%"></span></div>'
            '</div>'
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def _render_ai_employee_run(job) -> None:
    st.markdown("## AI社員 Live Run")
    status_label = {
        "running": "実行中",
        "syncing": "Drive同期中",
        "completed": "完了",
        "failed": "要確認",
        "idle": "待機中",
    }.get(job["status"], "待機中")
    banner_tone = {
        "running": "running",
        "syncing": "running",
        "completed": "success",
        "failed": "failed",
        "idle": "idle",
    }.get(job["status"], "idle")
    st.markdown(
        f"""
        <div class="employee-banner {banner_tone}">
          <div>
            <div class="employee-banner-label">AI COMPANY RUNNER</div>
            <div class="employee-banner-title">{status_label}</div>
          </div>
          <div class="employee-banner-meta">
            <span>現在: {_html_escape(job["current_step"])}</span>
            <span>更新: {_html_escape(job["updated_at"])}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    html_parts = ['<div class="employee-runway">']
    for employee in job["employees"]:
        html_parts.append(
            f'<div class="employee-card {employee["status"]}">'
            '<div class="employee-orbit"><span></span></div>'
            f'<div class="employee-avatar">{employee["code"]}</div>'
            f'<div class="employee-name">{employee["name"]}</div>'
            f'<div class="employee-role">{employee["role"]}</div>'
            f'<div class="employee-state">{employee["label"]}</div>'
            '</div>'
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)

    if job["status"] in {"running", "syncing"}:
        components.html(
            """
            <script>
              setTimeout(() => {
                window.parent.location.reload();
              }, 4500);
            </script>
            """,
            height=0,
        )
        st.caption("ライブ連動中: 実行中だけ画面を自動更新します。")


def _render_daily_brief_factory(data) -> None:
    st.markdown("## Daily Brief Factory")
    status_label = {
        "running": "生成中",
        "completed": "生成完了",
        "failed": "要確認",
        "idle": "待機中",
    }.get(data["status"], "待機中")
    st.markdown(
        f"""
        <div class="brief-factory {data["status"]}">
          <div class="brief-factory-head">
            <div>
              <div class="brief-kicker">DAILY BRIEF LINE</div>
              <div class="brief-title">{status_label}</div>
            </div>
            <div class="brief-current">現在: {_html_escape(data["current_step"])}</div>
          </div>
          <div class="brief-track">
            <span></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    for column, item in zip(cols, data["cards"]):
        column.markdown(
            f"""
            <div class="brief-card {item["tone"]}">
              <div class="brief-card-top">
                <div class="brief-code">{item["code"]}</div>
                <span>{item["status_label"]}</span>
              </div>
              <div class="brief-card-title">{item["title"]}</div>
              <div class="brief-card-date">{item["date"]}</div>
              <div class="brief-card-task">{_html_escape(item["top_task"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    step_cols = st.columns(4)
    for column, step in zip(step_cols, data["steps"]):
        column.markdown(
            f"""
            <div class="brief-step {step["status"]}">
              <div class="brief-step-dot"></div>
              <div class="brief-step-name">{step["label"]}</div>
              <div class="brief-step-owner">{step["employee"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    action_cols = st.columns([1, 1, 2])
    if action_cols[0].button("Daily Brief更新", width="stretch"):
        result = _start_daily_brief_job()
        st.session_state["action_result"] = result
        st.rerun()
    if action_cols[1].button("CEO_REPORTを開く", width="stretch"):
        st.session_state["detail_focus"] = "CEO Report"

    with action_cols[2]:
        st.caption("更新すると、各部署Brief生成からAI社長レポート生成まで実行します。投稿・WordPress更新・削除は行いません。")

    if data["status"] == "running":
        components.html(
            """
            <script>
              setTimeout(() => {
                window.parent.location.reload();
              }, 3500);
            </script>
            """,
            height=0,
        )
        st.caption("ライブ連動中: 生成中だけ画面を自動更新します。")


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
        "ai_beauty": _build_ai_beauty_guard_data(docs, latest_daily_dir),
        "wardrobe": _build_wardrobe_data(docs.get("Wardrobe Rotation", "")),
        "runner_job": _runner_job_state(docs.get("Run Report", "")),
        "daily_brief": _daily_brief_state(docs),
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


def _render_live_sync_toggle() -> None:
    st.markdown("## 表示")
    st.markdown('<div class="live-sync-pill">ライブ連動中</div>', unsafe_allow_html=True)
    st.caption("実行中だけAI社員の進捗に合わせて自動更新します。")
    mobile_url = _mobile_dashboard_url()
    st.markdown("## 携帯URL")
    st.code(mobile_url, language=None)
    st.caption("携帯は同じWi-FiでこのURLを開きます。`localhost`は携帯自身を指します。")


def _render_action_center(paths) -> None:
    st.markdown("## 操作")
    action_cols = st.columns(6)
    if action_cols[0].button("Runner実行", width="stretch"):
        result = _start_runner_job([sys.executable, "06_AI_COMPANY_Runner/main.py"])
        st.session_state["action_result"] = result
        st.rerun()

    actions = [
        ("KPI更新", [sys.executable, "generate_kpi_dashboard.py"]),
        ("CEO_REPORT再生成", [sys.executable, "05_AI社長/main.py"]),
    ]
    for column, (label, command) in zip(action_cols[1:3], actions):
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


def _render_mobile_command_strip(dashboard) -> None:
    kpi = dashboard["kpi"]
    blockers = dashboard["blockers"]
    x_rows = _load_x_result_rows()
    st.markdown(
        f"""
        <div class="mobile-command">
          <div class="mobile-command-head">
            <div>
              <div class="mobile-kicker">TODAY</div>
              <div class="mobile-title">会社状態</div>
            </div>
            <div class="live-pill"><span></span>LIVE</div>
          </div>
          <div class="mobile-grid">
            <div><strong>{kpi.get("posts", "未取得")}</strong><span>記事</span></div>
            <div><strong>{kpi.get("page_views", "未取得")}</strong><span>PV</span></div>
            <div><strong>{len(blockers)}</strong><span>Blocker</span></div>
            <div><strong>{len(x_rows)}</strong><span>X蓄積</span></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_company_overview(dashboard, docs, x_rows) -> None:
    st.markdown("## 会社サマリー")
    kpi = dashboard["kpi"]
    overview = [
        {
            "label": "WordPress",
            "value": f"{kpi.get('published', '未取得')}公開",
            "detail": f"カテゴリ {kpi.get('categories', '未取得')} / タグ {kpi.get('tags', '未取得')}",
            "tone": "ok",
        },
        {
            "label": "Search Console",
            "value": f"{kpi.get('clicks', '未取得')} clicks",
            "detail": f"impressions {kpi.get('impressions', '未取得')} / CTR {kpi.get('ctr', '未取得')}",
            "tone": "warn" if _as_number(kpi.get("impressions")) == 0 else "ok",
        },
        {
            "label": "GA4",
            "value": f"{kpi.get('page_views', '未取得')} PV",
            "detail": f"users {kpi.get('users', '未取得')} / sessions {kpi.get('sessions', '未取得')}",
            "tone": "warn" if _as_number(kpi.get("page_views")) == 0 else "ok",
        },
        {
            "label": "X Data",
            "value": f"{len(x_rows)}件",
            "detail": _latest_x_result_label(x_rows),
            "tone": "ok" if x_rows else "warn",
        },
    ]
    cols = st.columns(4)
    for column, item in zip(cols, overview):
        column.markdown(
            f"""
            <div class="hub-card {item["tone"]}">
              <div class="hub-card-pulse"></div>
              <div class="hub-label">{item["label"]}</div>
              <div class="hub-value">{item["value"]}</div>
              <div class="hub-detail">{item["detail"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## 事業部ステータス")
    departments = [
        ("P002 SNS", docs.get("P002 Daily Brief", ""), "投稿素材 / X結果蓄積"),
        ("P003 グラビア", docs.get("P003 Daily Brief", ""), "SEO改善 / 効果測定"),
        ("P004 アダルト", docs.get("P004 Daily Brief", ""), "対象記事判定 / SEO設計"),
        ("P005 AI社長", docs.get("CEO Report", ""), "経営判断"),
        ("P006 Runner", docs.get("Run Report", ""), "毎朝実行"),
    ]
    cols = st.columns(5)
    for column, (name, content, focus) in zip(cols, departments):
        status = "正常" if content else "未取得"
        if name == "P006 Runner" and content and "## 失敗\n\n- なし" not in content:
            status = "注意"
        tone = _status_tone(status)
        icon = {"正常": "🟢", "注意": "🟡"}.get(status, "🔴")
        column.markdown(
            f"""
            <div class="department-card {tone}">
              <div class="department-icon">{icon}</div>
              <div class="department-name">{name}</div>
              <div class="department-status">{status}</div>
              <div class="department-focus">{focus}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_company_flow(dashboard) -> None:
    st.markdown("## 今日の流れ")
    steps = [
        ("P002", "SNS素材確認", "done"),
        ("P003", "SEO効果測定", "active"),
        ("P004", "対象記事判定", "active" if dashboard["blockers"] else "done"),
        ("P005", "経営判断", "done"),
        ("P006", "Drive同期", "done"),
    ]
    html = ['<div class="flow-lane">']
    for label, title, state in steps:
        html.append(
            f"""
            <div class="flow-step {state}">
              <div class="flow-dot"></div>
              <div class="flow-label">{label}</div>
              <div class="flow-title">{title}</div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_ai_beauty_guard(data) -> None:
    st.markdown("## AI美女 品質監査")
    st.caption("別人化・AI感・本人感レビュー未入力を投稿前リスクとして集約します。")
    cards = [
        ("総合判定", data["status"], data["status_detail"], data["tone"]),
        ("本人感未確認", f"{data['identity_missing']}件", "目視レビュー未入力", "bad" if data["identity_missing"] else "ok"),
        ("別人化リスク", f"{data['identity_risk']}件", "別人感・顔ズレ記録", "bad" if data["identity_risk"] else "ok"),
        ("AI認定リスク", f"{data['ai_risk']}件", "AI感・不自然・破綻記録", "warn" if data["ai_risk"] else "ok"),
    ]
    cols = st.columns(4)
    for column, (label, value, detail, tone) in zip(cols, cards):
        column.markdown(
            f"""
            <div class="beauty-guard-card {tone}">
              <div class="beauty-icon">{_beauty_icon(tone)}</div>
              <div class="beauty-label">{label}</div>
              <div class="beauty-value">{value}</div>
              <div class="beauty-detail">{detail}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("### 投稿前チェック")
        checklist = [
            ("本人固定リファレンス優先", data["rules"].get("reference_lock", "未取得")),
            ("衣装資料は服だけに使う", data["rules"].get("outfit_limited", "未取得")),
            ("AI美女顔に寄せすぎない", data["rules"].get("avoid_ai_face", "未取得")),
            ("本人感レビュー未入力はPASS禁止", data["rules"].get("identity_required", "未取得")),
        ]
        for title, detail in checklist:
            st.markdown(
                f"""
                <div class="guard-check">
                  <div class="guard-check-mark">✓</div>
                  <div>
                    <div class="guard-check-title">{title}</div>
                    <div class="guard-check-detail">{detail}</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("### 要確認画像")
        if not data["risk_items"]:
            st.success("要確認画像はありません。")
        for item in data["risk_items"][:5]:
            st.markdown(
                f"""
                <div class="risk-item">
                  <div class="risk-item-head">
                    <strong>{item['character']} / {item['slot']}</strong>
                    <span>{item['status']}</span>
                  </div>
                  <div class="risk-item-path">{item['image']}</div>
                  <div class="risk-item-warning">{_html_escape(item['warning'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("AI-VQC / 固定ルール"):
        st.markdown("#### AI-VQC")
        st.markdown(data["docs"].get("AI-VQC", "未取得"))
        st.markdown("#### MIKU Fixed Rules")
        st.markdown(data["docs"].get("MIKU Fixed Rules", "未取得"))
        st.markdown("#### RIO Base Reference")
        st.markdown(data["docs"].get("RIO Base Reference", "未取得"))


def _render_wardrobe_rotation(data) -> None:
    st.markdown("## 衣装ローテ監査")
    st.caption("服装の単調さを防ぐため、衣装タグと次回候補を確認します。画像から断定せず、根拠がない場合は未取得にします。")

    status_tone = "ok" if data["status"] == "OK" else "warn"
    st.markdown(
        f"""
        <div class="wardrobe-status {status_tone}">
          <div>
            <div class="wardrobe-status-label">選定方式</div>
            <div class="wardrobe-status-title">{data["method"]}</div>
          </div>
          <div class="wardrobe-status-pill">{data["status"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for column, character in zip(cols, ("MIKU", "RIO")):
        with column:
            st.markdown(f"### {character}")
            rows = [row for row in data["today"] if row.get("キャラクター") == character]
            if not rows:
                st.info("今日の衣装タグは未取得です。")
            for row in rows:
                tone = "warn" if row.get("衣装タグ") == "未取得" else "ok"
                st.markdown(
                    f"""
                    <div class="wardrobe-card {tone}">
                      <div class="wardrobe-card-head">
                        <strong>{_html_escape(row.get("枠", "未取得"))}</strong>
                        <span>{_html_escape(row.get("衣装タグ", "未取得"))}</span>
                      </div>
                      <div class="wardrobe-card-body">
                        根拠: {_html_escape(row.get("根拠", "未取得"))}<br>
                        画像数: {_html_escape(row.get("画像数", "0"))} / 信頼度: {_html_escape(row.get("信頼度", "低"))}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            recommendation = data["recommendations"].get(character)
            if recommendation:
                st.markdown(
                    f"""
                    <div class="wardrobe-next">
                      <div class="wardrobe-next-label">明日の候補</div>
                      <div class="wardrobe-next-title">{_html_escape(recommendation.get("推奨衣装", "要確認"))}</div>
                      <div class="wardrobe-next-reason">{_html_escape(recommendation.get("理由", "未取得"))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if data["blockers"]:
        for blocker in data["blockers"]:
            st.markdown(
                f'<div class="blocker warn">🟡 {_html_escape(blocker)}</div>',
                unsafe_allow_html=True,
            )
    with st.expander("WARDROBE_ROTATION_REPORT.md"):
        st.caption(str(WARDROBE_ROTATION_REPORT_PATH))
        st.markdown(data["raw"] or "未取得")


def _render_x_result_paste() -> None:
    st.markdown("## X結果を貼って蓄積")
    st.caption("Xの投稿結果を貼り付けて保存します。SNS投稿やログイン操作は行いません。")
    with st.container(border=True):
        cols = st.columns(3)
        character = cols[0].selectbox("キャラクター", ("MIKU", "RIO", "共通"), key="x-character")
        post_date = cols[1].date_input("投稿日", value=date.today(), key="x-date")
        platform = cols[2].selectbox("SNS", ("X",), key="x-platform")
        post_url = st.text_input("投稿URL", placeholder="https://x.com/...", key="x-url")
        pasted = st.text_area(
            "Xの結果を貼り付け",
            height=170,
            placeholder="例: インプレッション 1234 / いいね 56 / リポスト 7 / 返信 2 / プロフィールクリック 10 / リンククリック 3",
            key="x-paste",
        )
        parsed = _parse_x_result_text(pasted)
        metric_cols = st.columns(6)
        impressions = metric_cols[0].number_input("表示回数", min_value=0, value=parsed.get("impressions", 0), step=1)
        likes = metric_cols[1].number_input("いいね", min_value=0, value=parsed.get("likes", 0), step=1)
        reposts = metric_cols[2].number_input("リポスト", min_value=0, value=parsed.get("reposts", 0), step=1)
        replies = metric_cols[3].number_input("返信", min_value=0, value=parsed.get("replies", 0), step=1)
        profile_clicks = metric_cols[4].number_input("プロフィール", min_value=0, value=parsed.get("profile_clicks", 0), step=1)
        link_clicks = metric_cols[5].number_input("リンク", min_value=0, value=parsed.get("link_clicks", 0), step=1)
        memo = st.text_area("メモ", height=90, key="x-memo")
        if st.button("X結果を保存", width="stretch"):
            row = {
                "id": uuid.uuid4().hex[:10],
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "date": post_date.isoformat(),
                "character": character,
                "platform": platform,
                "url": _clean_table_cell(post_url) or "未取得",
                "impressions": str(impressions),
                "likes": str(likes),
                "reposts": str(reposts),
                "replies": str(replies),
                "profile_clicks": str(profile_clicks),
                "link_clicks": str(link_clicks),
                "engagement": str(likes + reposts + replies),
                "memo": _clean_table_cell(memo),
                "raw": pasted.strip(),
            }
            result = _save_x_result(row)
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])


def _render_x_result_history(rows) -> None:
    st.markdown("## X蓄積データ")
    if not rows:
        st.info("まだX結果は保存されていません。")
        return
    totals = _x_totals(rows)
    metric_cols = st.columns(4)
    metric_cols[0].metric("保存件数", len(rows))
    metric_cols[1].metric("表示回数", _format_metric(totals["impressions"]))
    metric_cols[2].metric("Engagement", _format_metric(totals["engagement"]))
    metric_cols[3].metric("リンククリック", _format_metric(totals["link_clicks"]))
    st.dataframe(
        [
            {
                "date": row.get("date", ""),
                "character": row.get("character", ""),
                "url": row.get("url", ""),
                "impressions": row.get("impressions", "0"),
                "engagement": row.get("engagement", "0"),
                "link_clicks": row.get("link_clicks", "0"),
                "saved_at": row.get("saved_at", ""),
            }
            for row in reversed(rows[-20:])
        ],
        width="stretch",
        hide_index=True,
    )
    st.caption(f"保存先: {X_RESULT_LOG_PATH} / {X_RESULT_CSV_PATH}")


def _render_company_knowledge_base(docs, paths) -> None:
    st.markdown("## AI COMPANY 情報集約")
    tabs = st.tabs(("経営", "SNS", "AI美女", "グラビア", "アダルト", "Runner"))
    groups = [
        ("CEO Report", "KPI Dashboard"),
        ("P002 Daily Brief", "SNS Report"),
        (
            "Generation Quality",
            "AI-VQC",
            "MIKU Fixed Rules",
            "RIO Base Reference",
            "Selfie Phone Rules",
        ),
        ("P003 Daily Brief", "P003 Report", "Improvement Backlog", "Execution Board"),
        ("P004 Daily Brief", "P004 Report"),
        ("Run Report",),
    ]
    for tab, names in zip(tabs, groups):
        with tab:
            for name in names:
                with st.expander(name):
                    st.caption(str(paths.get(name, "")))
                    st.markdown(docs.get(name) or "未取得")


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
          <div class="sns-theme-outfit">衣装: {post.get("outfit", "未取得")} / 根拠: {post.get("outfit_source", "未取得")}</div>
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
        "P004 Daily Brief",
        "Improvement Backlog",
        "Execution Board",
        "P003 Task",
        "Approvals",
        "Generation Quality",
        "AI-VQC",
        "MIKU Fixed Rules",
        "RIO Base Reference",
        "Selfie Phone Rules",
    ):
        with st.expander(name, expanded=(focus == name)):
            st.caption(str(paths.get(name, "")))
            content = docs.get(name) or "未取得"
            st.markdown(content)


def _render_artifact_grid(items) -> None:
    if not items:
        st.info("成果物はありません。")
        return
    cols = st.columns(3)
    for index, item in enumerate(items):
        column = cols[index % len(cols)]
        with column:
            tone = "ready" if item["exists"] else "missing"
            st.markdown(
                f"""
                <div class="artifact-card {tone}">
                  <div class="artifact-head">
                    <span>{item["category"]}</span>
                    <strong>{item["status"]}</strong>
                  </div>
                  <div class="artifact-title">{item["title"]}</div>
                  <div class="artifact-path">{_html_escape(item["path"])}</div>
                  <div class="artifact-meta">更新: {item["modified"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if item["exists"]:
                with st.expander("本文を見る"):
                    content = _read_text(Path(item["path"]))
                    st.markdown(content or "未取得")
                    st.download_button(
                        "ダウンロード",
                        data=(content or "").encode("utf-8"),
                        file_name=Path(item["path"]).name,
                        mime="text/markdown",
                        width="stretch",
                        key=f"download-{item['path']}",
                    )


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


def _build_ai_beauty_guard_data(docs, latest_daily_dir):
    report_items = _collect_visual_quality_items(latest_daily_dir)
    quality_markdown = docs.get("Generation Quality", "")
    markdown_risks = _extract_generation_quality_risks(quality_markdown)
    identity_missing = sum(1 for item in report_items if item["identity_missing"])
    identity_risk = sum(1 for item in report_items if item["identity_risk"]) + markdown_risks["identity_risk"]
    ai_risk = sum(1 for item in report_items if item["ai_risk"]) + markdown_risks["ai_risk"]
    fail_count = sum(1 for item in report_items if item["status"] == "FAIL")
    review_count = sum(1 for item in report_items if item["status"] == "REVIEW")
    risk_items = [
        item
        for item in report_items
        if item["identity_missing"] or item["identity_risk"] or item["ai_risk"] or item["status"] in {"FAIL", "REVIEW"}
    ]
    if identity_missing or identity_risk or fail_count:
        status = "要確認"
        tone = "bad"
        status_detail = f"FAIL {fail_count}件 / REVIEW {review_count}件"
    elif ai_risk:
        status = "注意"
        tone = "warn"
        status_detail = "AI感・不自然表現の確認あり"
    else:
        status = "正常"
        tone = "ok"
        status_detail = "投稿前リスクなし"

    return {
        "status": status,
        "tone": tone,
        "status_detail": status_detail,
        "identity_missing": identity_missing,
        "identity_risk": identity_risk,
        "ai_risk": ai_risk,
        "risk_items": risk_items,
        "rules": _extract_ai_beauty_rules(docs),
        "docs": {
            "AI-VQC": docs.get("AI-VQC", ""),
            "MIKU Fixed Rules": docs.get("MIKU Fixed Rules", ""),
            "RIO Base Reference": docs.get("RIO Base Reference", ""),
        },
    }


def _collect_visual_quality_items(latest_daily_dir):
    items = []
    for report_path in _visual_quality_report_paths(latest_daily_dir):
        try:
            data = _load_json(report_path)
        except ValueError:
            continue
        warnings = _visual_quality_findings(data)
        warning_text = " / ".join(str(item) for item in warnings)
        relative = _display_path(report_path)
        base_dir = _visual_quality_base_dir(report_path, latest_daily_dir)
        try:
            parts = report_path.relative_to(base_dir).parts
        except ValueError:
            parts = report_path.parts
        character = parts[0] if parts else "未取得"
        slot = parts[1] if len(parts) > 1 else "未取得"
        image_value = data.get("source_path") or data.get("image") or data.get("path") or data.get("file_name") or report_path.name
        identity_score = data.get("identity_review_score")
        items.append(
            {
                "character": _html_escape(character),
                "slot": _html_escape(slot),
                "status": str(data.get("status", "未取得")).upper(),
                "score": data.get("score") or data.get("score_summary", {}).get("average") or "未取得",
                "image": _html_escape(str(image_value) if image_value != report_path.name else relative),
                "warning": _shorten_text(warning_text or "未取得", 220),
                "identity_missing": bool(data.get("identity_review_required")) and identity_score in (None, ""),
                "identity_risk": _contains_any(warning_text, ("別人", "本人感", "顔が", "顔ズレ", "face_matches_base")),
                "ai_risk": _contains_any(warning_text, ("AI", "不自然", "破綻", "滑らか", "背景文字", "ロゴ")),
            }
        )
    return items


def _visual_quality_report_paths(latest_daily_dir):
    candidates = []
    if latest_daily_dir:
        candidates.extend(sorted(latest_daily_dir.glob("*/**/reports/image_*_report.json")))
    if candidates:
        return candidates

    output_root = WORKSPACE_ROOT / "02_Daily_Output"
    if not output_root.exists():
        return []
    for daily_dir in sorted((path for path in output_root.iterdir() if path.is_dir()), key=lambda path: path.name, reverse=True):
        candidates = sorted(daily_dir.glob("*/**/reports/image_*_report.json"))
        if candidates:
            return candidates
    return []


def _visual_quality_base_dir(report_path: Path, latest_daily_dir):
    if latest_daily_dir and report_path.is_relative_to(latest_daily_dir):
        return latest_daily_dir
    output_root = WORKSPACE_ROOT / "02_Daily_Output"
    try:
        relative = report_path.relative_to(output_root)
    except ValueError:
        return report_path.parent
    if relative.parts:
        return output_root / relative.parts[0]
    return report_path.parent


def _visual_quality_findings(data):
    findings = []
    for key in (
        "warnings",
        "review_reasons",
        "critical_errors",
        "person_findings",
        "object_findings",
        "background_findings",
        "photo_quality_findings",
        "character_consistency_findings",
    ):
        value = data.get(key)
        if isinstance(value, list):
            findings.extend(value)
        elif value:
            findings.append(value)
    return findings


def _extract_generation_quality_risks(content: str):
    review_section = _extract_section(content, "Review Required")
    return {
        "identity_risk": sum(1 for line in review_section.splitlines() if "別人" in line or "本人感" in line),
        "ai_risk": sum(1 for line in review_section.splitlines() if "AI" in line or "不自然" in line or "破綻" in line),
    }


def _extract_ai_beauty_rules(docs):
    ai_vqc = docs.get("AI-VQC", "")
    miku = docs.get("MIKU Fixed Rules", "")
    rio = docs.get("RIO Base Reference", "")
    return {
        "reference_lock": _first_rule_line(rio, ("最優先", "顔を最優先", "本人感")) or "本人固定資料を最優先する。",
        "outfit_limited": _first_rule_line(miku + "\n" + rio, ("服装だけ", "顔や体型を持ち込んでいない")) or "衣装資料は顔・体型へ使わない。",
        "avoid_ai_face": _first_rule_line(miku + "\n" + rio, ("AI美女", "美少女")) or "AI美女顔・若く盛りすぎを避ける。",
        "identity_required": _first_rule_line(ai_vqc, ("自動PASS", "本人感レビュー未入力")) or "本人感レビュー未入力はPASS禁止。",
    }


def _build_wardrobe_data(content: str) -> dict:
    today_rows = _parse_section_markdown_table(content, "今日の衣装タグ")
    recommendation_rows = _parse_section_markdown_table(content, "明日の衣装候補")
    blockers = _extract_simple_blockers(content)
    recommendations = {
        row.get("キャラクター", ""): row
        for row in recommendation_rows
        if row.get("キャラクター")
    }
    missing_count = sum(1 for row in today_rows if row.get("衣装タグ") == "未取得")
    return {
        "raw": content,
        "today": today_rows,
        "recommendations": recommendations,
        "blockers": blockers,
        "status": "OK" if today_rows and missing_count == 0 else "要確認",
        "method": "優先候補 + 衣装タグ監査" if content else "衣装ローテ未生成",
    }


def _extract_simple_blockers(content: str):
    section = _extract_section(content, "Blocker")
    blockers = []
    for line in section.splitlines():
        clean = line.strip()
        if not clean or clean in {"なし", "- なし"}:
            continue
        if clean.startswith("- "):
            blockers.append(clean[2:])
        elif clean.startswith("・"):
            blockers.append(clean[1:])
    return blockers


def _parse_section_markdown_table(content: str, section_heading: str):
    section = _extract_section(content, section_heading)
    rows = []
    headers = []
    for line in section.splitlines():
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


def _first_rule_line(content: str, keywords) -> str:
    for line in content.splitlines():
        clean = line.strip().lstrip("-").strip()
        if clean and any(keyword in clean for keyword in keywords):
            return clean
    return ""


def _beauty_icon(tone: str) -> str:
    if tone == "ok":
        return "OK"
    if tone == "warn":
        return "!"
    return "NG"


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(str(exc)) from exc


def _contains_any(text: str, keywords) -> bool:
    return any(keyword in (text or "") for keyword in keywords)


def _shorten_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _html_escape(value) -> str:
    return html.escape(str(value), quote=True)


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


def _mobile_dashboard_url() -> str:
    ip_address = "localhost"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
    except OSError:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip_address = "localhost"
    return f"http://{ip_address}:8510/"


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


def _artifact_items(latest_daily_dir):
    latest_ceo = _latest_artifact("CEO_REPORT.md", latest_daily_dir)
    latest_kpi = _latest_artifact("KPI_DASHBOARD.md", latest_daily_dir)
    latest_run = _latest_artifact("RUN_REPORT.md", latest_daily_dir)
    definitions = [
        ("経営", "CEO_REPORT", latest_ceo),
        ("経営", "KPI_DASHBOARD", latest_kpi),
        ("Runner", "RUN_REPORT", latest_run),
        ("SNS", "P002 DAILY_BRIEF", INPUTS["P002 Daily Brief"]),
        ("SNS", "SNS_REPORT", Path("03_SNS事業部") / "SNS_REPORT.md"),
        ("SNS", "TODAY_POST", TODAY_POST_PATH),
        ("SNS", "WARDROBE_ROTATION_REPORT", WARDROBE_ROTATION_REPORT_PATH),
        ("グラビア", "P003 DAILY_BRIEF", INPUTS["P003 Daily Brief"]),
        ("グラビア", "P003 REPORT", P003_PROJECT_DIR / "REPORT.md"),
        ("グラビア", "CATEGORY_FIX_PLAN", P003_PROJECT_DIR / "CATEGORY_FIX_PLAN.md"),
        ("グラビア", "INTERNAL_LINK_PLAN", P003_PROJECT_DIR / "INTERNAL_LINK_PLAN.md"),
        ("グラビア", "TITLE_IMPROVEMENT_PLAN", P003_PROJECT_DIR / "TITLE_IMPROVEMENT_PLAN.md"),
        ("グラビア", "IMPROVEMENT_BACKLOG", IMPROVEMENT_BACKLOG_PATH),
        ("グラビア", "EXECUTION_BOARD", EXECUTION_BOARD_PATH),
        ("アダルト", "P004 DAILY_BRIEF", INPUTS["P004 Daily Brief"]),
        ("アダルト", "P004 REPORT", Path("04_アダルト事業部") / "REPORT.md"),
        ("アダルト", "SEO_PLAN", Path("04_アダルト事業部") / "SEO_PLAN.md"),
        ("品質", "GENERATION_QUALITY_REPORT", GENERATION_QUALITY_REPORT_PATH),
        ("品質", "AI_VQC", AI_VQC_PATH),
    ]
    if latest_daily_dir:
        for path in sorted(latest_daily_dir.glob("*.md")):
            rel = path.relative_to(WORKSPACE_ROOT)
            if rel not in [Path(item[2]) for item in definitions]:
                definitions.append(("Daily Output", path.stem, rel))
    return [_artifact_item(category, title, path) for category, title, path in definitions]


def _artifact_item(category: str, title: str, path: Path):
    absolute = _absolute(path)
    exists = absolute.exists()
    modified = "未取得"
    if exists:
        try:
            modified = datetime.fromtimestamp(absolute.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            modified = "未取得"
    return {
        "category": category,
        "title": title,
        "path": str(path),
        "exists": exists,
        "status": "表示可" if exists else "未取得",
        "modified": modified,
    }


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
                "outfit": _extract_list_value(block, "衣装タグ") or "未取得",
                "outfit_source": _extract_list_value(block, "衣装根拠") or "未取得",
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


def _parse_x_result_text(text: str) -> dict[str, int]:
    if not text.strip():
        return {}
    normalized = (
        text.replace(",", "")
        .replace("：", ":")
        .replace("　", " ")
        .replace("\t", " ")
    )
    aliases = {
        "impressions": ("impressions", "impression", "インプレッション", "表示回数", "views", "view"),
        "likes": ("likes", "like", "いいね"),
        "reposts": ("reposts", "repost", "retweets", "retweet", "リポスト", "リツイート"),
        "replies": ("replies", "reply", "返信", "コメント"),
        "profile_clicks": ("profile clicks", "profile_clicks", "プロフィールクリック", "プロフィール"),
        "link_clicks": ("link clicks", "link_clicks", "url clicks", "リンククリック", "クリック"),
    }
    values = {}
    for key, names in aliases.items():
        values[key] = _find_metric_value(normalized, names)
    return values


def _find_metric_value(text: str, aliases) -> int:
    import re

    for alias in aliases:
        pattern = rf"{re.escape(alias)}\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)(?:万|k|K)?"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        value = float(match.group(1))
        suffix_match = re.search(pattern, text, re.IGNORECASE)
        matched_text = suffix_match.group(0) if suffix_match else ""
        if matched_text.endswith("万"):
            value *= 10000
        elif matched_text.lower().endswith("k"):
            value *= 1000
        return int(value)

    numbers = [int(value) for value in re.findall(r"\b[0-9]+\b", text)]
    return numbers[0] if len(aliases) == 1 and numbers else 0


def _save_x_result(row: dict[str, str]):
    try:
        absolute_dir = _absolute(X_RESULT_DIR)
        absolute_dir.mkdir(parents=True, exist_ok=True)
        rows = _load_x_result_rows()
        rows.append(row)
        _absolute(X_RESULT_LOG_PATH).write_text(_format_x_result_log(rows), encoding="utf-8")
        _write_x_result_csv(rows)
        raw_path = absolute_dir / f"{row['date']}_{row['character']}_{row['id']}.txt"
        raw_path.write_text(row.get("raw", ""), encoding="utf-8")
        return {"success": True, "message": "X結果を保存しました。"}
    except OSError as exc:
        return {"success": False, "message": f"X結果を保存できませんでした: {exc}"}


def _load_x_result_rows():
    content = _read_text(X_RESULT_LOG_PATH)
    rows = _parse_any_markdown_table(content)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "id": row.get("ID", ""),
                "saved_at": row.get("保存日時", ""),
                "date": row.get("投稿日", ""),
                "character": row.get("キャラクター", ""),
                "platform": row.get("SNS", ""),
                "url": row.get("投稿URL", ""),
                "impressions": row.get("表示回数", "0"),
                "likes": row.get("いいね", "0"),
                "reposts": row.get("リポスト", "0"),
                "replies": row.get("返信", "0"),
                "profile_clicks": row.get("プロフィールクリック", "0"),
                "link_clicks": row.get("リンククリック", "0"),
                "engagement": row.get("Engagement", "0"),
                "memo": row.get("メモ", ""),
            }
        )
    return normalized


def _format_x_result_log(rows) -> str:
    lines = [
        "# X RESULT LOG",
        "",
        "Xの結果を手動で貼り付け、AI COMPANY内に蓄積する。",
        "",
        "| ID | 保存日時 | 投稿日 | キャラクター | SNS | 投稿URL | 表示回数 | いいね | リポスト | 返信 | プロフィールクリック | リンククリック | Engagement | メモ |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {saved_at} | {date} | {character} | {platform} | {url} | {impressions} | {likes} | {reposts} | {replies} | {profile_clicks} | {link_clicks} | {engagement} | {memo} |".format(
                **{key: _clean_table_cell(row.get(key, "")) for key in row}
            )
        )
    lines.extend(
        [
            "",
            "## 制約確認",
            "",
            "- SNS自動投稿: 未実行",
            "- SNSログイン操作: 未実行",
            "- 削除: 未実行",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _write_x_result_csv(rows) -> None:
    path = _absolute(X_RESULT_CSV_PATH)
    fieldnames = [
        "id",
        "saved_at",
        "date",
        "character",
        "platform",
        "url",
        "impressions",
        "likes",
        "reposts",
        "replies",
        "profile_clicks",
        "link_clicks",
        "engagement",
        "memo",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _x_totals(rows):
    return {
        "impressions": sum(_as_number(row.get("impressions")) for row in rows),
        "engagement": sum(_as_number(row.get("engagement")) for row in rows),
        "link_clicks": sum(_as_number(row.get("link_clicks")) for row in rows),
    }


def _latest_x_result_label(rows) -> str:
    if not rows:
        return "未保存"
    latest = rows[-1]
    return f"{latest.get('date', '未取得')} / {latest.get('character', '未取得')}"


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
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and not any(part.lower() in {"fail", "failed", "reject", "rejected"} for part in path.parts)
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

    fallback_daily = _latest_existing_daily_artifact(filename)
    if fallback_daily:
        return fallback_daily.relative_to(WORKSPACE_ROOT)

    if filename == "RUN_REPORT.md":
        fallback = WORKSPACE_ROOT / "06_AI_COMPANY_Runner" / "RUN_REPORT.md"
        if fallback.exists():
            return fallback.relative_to(WORKSPACE_ROOT)

    return Path("02_Daily_Output") / date.today().isoformat() / filename


def _latest_existing_daily_artifact(filename: str):
    output_root = WORKSPACE_ROOT / "02_Daily_Output"
    if not output_root.exists():
        return None
    for daily_dir in sorted((path for path in output_root.iterdir() if path.is_dir()), key=lambda path: path.name, reverse=True):
        candidate = daily_dir / filename
        if candidate.exists():
            return candidate
    return None


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


def _start_runner_job(command):
    current = _runner_job_state("")
    if current["status"] in {"running", "syncing"}:
        return {
            "success": True,
            "message": "Runnerは実行中です。AI社員Live Runを確認してください。",
            "output": "",
        }

    job_dir = _absolute(RUNNER_JOB_DIR)
    job_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = _absolute(RUNNER_STDOUT_PATH)
    stderr_path = _absolute(RUNNER_STDERR_PATH)
    try:
        stdout_file = stdout_path.open("w", encoding="utf-8")
        stderr_file = stderr_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=str(WORKSPACE_ROOT),
            text=True,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
        )
        stdout_file.close()
        stderr_file.close()
    except Exception as exc:
        return {"success": False, "message": f"Runner開始失敗: {exc}", "output": ""}

    now = datetime.now().isoformat(timespec="seconds")
    payload = {
        "status": "running",
        "pid": process.pid,
        "started_at": now,
        "updated_at": now,
        "command": " ".join(command),
    }
    _write_dashboard_json(RUNNER_JOB_PATH, payload)
    st.session_state["runner_process"] = process
    return {
        "success": True,
        "message": "Runner開始。AI社員が動き始めました。",
        "output": f"pid={process.pid}",
    }


def _start_daily_brief_job():
    current = _daily_brief_process_status()
    if current in {"running"}:
        return {
            "success": True,
            "message": "Daily Briefは生成中です。Daily Brief Factoryを確認してください。",
            "output": "",
        }

    command = [sys.executable, "07_Editor_Dashboard/run_daily_brief_job.py"]
    job_dir = _absolute(RUNNER_JOB_DIR)
    job_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = _absolute(BRIEF_STDOUT_PATH)
    stderr_path = _absolute(BRIEF_STDERR_PATH)
    try:
        stdout_file = stdout_path.open("w", encoding="utf-8")
        stderr_file = stderr_path.open("w", encoding="utf-8")
        process = subprocess.Popen(
            command,
            cwd=str(WORKSPACE_ROOT),
            text=True,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
        )
        stdout_file.close()
        stderr_file.close()
    except Exception as exc:
        return {"success": False, "message": f"Daily Brief開始失敗: {exc}", "output": ""}

    now = datetime.now().isoformat(timespec="seconds")
    payload = {
        "status": "running",
        "pid": process.pid,
        "started_at": now,
        "updated_at": now,
        "command": " ".join(command),
    }
    _write_dashboard_json(BRIEF_JOB_PATH, payload)
    st.session_state["daily_brief_process"] = process
    return {
        "success": True,
        "message": "Daily Brief生成開始。AI社員がBriefラインへ移動しました。",
        "output": f"pid={process.pid}",
    }


def _daily_brief_state(docs):
    process_status = _daily_brief_process_status()
    progress = _read_dashboard_json(BRIEF_PROGRESS_PATH)
    status = progress.get("status") if process_status == "running" else process_status
    if status not in {"running", "completed", "failed"}:
        status = "idle"

    brief_defs = [
        ("P002", "SNS事業部", "P002 Daily Brief", "SNS Daily Brief"),
        ("P003", "グラビア事業部", "P003 Daily Brief", "Gravure Daily Brief"),
        ("P004", "アダルト事業部", "P004 Daily Brief", "Adult Daily Brief"),
        ("CEO", "AI社長", "CEO Report", "CEO Report"),
    ]
    progress_steps = progress.get("steps") if isinstance(progress.get("steps"), list) else []
    progress_map = {item.get("name"): item.get("status") for item in progress_steps if isinstance(item, dict)}
    cards = []
    for code, title, doc_name, step_name in brief_defs:
        content = docs.get(doc_name, "")
        step_status = progress_map.get(step_name)
        tone = _brief_card_tone(content, step_status, status)
        cards.append(
            {
                "code": code,
                "title": title,
                "date": _brief_date(content),
                "top_task": _brief_top_task(content),
                "tone": tone,
                "status_label": _brief_status_label(tone),
            }
        )

    steps = _brief_pipeline_steps(progress_map, status)
    return {
        "status": status,
        "current_step": progress.get("current_step") or ("完了" if status == "completed" else "待機"),
        "cards": cards,
        "steps": steps,
    }


def _daily_brief_process_status() -> str:
    job = _read_dashboard_json(BRIEF_JOB_PATH)
    process = st.session_state.get("daily_brief_process")
    if process and job.get("status") == "running":
        returncode = process.poll()
        if returncode is None:
            return "running"
        job["status"] = "completed" if returncode == 0 else "failed"
        job["returncode"] = returncode
        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _write_dashboard_json(BRIEF_JOB_PATH, job)
        st.session_state.pop("daily_brief_process", None)
        return job["status"]
    if job.get("status") == "running":
        if _pid_is_running(job.get("pid")):
            return "running"
        progress = _read_dashboard_json(BRIEF_PROGRESS_PATH)
        status = progress.get("status")
        job["status"] = status if status in {"completed", "failed"} else "completed"
        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _write_dashboard_json(BRIEF_JOB_PATH, job)
        return job["status"]
    return job.get("status", "idle")


def _brief_pipeline_steps(progress_map, run_status):
    definitions = [
        ("入力確認", "入力確認", "管理AI"),
        ("SNS Daily Brief", "SNS生成", "SNS分析AI"),
        ("Gravure Daily Brief", "グラビア生成", "グラビア事業部長AI"),
        ("Adult Daily Brief", "アダルト生成", "アダルト事業部長AI"),
        ("CEO Report", "AI社長集約", "AI社長"),
    ]
    steps = []
    for step_name, label, employee in definitions:
        status = progress_map.get(step_name)
        if step_name == "入力確認" and run_status == "running" and not progress_map:
            status = "running"
        if run_status == "completed" and not status:
            status = "success"
        steps.append(
            {
                "label": label,
                "employee": employee,
                "status": status or "pending",
            }
        )
    return steps


def _brief_card_tone(content: str, step_status, run_status: str) -> str:
    if step_status == "running":
        return "running"
    if step_status == "failed":
        return "failed"
    if step_status == "success":
        return "ready"
    if not content:
        return "missing"
    if "DAILY_BRIEF saved with error" in content or ("Blocker" in content and "Error:" in content):
        return "warn"
    if run_status == "completed":
        return "ready"
    return "ready"


def _brief_status_label(tone: str) -> str:
    return {
        "running": "生成中",
        "ready": "提出済み",
        "failed": "要確認",
        "missing": "未提出",
        "warn": "注意",
    }.get(tone, "待機")


def _brief_date(content: str) -> str:
    if not content:
        return "未取得"
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "日付":
            continue
        for value in lines[index + 1 :]:
            clean = value.strip()
            if clean:
                return clean
    return "未取得"


def _brief_top_task(content: str) -> str:
    if not content:
        return "未取得"
    section = _extract_section(content, "今日やること TOP3")
    if not section:
        section = _extract_section(content, "今日やることTOP3")
    for line in section.splitlines():
        clean = line.strip()
        if clean.startswith("①"):
            return _shorten_text(clean, 58)
    lines = section.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "### Priority 1":
            continue
        for value in lines[index + 1 :]:
            clean = value.strip()
            if clean:
                return _shorten_text(clean, 58)
    summary = _extract_section(content, "本日の総評")
    if summary:
        return _shorten_text(summary, 58)
    return "未取得"


def _runner_job_state(run_report: str):
    job = _read_dashboard_json(RUNNER_JOB_PATH)
    progress = _read_dashboard_json(RUNNER_PROGRESS_PATH)
    process = st.session_state.get("runner_process")
    if process and job.get("status") in {"running", "syncing"}:
        returncode = process.poll()
        if returncode is not None:
            job["status"] = "completed" if returncode == 0 else "failed"
            job["returncode"] = returncode
            job["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _write_dashboard_json(RUNNER_JOB_PATH, job)
            st.session_state.pop("runner_process", None)
    elif job.get("status") in {"running", "syncing"} and not _pid_is_running(job.get("pid")):
        job["status"] = "completed"
        job["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _write_dashboard_json(RUNNER_JOB_PATH, job)

    status = progress.get("status") or job.get("status") or ("completed" if run_report else "idle")
    if job.get("status") == "failed":
        status = "failed"
    current_step = progress.get("current_step") or _latest_run_current_step(run_report) or "待機"
    updated_at = progress.get("updated_at") or job.get("updated_at") or _run_report_end_time(run_report) or "未取得"
    steps = progress.get("steps") or _steps_from_run_report(run_report)
    employees = _employee_cards(steps, status)
    return {
        "status": status if status in {"running", "syncing", "completed", "failed"} else "idle",
        "current_step": current_step,
        "updated_at": updated_at,
        "employees": employees,
    }


def _employee_cards(steps, run_status: str):
    definitions = [
        ("P002 SNS事業部", "SNS", "SNS分析AI", "投稿素材とX結果を確認"),
        ("P003 グラビア事業部", "SEO", "グラビア事業部長AI", "WordPressとSEOを解析"),
        ("KPI Dashboard", "KPI", "KPI分析AI", "数字を集計"),
        ("P004 アダルト事業部", "AD", "アダルト事業部長AI", "対象記事を分析"),
        ("GPT Image Quality", "QC", "品質監査AI", "画像の本人感と破綻を確認"),
        ("P005 AI社長", "CEO", "AI社長", "経営判断を作成"),
        ("Google Drive保存", "DRV", "同期AI", "成果物を保存"),
    ]
    step_map = {item.get("name"): item.get("status") for item in steps if isinstance(item, dict)}
    if run_status == "syncing":
        step_map["Google Drive保存"] = "running"
    elif run_status == "completed":
        step_map.setdefault("Google Drive保存", "success")
    employees = []
    for step_name, code, name, role in definitions:
        status = step_map.get(step_name, "pending")
        if run_status == "idle" and status == "pending":
            label = "待機"
        else:
            label = {
                "running": "作業中",
                "success": "完了",
                "failed": "要確認",
                "pending": "待機",
            }.get(status, "待機")
        employees.append(
            {
                "code": code,
                "name": name,
                "role": role,
                "status": status,
                "label": label,
            }
        )
    return employees


def _steps_from_run_report(run_report: str):
    names = [
        "P002 SNS事業部",
        "P003 グラビア事業部",
        "KPI Dashboard",
        "P004 アダルト事業部",
        "GPT Image Quality",
        "P005 AI社長",
    ]
    success_section = _extract_section(run_report, "成功")
    failed_section = _extract_section(run_report, "失敗")
    steps = []
    for name in names:
        if name in failed_section:
            status = "failed"
        elif name in success_section:
            status = "success"
        else:
            status = "pending"
        steps.append({"name": name, "status": status})
    if "SUCCESS" in _extract_section(run_report, "Google Drive保存"):
        steps.append({"name": "Google Drive保存", "status": "success"})
    return steps


def _latest_run_current_step(run_report: str) -> str:
    if not run_report:
        return ""
    failed = _extract_section(run_report, "失敗")
    if failed and "なし" not in failed:
        return "要確認"
    if "## 終了時間" in run_report:
        return "完了"
    return ""


def _run_report_end_time(run_report: str) -> str:
    section = _extract_section(run_report, "終了時間")
    for line in section.splitlines():
        clean = line.strip()
        if clean:
            return clean
    return ""


def _pid_is_running(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _read_dashboard_json(path: Path):
    absolute = _absolute(path)
    if not absolute.exists():
        return {}
    try:
        return json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_dashboard_json(path: Path, payload) -> None:
    absolute = _absolute(path)
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _bounded_percent(value) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 0
    return max(8, min(100, number))


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
        .live-sync-pill {
          display: inline-flex;
          align-items: center;
          min-height: 32px;
          padding: 7px 11px;
          border-radius: 999px;
          color: #166534;
          background: #dcfce7;
          border: 1px solid #86efac;
          font-size: 0.78rem;
          font-weight: 950;
        }
        .live-sync-pill::before {
          content: "";
          width: 8px;
          height: 8px;
          margin-right: 8px;
          border-radius: 999px;
          background: #16a34a;
          animation: pulse 1.4s ease-in-out infinite;
        }
        .artifact-summary-card {
          min-height: 104px;
          margin-bottom: 10px;
          padding: 14px;
          border-radius: 12px;
          color: #ffffff;
          background: linear-gradient(135deg, #0f172a, #2563eb, #14b8a6);
          box-shadow: 0 12px 26px rgba(15, 23, 42, 0.14);
        }
        .artifact-summary-label {
          font-size: 0.75rem;
          font-weight: 900;
          opacity: 0.78;
        }
        .artifact-summary-value {
          margin-top: 12px;
          font-size: 1.45rem;
          font-weight: 950;
          line-height: 1;
        }
        .artifact-card {
          min-height: 158px;
          margin-bottom: 8px;
          padding: 13px;
          border-radius: 12px;
          border: 1px solid rgba(148, 163, 184, 0.28);
          background: #ffffff;
          box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .artifact-card.ready {
          border-left: 6px solid #2563eb;
          background: linear-gradient(180deg, #eff6ff, #ffffff);
        }
        .artifact-card.missing {
          border-left: 6px solid #dc2626;
          background: #fef2f2;
        }
        .artifact-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .artifact-head span {
          color: #475569;
          font-size: 0.72rem;
          font-weight: 900;
        }
        .artifact-head strong {
          padding: 4px 8px;
          border-radius: 999px;
          color: #1d4ed8;
          background: #dbeafe;
          font-size: 0.68rem;
          font-weight: 950;
        }
        .artifact-card.missing .artifact-head strong {
          color: #991b1b;
          background: #fee2e2;
        }
        .artifact-title {
          margin-top: 12px;
          color: #0f172a;
          font-size: 1rem;
          font-weight: 950;
        }
        .artifact-path {
          margin-top: 8px;
          color: #64748b;
          font-size: 0.72rem;
          font-weight: 780;
          overflow-wrap: anywhere;
        }
        .artifact-meta {
          margin-top: 10px;
          color: #475569;
          font-size: 0.72rem;
          font-weight: 800;
        }
        .momentum-board {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 10px;
          margin: 8px 0 18px;
        }
        .momentum-card {
          position: relative;
          overflow: hidden;
          min-height: 158px;
          padding: 15px;
          border-radius: 14px;
          color: #ffffff;
          box-shadow: 0 14px 30px rgba(15, 23, 42, 0.14);
          transition: transform 180ms ease, box-shadow 180ms ease;
        }
        .momentum-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 20px 42px rgba(15, 23, 42, 0.20);
        }
        .momentum-card.green { background: linear-gradient(135deg, #047857 0%, #16a34a 58%, #84cc16 100%); }
        .momentum-card.pink { background: linear-gradient(135deg, #be185d 0%, #db2777 56%, #fb7185 100%); }
        .momentum-card.blue { background: linear-gradient(135deg, #1d4ed8 0%, #0891b2 52%, #14b8a6 100%); }
        .momentum-card.ok { background: linear-gradient(135deg, #15803d 0%, #22c55e 54%, #a3e635 100%); }
        .momentum-card.warn { background: linear-gradient(135deg, #b45309 0%, #f59e0b 54%, #facc15 100%); }
        .momentum-card.bad, .momentum-card.red { background: linear-gradient(135deg, #991b1b 0%, #dc2626 56%, #f97316 100%); }
        .momentum-scan {
          position: absolute;
          inset: 0;
          background:
            linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.20) 28%, transparent 44%),
            repeating-linear-gradient(0deg, rgba(255,255,255,0.08) 0 1px, transparent 1px 8px);
          transform: translateX(-80%);
          animation: scan 4.8s ease-in-out infinite;
          pointer-events: none;
        }
        .momentum-top {
          position: relative;
          z-index: 1;
          display: flex;
          align-items: center;
          gap: 9px;
        }
        .momentum-icon {
          display: grid;
          place-items: center;
          width: 42px;
          height: 42px;
          border-radius: 12px;
          color: #0f172a;
          background: rgba(255, 255, 255, 0.88);
          font-size: 0.78rem;
          font-weight: 950;
        }
        .momentum-title {
          color: rgba(255,255,255,0.88);
          font-size: 0.78rem;
          font-weight: 900;
        }
        .momentum-value {
          position: relative;
          z-index: 1;
          margin-top: 18px;
          color: #ffffff;
          font-size: 1.55rem;
          font-weight: 950;
          line-height: 1;
        }
        .momentum-detail {
          position: relative;
          z-index: 1;
          margin-top: 9px;
          min-height: 34px;
          color: rgba(255,255,255,0.86);
          font-size: 0.76rem;
          font-weight: 800;
          line-height: 1.45;
        }
        .momentum-meter {
          position: relative;
          z-index: 1;
          height: 7px;
          margin-top: 13px;
          border-radius: 999px;
          background: rgba(255,255,255,0.28);
          overflow: hidden;
        }
        .momentum-meter span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: #ffffff;
          box-shadow: 0 0 16px rgba(255,255,255,0.75);
          animation: breathe 2.5s ease-in-out infinite;
        }
        .employee-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          margin: 6px 0 10px;
          padding: 14px 16px;
          border-radius: 14px;
          border: 1px solid rgba(148, 163, 184, 0.25);
          background: #ffffff;
          box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
        }
        .employee-banner.running {
          color: #ffffff;
          border-color: rgba(59, 130, 246, 0.28);
          background: linear-gradient(100deg, #1d4ed8, #0891b2, #16a34a);
          background-size: 220% 100%;
          animation: flow 3.2s linear infinite;
        }
        .employee-banner.success {
          color: #ffffff;
          background: linear-gradient(100deg, #047857, #16a34a);
        }
        .employee-banner.failed {
          color: #ffffff;
          background: linear-gradient(100deg, #991b1b, #dc2626, #f97316);
        }
        .employee-banner-label {
          font-size: 0.72rem;
          font-weight: 950;
          opacity: 0.82;
        }
        .employee-banner-title {
          margin-top: 3px;
          font-size: 1.28rem;
          font-weight: 950;
          line-height: 1;
        }
        .employee-banner-meta {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 8px;
        }
        .employee-banner-meta span {
          padding: 6px 9px;
          border-radius: 999px;
          background: rgba(255,255,255,0.22);
          color: inherit;
          font-size: 0.72rem;
          font-weight: 850;
        }
        .employee-banner.idle .employee-banner-meta span {
          background: #f1f5f9;
          color: #475569;
        }
        .employee-runway {
          position: relative;
          display: grid;
          grid-template-columns: repeat(7, minmax(0, 1fr));
          gap: 10px;
          margin: 8px 0 18px;
        }
        .employee-runway::before {
          content: "";
          position: absolute;
          left: 3%;
          right: 3%;
          top: 38px;
          height: 4px;
          border-radius: 999px;
          background: linear-gradient(90deg, #bfdbfe, #f9a8d4, #fde68a, #86efac);
          background-size: 220% 100%;
          animation: flow 2.8s linear infinite;
          opacity: 0.72;
        }
        .employee-card {
          position: relative;
          overflow: hidden;
          min-height: 150px;
          padding: 13px;
          border-radius: 14px;
          border: 1px solid rgba(148, 163, 184, 0.25);
          background: #ffffff;
          box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .employee-card.pending {
          opacity: 0.76;
          background: #f8fafc;
        }
        .employee-card.running {
          border-color: #60a5fa;
          background: linear-gradient(180deg, #eff6ff, #ffffff);
          animation: employeeLift 1.2s ease-in-out infinite;
        }
        .employee-card.success {
          border-color: #86efac;
          background: #f0fdf4;
        }
        .employee-card.failed {
          border-color: #fecaca;
          background: #fef2f2;
        }
        .employee-orbit {
          position: absolute;
          right: -34px;
          top: -34px;
          width: 92px;
          height: 92px;
          border-radius: 999px;
          border: 1px solid rgba(37, 99, 235, 0.18);
        }
        .employee-card.running .employee-orbit {
          animation: spin 3.4s linear infinite;
          border-color: rgba(37, 99, 235, 0.42);
        }
        .employee-orbit span {
          position: absolute;
          left: 10px;
          top: 16px;
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #2563eb;
        }
        .employee-avatar {
          position: relative;
          z-index: 1;
          display: grid;
          place-items: center;
          width: 46px;
          height: 46px;
          border-radius: 13px;
          color: #ffffff;
          background: #0f172a;
          font-size: 0.78rem;
          font-weight: 950;
        }
        .employee-card.running .employee-avatar { background: #2563eb; }
        .employee-card.success .employee-avatar { background: #16a34a; }
        .employee-card.failed .employee-avatar { background: #dc2626; }
        .employee-name {
          position: relative;
          z-index: 1;
          margin-top: 12px;
          color: #0f172a;
          font-size: 0.92rem;
          font-weight: 950;
          line-height: 1.25;
        }
        .employee-role {
          position: relative;
          z-index: 1;
          margin-top: 6px;
          min-height: 32px;
          color: #64748b;
          font-size: 0.72rem;
          font-weight: 800;
          line-height: 1.4;
        }
        .employee-state {
          position: relative;
          z-index: 1;
          display: inline-flex;
          margin-top: 9px;
          padding: 5px 8px;
          border-radius: 999px;
          color: #475569;
          background: #e2e8f0;
          font-size: 0.7rem;
          font-weight: 900;
        }
        .employee-card.running .employee-state {
          color: #1d4ed8;
          background: #dbeafe;
        }
        .employee-card.success .employee-state {
          color: #166534;
          background: #dcfce7;
        }
        .employee-card.failed .employee-state {
          color: #991b1b;
          background: #fee2e2;
        }
        .brief-factory {
          position: relative;
          overflow: hidden;
          margin: 8px 0 10px;
          padding: 15px;
          border-radius: 14px;
          border: 1px solid rgba(148, 163, 184, 0.25);
          background: linear-gradient(135deg, #f8fafc, #ffffff);
          box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
        }
        .brief-factory.running {
          color: #ffffff;
          background: linear-gradient(110deg, #312e81, #1d4ed8, #db2777);
          background-size: 240% 100%;
          animation: flow 3s linear infinite;
        }
        .brief-factory.completed {
          color: #ffffff;
          background: linear-gradient(110deg, #065f46, #16a34a, #14b8a6);
        }
        .brief-factory.failed {
          color: #ffffff;
          background: linear-gradient(110deg, #7f1d1d, #dc2626, #f97316);
        }
        .brief-factory-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .brief-kicker {
          font-size: 0.72rem;
          font-weight: 950;
          color: inherit;
          opacity: 0.75;
        }
        .brief-title {
          margin-top: 3px;
          font-size: 1.25rem;
          font-weight: 950;
          color: inherit;
        }
        .brief-current {
          padding: 7px 10px;
          border-radius: 999px;
          color: inherit;
          background: rgba(255,255,255,0.20);
          font-size: 0.74rem;
          font-weight: 900;
        }
        .brief-factory.idle .brief-current {
          color: #475569;
          background: #f1f5f9;
        }
        .brief-track {
          height: 8px;
          margin-top: 14px;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.28);
          overflow: hidden;
        }
        .brief-track span {
          display: block;
          width: 42%;
          height: 100%;
          border-radius: 999px;
          background: linear-gradient(90deg, #ffffff, #facc15, #ffffff);
          box-shadow: 0 0 18px rgba(255,255,255,0.75);
          animation: briefMove 2.1s ease-in-out infinite;
        }
        .brief-factory.idle .brief-track span {
          background: linear-gradient(90deg, #2563eb, #db2777);
          opacity: 0.55;
          animation: none;
        }
        .brief-card {
          position: relative;
          overflow: hidden;
          min-height: 156px;
          margin-bottom: 8px;
          padding: 13px;
          border-radius: 12px;
          border: 1px solid rgba(148, 163, 184, 0.28);
          background: #ffffff;
          box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
        }
        .brief-card.running {
          border-color: #93c5fd;
          background: linear-gradient(180deg, #eff6ff, #ffffff);
          animation: employeeLift 1.2s ease-in-out infinite;
        }
        .brief-card.ready {
          border-left: 6px solid #16a34a;
          background: #f0fdf4;
        }
        .brief-card.warn {
          border-left: 6px solid #f59e0b;
          background: #fffbeb;
        }
        .brief-card.failed, .brief-card.missing {
          border-left: 6px solid #dc2626;
          background: #fef2f2;
        }
        .brief-card-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
        }
        .brief-code {
          display: grid;
          place-items: center;
          width: 42px;
          height: 42px;
          border-radius: 11px;
          color: #ffffff;
          background: #0f172a;
          font-size: 0.78rem;
          font-weight: 950;
        }
        .brief-card.running .brief-code { background: #2563eb; }
        .brief-card.ready .brief-code { background: #16a34a; }
        .brief-card.warn .brief-code { background: #f59e0b; }
        .brief-card.failed .brief-code, .brief-card.missing .brief-code { background: #dc2626; }
        .brief-card-top span {
          padding: 4px 8px;
          border-radius: 999px;
          color: #475569;
          background: #e2e8f0;
          font-size: 0.7rem;
          font-weight: 900;
          white-space: nowrap;
        }
        .brief-card-title {
          margin-top: 12px;
          color: #0f172a;
          font-size: 1.02rem;
          font-weight: 950;
        }
        .brief-card-date {
          margin-top: 4px;
          color: #64748b;
          font-size: 0.72rem;
          font-weight: 800;
        }
        .brief-card-task {
          margin-top: 9px;
          color: #334155;
          font-size: 0.76rem;
          font-weight: 780;
          line-height: 1.45;
        }
        .brief-step {
          position: relative;
          min-height: 82px;
          margin: 3px 0 8px;
          padding: 12px;
          border-radius: 10px;
          border: 1px solid rgba(148, 163, 184, 0.25);
          background: #f8fafc;
        }
        .brief-step.running {
          border-color: #60a5fa;
          background: #eff6ff;
        }
        .brief-step.success {
          border-color: #86efac;
          background: #f0fdf4;
        }
        .brief-step.failed {
          border-color: #fecaca;
          background: #fef2f2;
        }
        .brief-step-dot {
          width: 11px;
          height: 11px;
          border-radius: 999px;
          background: #94a3b8;
        }
        .brief-step.running .brief-step-dot {
          background: #2563eb;
          animation: pulse 1.2s ease-in-out infinite;
        }
        .brief-step.success .brief-step-dot { background: #16a34a; }
        .brief-step.failed .brief-step-dot { background: #dc2626; }
        .brief-step-name {
          margin-top: 8px;
          color: #0f172a;
          font-size: 0.86rem;
          font-weight: 950;
        }
        .brief-step-owner {
          margin-top: 3px;
          color: #64748b;
          font-size: 0.72rem;
          font-weight: 800;
        }
        .visual-card-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 6px;
          padding: 9px 10px;
          border-radius: 10px 10px 0 0;
          color: #ffffff;
          background: linear-gradient(90deg, #0f172a, #db2777, #f59e0b);
          box-shadow: 0 8px 18px rgba(15, 23, 42, 0.10);
        }
        .visual-card-head span {
          font-size: 0.7rem;
          font-weight: 950;
          letter-spacing: 0.05em;
        }
        .visual-card-head strong {
          font-size: 0.78rem;
          font-weight: 950;
        }
        .visual-file-name {
          margin-top: -4px;
          margin-bottom: 8px;
          padding: 8px 10px;
          color: #475569;
          background: #ffffff;
          border: 1px solid rgba(148, 163, 184, 0.28);
          border-top: 0;
          border-radius: 0 0 10px 10px;
          font-size: 0.72rem;
          font-weight: 800;
          overflow-wrap: anywhere;
        }
        div[data-testid="stImage"] img {
          border-radius: 0;
          box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
        }
        .beauty-guard-card {
          position: relative;
          overflow: hidden;
          min-height: 132px;
          padding: 15px;
          border-radius: 12px;
          border: 1px solid rgba(49, 51, 63, 0.13);
          background: #ffffff;
          box-shadow: 0 2px 14px rgba(15, 23, 42, 0.07);
        }
        .beauty-guard-card::after {
          content: "";
          position: absolute;
          right: -36px;
          top: -36px;
          width: 96px;
          height: 96px;
          border-radius: 999px;
          opacity: 0.18;
          animation: pulse 2.4s ease-in-out infinite;
        }
        .beauty-guard-card.ok {
          border-left: 6px solid #16a34a;
          background: #f0fdf4;
        }
        .beauty-guard-card.ok::after { background: #16a34a; }
        .beauty-guard-card.warn {
          border-left: 6px solid #f59e0b;
          background: #fffbeb;
        }
        .beauty-guard-card.warn::after { background: #f59e0b; }
        .beauty-guard-card.bad {
          border-left: 6px solid #dc2626;
          background: #fef2f2;
        }
        .beauty-guard-card.bad::after { background: #dc2626; }
        .beauty-icon {
          display: inline-grid;
          place-items: center;
          width: 38px;
          height: 38px;
          border-radius: 10px;
          color: #ffffff;
          background: #0f172a;
          font-size: 0.82rem;
          font-weight: 950;
        }
        .beauty-guard-card.ok .beauty-icon { background: #16a34a; }
        .beauty-guard-card.warn .beauty-icon { background: #f59e0b; }
        .beauty-guard-card.bad .beauty-icon { background: #dc2626; }
        .beauty-label {
          margin-top: 10px;
          color: #475569;
          font-size: 0.76rem;
          font-weight: 900;
        }
        .beauty-value {
          margin-top: 4px;
          color: #0f172a;
          font-size: 1.28rem;
          font-weight: 950;
        }
        .beauty-detail {
          margin-top: 4px;
          color: #64748b;
          font-size: 0.76rem;
          font-weight: 750;
        }
        .guard-check {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          margin-bottom: 8px;
          padding: 11px;
          border-radius: 10px;
          background: #f8fafc;
          border: 1px solid rgba(148, 163, 184, 0.22);
        }
        .guard-check-mark {
          display: grid;
          place-items: center;
          flex: 0 0 26px;
          width: 26px;
          height: 26px;
          border-radius: 8px;
          background: #0f766e;
          color: #ffffff;
          font-size: 0.84rem;
          font-weight: 950;
        }
        .guard-check-title {
          color: #0f172a;
          font-size: 0.86rem;
          font-weight: 950;
        }
        .guard-check-detail {
          margin-top: 3px;
          color: #64748b;
          font-size: 0.74rem;
          line-height: 1.45;
        }
        .risk-item {
          margin-bottom: 8px;
          padding: 11px;
          border-radius: 10px;
          border: 1px solid #fecaca;
          border-left: 6px solid #dc2626;
          background: #fff7ed;
        }
        .risk-item-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }
        .risk-item-head strong {
          color: #0f172a;
          font-size: 0.86rem;
        }
        .risk-item-head span {
          display: inline-flex;
          padding: 3px 8px;
          border-radius: 999px;
          color: #991b1b;
          background: #fee2e2;
          font-size: 0.7rem;
          font-weight: 900;
          white-space: nowrap;
        }
        .risk-item-path {
          margin-top: 6px;
          color: #475569;
          font-size: 0.72rem;
          overflow-wrap: anywhere;
        }
        .risk-item-warning {
          margin-top: 6px;
          color: #7f1d1d;
          font-size: 0.74rem;
          line-height: 1.45;
        }
        .wardrobe-status {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          margin-bottom: 14px;
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(49, 51, 63, 0.13);
          background: #ffffff;
          box-shadow: 0 2px 14px rgba(15, 23, 42, 0.07);
        }
        .wardrobe-status.ok {
          border-left: 6px solid #0f766e;
          background: #f0fdfa;
        }
        .wardrobe-status.warn {
          border-left: 6px solid #f59e0b;
          background: #fffbeb;
        }
        .wardrobe-status-label {
          color: #64748b;
          font-size: 0.72rem;
          font-weight: 900;
        }
        .wardrobe-status-title {
          margin-top: 3px;
          color: #0f172a;
          font-size: 1rem;
          font-weight: 950;
        }
        .wardrobe-status-pill {
          display: inline-flex;
          padding: 6px 10px;
          border-radius: 999px;
          color: #0f172a;
          background: rgba(255, 255, 255, 0.72);
          font-size: 0.78rem;
          font-weight: 950;
          white-space: nowrap;
        }
        .wardrobe-card {
          margin-bottom: 9px;
          padding: 12px;
          border-radius: 10px;
          border: 1px solid rgba(49, 51, 63, 0.13);
          background: #ffffff;
        }
        .wardrobe-card.ok { border-left: 6px solid #0f766e; }
        .wardrobe-card.warn { border-left: 6px solid #f59e0b; background: #fffbeb; }
        .wardrobe-card-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
        }
        .wardrobe-card-head strong {
          color: #0f172a;
          font-size: 0.9rem;
        }
        .wardrobe-card-head span {
          display: inline-flex;
          padding: 4px 9px;
          border-radius: 999px;
          color: #134e4a;
          background: #ccfbf1;
          font-size: 0.72rem;
          font-weight: 950;
          white-space: nowrap;
        }
        .wardrobe-card.warn .wardrobe-card-head span {
          color: #92400e;
          background: #fef3c7;
        }
        .wardrobe-card-body {
          margin-top: 8px;
          color: #475569;
          font-size: 0.76rem;
          line-height: 1.48;
        }
        .wardrobe-next {
          margin-top: 10px;
          padding: 13px;
          border-radius: 10px;
          background: linear-gradient(135deg, #ecfeff, #f0fdf4);
          border: 1px solid rgba(14, 116, 144, 0.24);
        }
        .wardrobe-next-label {
          color: #0f766e;
          font-size: 0.72rem;
          font-weight: 950;
        }
        .wardrobe-next-title {
          margin-top: 3px;
          color: #0f172a;
          font-size: 1.08rem;
          font-weight: 950;
        }
        .wardrobe-next-reason {
          margin-top: 5px;
          color: #475569;
          font-size: 0.76rem;
          line-height: 1.45;
        }
        .x-input-guide {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          margin: 14px 0 18px;
          padding: 14px 16px;
          border-radius: 12px;
          border: 1px solid rgba(15, 23, 42, 0.12);
          border-left: 6px solid #0f172a;
          background: linear-gradient(135deg, #f8fafc, #eef2ff);
          box-shadow: 0 2px 14px rgba(15, 23, 42, 0.07);
        }
        .x-input-guide-label {
          color: #475569;
          font-size: 0.72rem;
          font-weight: 950;
        }
        .x-input-guide-title {
          margin-top: 3px;
          color: #0f172a;
          font-size: 1rem;
          font-weight: 950;
        }
        .x-input-guide-body {
          margin-top: 4px;
          color: #64748b;
          font-size: 0.78rem;
          font-weight: 750;
        }
        .x-input-guide-pill {
          display: inline-flex;
          padding: 7px 10px;
          border-radius: 999px;
          color: #ffffff;
          background: #0f172a;
          font-size: 0.76rem;
          font-weight: 950;
          white-space: nowrap;
        }
        .console-hero {
          position: relative;
          overflow: hidden;
          min-height: 230px;
          margin: 4px 0 16px;
          padding: 24px;
          border-radius: 16px;
          border: 1px solid rgba(37, 99, 235, 0.22);
          background:
            linear-gradient(120deg, rgba(255,255,255,0.62), transparent 28%, rgba(255,255,255,0.38) 58%, transparent 82%),
            linear-gradient(135deg, #fff7ed 0%, #eff6ff 34%, #fdf2f8 66%, #ecfdf5 100%);
          box-shadow: 0 14px 38px rgba(15, 23, 42, 0.10);
        }
        .console-hero::before {
          content: "";
          position: absolute;
          inset: 0;
          background:
            linear-gradient(rgba(15, 23, 42, 0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(15, 23, 42, 0.05) 1px, transparent 1px);
          background-size: 34px 34px;
          mask-image: linear-gradient(90deg, rgba(0,0,0,0.65), transparent 70%);
          animation: gridmove 9s linear infinite;
          pointer-events: none;
        }
        .hero-glow {
          position: absolute;
          border-radius: 999px;
          filter: blur(8px);
          opacity: 0.72;
          pointer-events: none;
        }
        .hero-glow.one {
          width: 220px;
          height: 220px;
          left: -80px;
          top: -80px;
          background: rgba(37, 99, 235, 0.16);
          animation: drift 9s ease-in-out infinite alternate;
        }
        .hero-glow.two {
          width: 260px;
          height: 260px;
          right: -100px;
          bottom: -120px;
          background: rgba(16, 185, 129, 0.14);
          animation: drift 11s ease-in-out infinite alternate-reverse;
        }
        .hero-content {
          position: relative;
          z-index: 1;
          max-width: 760px;
        }
        .hero-label {
          display: inline-flex;
          align-items: center;
          min-height: 30px;
          padding: 5px 11px;
          border-radius: 999px;
          background: rgba(37, 99, 235, 0.10);
          color: #1d4ed8;
          font-size: 0.78rem;
          font-weight: 950;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .hero-title {
          margin-top: 12px;
          color: #0f172a;
          font-size: clamp(2rem, 5vw, 4rem);
          line-height: 1;
          font-weight: 950;
        }
        .hero-subtitle {
          margin-top: 12px;
          color: #475569;
          font-size: 1rem;
          font-weight: 700;
        }
        .hero-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 18px;
        }
        .hero-pills span {
          display: inline-flex;
          gap: 6px;
          align-items: center;
          padding: 8px 10px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.78);
          border: 1px solid rgba(148, 163, 184, 0.26);
          color: #475569;
          font-size: 0.78rem;
          font-weight: 800;
        }
        .hero-pills b { color: #0f172a; }
        .hero-status {
          position: absolute;
          z-index: 1;
          right: 34px;
          top: 34px;
          display: grid;
          justify-items: center;
          gap: 8px;
        }
        .radar {
          position: relative;
          width: 112px;
          height: 112px;
          border-radius: 999px;
          display: grid;
          place-items: center;
          background: rgba(255, 255, 255, 0.70);
          border: 1px solid rgba(37, 99, 235, 0.18);
        }
        .radar span {
          position: absolute;
          inset: 14px;
          border-radius: 999px;
          border: 1px solid rgba(37, 99, 235, 0.32);
          animation: radar 2.8s ease-out infinite;
        }
        .radar span:nth-child(2) { animation-delay: 0.55s; }
        .radar span:nth-child(3) { animation-delay: 1.1s; }
        .radar strong {
          position: relative;
          z-index: 1;
          color: #1d4ed8;
          font-size: 1.6rem;
          font-weight: 950;
        }
        .hero-status-text {
          color: #166534;
          font-size: 0.74rem;
          font-weight: 950;
        }
        .nav-tile {
          position: relative;
          overflow: hidden;
          min-height: 104px;
          padding: 13px;
          border-radius: 12px;
          background: #ffffff;
          border: 1px solid rgba(49, 51, 63, 0.13);
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
          transition: transform 160ms ease, box-shadow 160ms ease;
        }
        .nav-tile:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 26px rgba(15, 23, 42, 0.10);
        }
        .nav-tile::after {
          content: "";
          position: absolute;
          width: 92px;
          height: 92px;
          right: -40px;
          top: -40px;
          border-radius: 999px;
          opacity: 0.24;
        }
        .nav-tile.graph::after { background: #2563eb; }
        .nav-tile.social::after { background: #db2777; }
        .nav-tile.x::after { background: #0f172a; }
        .nav-tile.seo::after { background: #16a34a; }
        .nav-tile.ceo::after { background: #9333ea; }
        .nav-tile.drive::after { background: #f59e0b; }
        .nav-icon {
          display: grid;
          place-items: center;
          width: 34px;
          height: 34px;
          border-radius: 9px;
          color: #ffffff;
          background: #0f172a;
          font-weight: 950;
        }
        .nav-tile.graph .nav-icon { background: #2563eb; }
        .nav-tile.social .nav-icon { background: #db2777; }
        .nav-tile.x .nav-icon { background: #0f172a; }
        .nav-tile.seo .nav-icon { background: #16a34a; }
        .nav-tile.ceo .nav-icon { background: #9333ea; }
        .nav-tile.drive .nav-icon { background: #f59e0b; }
        .nav-title {
          margin-top: 9px;
          color: #0f172a;
          font-size: 0.98rem;
          font-weight: 950;
        }
        .nav-body {
          color: #64748b;
          font-size: 0.76rem;
          font-weight: 800;
        }
        .mobile-command {
          position: relative;
          overflow: hidden;
          padding: 18px;
          margin: 10px 0 18px;
          border-radius: 12px;
          border: 1px solid #bfdbfe;
          background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 58%, #ecfdf5 100%);
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
        }
        .mobile-command::after {
          content: "";
          position: absolute;
          inset: -40% auto auto -20%;
          width: 220px;
          height: 220px;
          border-radius: 999px;
          background: rgba(37, 99, 235, 0.12);
          animation: drift 8s ease-in-out infinite alternate;
        }
        .mobile-command-head {
          position: relative;
          z-index: 1;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .mobile-kicker {
          color: #2563eb;
          font-size: 0.72rem;
          font-weight: 900;
        }
        .mobile-title {
          color: #0f172a;
          font-size: 1.55rem;
          font-weight: 950;
          line-height: 1.1;
        }
        .live-pill {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 6px 10px;
          border-radius: 999px;
          background: #dcfce7;
          color: #166534;
          font-size: 0.74rem;
          font-weight: 900;
          white-space: nowrap;
        }
        .live-pill span {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: #16a34a;
          animation: pulse 1.4s ease-in-out infinite;
        }
        .mobile-grid {
          position: relative;
          z-index: 1;
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-top: 16px;
        }
        .mobile-grid div {
          min-height: 72px;
          padding: 10px;
          border-radius: 10px;
          background: rgba(255, 255, 255, 0.82);
          border: 1px solid rgba(148, 163, 184, 0.25);
        }
        .mobile-grid strong {
          display: block;
          color: #0f172a;
          font-size: 1.25rem;
          font-weight: 950;
        }
        .mobile-grid span {
          color: #64748b;
          font-size: 0.75rem;
          font-weight: 800;
        }
        .hub-card, .department-card {
          position: relative;
          overflow: hidden;
          min-height: 124px;
          padding: 14px;
          border-radius: 10px;
          border: 1px solid rgba(49, 51, 63, 0.14);
          background: #ffffff;
          box-shadow: 0 1px 10px rgba(0,0,0,0.06);
        }
        .hub-card.ok, .department-card.ok { border-left: 6px solid #16a34a; }
        .hub-card.warn, .department-card.warn { border-left: 6px solid #f59e0b; background: #fffbeb; }
        .hub-card.bad, .department-card.bad { border-left: 6px solid #dc2626; background: #fef2f2; }
        .hub-card-pulse {
          position: absolute;
          right: 12px;
          top: 12px;
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #16a34a;
          animation: pulse 1.8s ease-in-out infinite;
        }
        .hub-card.warn .hub-card-pulse { background: #f59e0b; }
        .hub-card.bad .hub-card-pulse { background: #dc2626; }
        .hub-label, .department-focus { color: #64748b; font-size: 0.74rem; font-weight: 800; }
        .hub-value, .department-name { color: #0f172a; font-size: 1.22rem; font-weight: 950; margin-top: 8px; }
        .hub-detail, .department-status { color: #475569; font-size: 0.78rem; margin-top: 6px; }
        .department-icon { font-size: 1.1rem; }
        .flow-lane {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 8px;
          margin: 8px 0 18px;
        }
        .flow-step {
          position: relative;
          min-height: 86px;
          padding: 13px;
          border-radius: 10px;
          border: 1px solid #cbd5e1;
          background: #f8fafc;
        }
        .flow-step::before {
          content: "";
          position: absolute;
          left: 0;
          bottom: 0;
          height: 4px;
          width: 100%;
          background: #cbd5e1;
        }
        .flow-step.done::before { background: #16a34a; }
        .flow-step.active::before {
          background: linear-gradient(90deg, #2563eb, #16a34a, #2563eb);
          background-size: 200% 100%;
          animation: flow 2.4s linear infinite;
        }
        .flow-dot {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #94a3b8;
        }
        .flow-step.done .flow-dot { background: #16a34a; }
        .flow-step.active .flow-dot {
          background: #2563eb;
          animation: pulse 1.3s ease-in-out infinite;
        }
        .flow-label { margin-top: 10px; color: #64748b; font-size: 0.72rem; font-weight: 900; }
        .flow-title { margin-top: 3px; color: #0f172a; font-size: 0.9rem; font-weight: 900; }
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.35); opacity: 0.55; }
        }
        @keyframes flow {
          from { background-position: 0 0; }
          to { background-position: 200% 0; }
        }
        @keyframes drift {
          from { transform: translate(0, 0); }
          to { transform: translate(80px, 40px); }
        }
        @keyframes radar {
          0% { transform: scale(0.52); opacity: 0.85; }
          100% { transform: scale(1.55); opacity: 0; }
        }
        @keyframes scan {
          0%, 42% { transform: translateX(-90%); opacity: 0; }
          52% { opacity: 1; }
          100% { transform: translateX(90%); opacity: 0; }
        }
        @keyframes breathe {
          0%, 100% { opacity: 0.72; }
          50% { opacity: 1; }
        }
        @keyframes gridmove {
          from { background-position: 0 0; }
          to { background-position: 68px 34px; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes employeeLift {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
        @keyframes briefMove {
          0% { transform: translateX(-110%); }
          100% { transform: translateX(250%); }
        }
        @media (max-width: 760px) {
          .block-container { padding-left: 0.8rem; padding-right: 0.8rem; padding-top: 0.9rem; }
          h1 { font-size: 1.55rem !important; }
          h2 { font-size: 1.12rem !important; margin-top: 1.1rem !important; }
          div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap;
            gap: 0.55rem;
          }
          div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
          }
          div[data-testid="stSidebar"] {
            width: min(92vw, 24rem) !important;
          }
          .status-card, .kpi-card, .task-card, .improvement-card, .hub-card, .department-card, .beauty-guard-card, .wardrobe-status, .wardrobe-card, .x-input-guide {
            min-height: auto;
            padding: 12px;
            border-radius: 8px;
          }
          .x-input-guide {
            display: block;
          }
          .x-input-guide-pill {
            margin-top: 9px;
          }
          .mobile-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          .momentum-board {
            grid-template-columns: 1fr;
          }
          .momentum-card {
            min-height: 132px;
          }
          .employee-banner {
            display: block;
          }
          .employee-banner-meta {
            justify-content: flex-start;
            margin-top: 10px;
          }
          .employee-runway {
            grid-template-columns: 1fr;
          }
          .employee-runway::before {
            display: none;
          }
          .brief-factory-head {
            display: block;
          }
          .brief-current {
            display: inline-flex;
            margin-top: 10px;
          }
          .flow-lane {
            grid-template-columns: 1fr;
          }
          .flow-step {
            min-height: 72px;
          }
          .kpi-row strong, .hub-value {
            font-size: 1rem;
          }
          .mobile-title {
            font-size: 1.28rem;
          }
          .console-hero {
            min-height: 240px;
            padding: 18px;
            border-radius: 12px;
          }
          .hero-title {
            font-size: 2.1rem;
          }
          .hero-status {
            right: 14px;
            top: 14px;
            transform: scale(0.72);
            transform-origin: top right;
          }
          .hero-pills span {
            width: 100%;
            justify-content: space-between;
          }
          .nav-tile {
            min-height: 88px;
          }
          .state-badge {
            white-space: normal;
            text-align: center;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

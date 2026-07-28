from datetime import date
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = (
    WORKSPACE_ROOT / "01_グラビア事業部" / "P003_グラビア事業部" / "REPORT.md"
)
TITLE_RESULT_PATH = (
    WORKSPACE_ROOT
    / "01_グラビア事業部"
    / "P003_グラビア事業部"
    / "TITLE_IMPROVEMENT_RESULT.md"
)
OUTPUT_PATH = WORKSPACE_ROOT / "04_グラビア事業部" / "DAILY_BRIEF.md"


def main() -> int:
    report = _read_report()
    title_result = _read_text(TITLE_RESULT_PATH)
    content = build_daily_brief(report, title_result)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"DAILY_BRIEF saved: {OUTPUT_PATH}")
    return 0


def build_daily_brief(report: str, title_result: str = "") -> str:
    article_count = _extract_bullet_value(report, "記事一覧取得") or "未取得"
    uncategorized_count = _extract_category_count(report, "Uncategorized") or "0件"
    gravure_count = _extract_category_count(report, "グラビア") or "未取得"
    top_tag_count = _extract_tag_count(report, "菊地姫奈") or "未取得"
    category_done = _count_to_int(uncategorized_count) == 0
    title_done = "更新成功: 9件" in title_result and "更新失敗: 0件" in title_result
    priority_title = (
        "カテゴリ・タイトル改善後の効果測定を開始する"
        if category_done and title_done
        else "カテゴリ改善後の効果測定を開始する"
        if category_done
        else "Uncategorized記事の整理案を作る"
    )
    priority_reason = (
        f"カテゴリ改善によりUncategorizedが{uncategorized_count}、タイトル改善によりGO対象9件の検索表示文言を整理済みのため。"
        if category_done and title_done
        else
        f"カテゴリ改善によりUncategorizedが{uncategorized_count}、グラビアが{gravure_count}になったため。"
        if category_done
        else "カテゴリ未整理の記事が残っており、SEO・内部リンク・回遊率改善の判断材料になるため。"
    )
    top1_title = (
        "カテゴリ・タイトル改善後の効果測定を開始する"
        if category_done and title_done
        else "カテゴリ改善後の効果測定を開始する"
        if category_done
        else "Uncategorized記事のカテゴリ整理案を作る"
    )
    top1_reason = (
        f"取得記事{article_count}中、Uncategorizedが{uncategorized_count}、グラビアが{gravure_count}。さらにGO対象9件のタイトル改善が完了し、CTR変化を追跡できるため。"
        if category_done and title_done
        else
        f"取得記事{article_count}中、Uncategorizedが{uncategorized_count}、グラビアが{gravure_count}になり、カテゴリ整理後の状態確認へ進めるため。"
        if category_done
        else f"取得記事{article_count}中、Uncategorizedが{uncategorized_count}あり、カテゴリ傾向が弱くなっているため。"
    )
    top1_effect = (
        "Search Console / GA4でカテゴリ整理とタイトル改善後のCTR・PV変化を追跡し、次の内部リンク改善判断につなげる。"
        if category_done and title_done
        else
        "カテゴリ整理後のSearch Console / GA4変化を追跡し、次の改善判断につなげる。"
        if category_done
        else "記事分類が明確になり、SEO評価、内部リンク設計、読者回遊の改善候補を判断しやすくなる。"
    )

    return f"""# Executive Summary

本日の最優先は
「{priority_title}」です。

理由
{priority_reason}

# Daily Brief

日付

{date.today().isoformat()}

## 今日やること TOP3

① {top1_title}

理由

{top1_reason}

期待効果

{top1_effect}

作業時間

30分

----------------

② 菊地姫奈関連記事の内部リンク改善案を作る

理由

菊地姫奈タグの記事が{top_tag_count}あり、関連性の高い内部リンク候補が検出されているため。

期待効果

同一人物の記事間回遊を強化し、PV、回遊率、写真集導線CTRの改善につなげる。

作業時間

30分

----------------

③ メタディスクリプション改善案の準備をする

理由

カテゴリ改善とタイトル改善が完了したため、次のCTR改善施策をメタディスクリプションへ広げられるため。

期待効果

検索結果上のクリック判断材料を増やし、タイトル改善との相乗効果を狙える。

作業時間

45分

----------------

## Blocker

止まっていること

{_extract_section(report, "Blocker") or "なし。"}

## 明日の候補

・TASK-005 SEO改善提案を作成する。

・Search Console / GA4の未取得項目を確認する。

・内部リンク追加のGO対象を実行する。

## Rules

GO承認済み対象以外のWordPress更新は禁止。

投稿は禁止。

更新を行う場合は結果ファイルへ記録する。
"""


def _read_report() -> str:
    return _read_text(REPORT_PATH)


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_bullet_value(text: str, label: str) -> str:
    prefix = f"- {label}:"
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith(prefix):
            return clean.replace(prefix, "", 1).strip()
    return ""


def _extract_category_count(text: str, category: str) -> str:
    return _extract_named_count(text, "カテゴリ傾向", category)


def _extract_tag_count(text: str, tag: str) -> str:
    return _extract_named_count(text, "タグ傾向", tag)


def _extract_named_count(text: str, heading: str, name: str) -> str:
    section = _extract_section(text, heading)
    prefix = f"- {name}:"
    for line in section.splitlines():
        clean = line.strip()
        if clean.startswith(prefix):
            return clean.replace(prefix, "", 1).strip()
    return ""


def _count_to_int(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return -1
    return int(digits)


def _extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    capture = False
    captured = []
    target = f"## {heading}"
    for line in lines:
        if line.strip() == target:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


if __name__ == "__main__":
    raise SystemExit(main())

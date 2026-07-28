from datetime import date
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_DIR / "REPORT.md"
OUTPUT_PATH = PROJECT_DIR / "DAILY_BRIEF.md"


def main() -> int:
    report = _read_text(REPORT_PATH)
    content = build_daily_brief(report)
    OUTPUT_PATH.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"P004 DAILY_BRIEF saved: {OUTPUT_PATH}")
    return 0


def build_daily_brief(report: str) -> str:
    candidate_count = _extract_bullet_value(report, "アダルト候補記事数") or "未取得"
    blocker = _extract_section(report, "Blocker") or "- なし。"
    no_candidates = candidate_count.startswith("0")

    top1 = (
        "アダルト専用カテゴリ・タグ設計を確定する"
        if no_candidates
        else "アダルト候補記事のSEO改善案を作る"
    )
    reason1 = (
        "現状では対象記事を安定判定できるカテゴリ・タグが不足しているため。"
        if no_candidates
        else f"アダルト候補記事が{candidate_count}あり、既存記事改善に進めるため。"
    )
    effect1 = (
        "分析対象を明確化し、SEO / CTR / 回遊改善の起点を作れる。"
        if no_candidates
        else "検索CTRと回遊率改善の優先順位を判断できる。"
    )

    return f"""# Daily Brief

日付

{date.today().isoformat()}

## 今日やること TOP3

① {top1}

理由

{reason1}

期待効果

{effect1}

作業時間

30分

----------------

② アダルト領域のSearch Console / GA4取得条件を確認する

理由

SEO流入、CTR、PV、回遊率を実データで判断する必要があるため。

期待効果

改善対象ページと優先順位を推測なしで決められる。

作業時間

30分

----------------

③ アダルト事業部の改善バックログを作る

理由

カテゴリ、タイトル、メタディスクリプション、内部リンク、CTAを継続管理するため。

期待効果

編集長が毎朝5分以内でGO / STOP判断できる。

作業時間

30分

----------------

## Blocker

止まっていること

{blocker}

## 明日の候補

・アダルト対象記事の抽出条件を確定する。

・対象記事のタイトル改善案を作る。

・内部リンク改善候補を作る。

## Rules

WordPress更新は禁止。

投稿は禁止。

解析のみ。
"""


def _extract_bullet_value(text: str, label: str) -> str:
    prefix = f"- {label}:"
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith(prefix):
            return clean.replace(prefix, "", 1).strip()
    return ""


def _extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    capture = False
    captured = []
    for line in lines:
        if line.strip() == f"## {heading}":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    return "\n".join(captured).strip()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())

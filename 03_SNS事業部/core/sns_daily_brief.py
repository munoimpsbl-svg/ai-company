from datetime import date
from pathlib import Path
from typing import Optional


def build_sns_daily_brief(
    sns_report: str,
    output_date: Optional[date] = None,
) -> str:
    current_date = output_date or date.today()
    blocker = _extract_section(sns_report, "Blocker") or "未取得"
    tomorrow = _extract_section(sns_report, "明日の改善候補") or "未取得"

    return f"""# Daily Brief

日付

{current_date.isoformat()}

## 今日やることTOP3

### Priority 1

採用候補の最終判断を行う

優先順位

1

理由

SNS_REPORTで採用画像数が13枚あり、投稿前に採用候補の絞り込みが必要なため。

期待ROI

投稿品質を安定させ、SNS投稿前の判断時間を短縮できる。

### Priority 2

投稿先ごとの文面差分を確認する

優先順位

2

理由

Instagram、X、Threadsで投稿文が分かれており、媒体ごとの文体確認が必要なため。

期待ROI

各SNSの読者に合わせた投稿品質を維持できる。

### Priority 3

SNS実投稿データ接続の準備をする

優先順位

3

理由

現在は投稿文と生成結果の解析のみで、実投稿後の反応率は未接続のため。

期待ROI

次回以降、03_Analyticsへ反応率を保存し、改善判断の精度を上げられる。

## Blocker

{blocker}

## 明日の予定

{tomorrow}

## 制約確認

- 分析のみ
- SNS投稿禁止
- 画像生成禁止
"""


def generate_sns_daily_brief(project_root: Path) -> Path:
    sns_report_path = project_root / "SNS_REPORT.md"
    output_path = project_root / "04_Daily" / "DAILY_BRIEF.md"

    if not sns_report_path.exists():
        content = _build_missing_report_brief()
    else:
        content = build_sns_daily_brief(sns_report_path.read_text(encoding="utf-8"))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return output_path


def _extract_section(content: str, heading: str) -> str:
    lines = content.splitlines()
    captured = []
    capture = False
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


def _build_missing_report_brief() -> str:
    return f"""# Daily Brief

日付

{date.today().isoformat()}

## 今日やることTOP3

### Priority 1

SNS_REPORT.mdを生成する

優先順位

1

理由

SNS_REPORT.mdが未取得のため。

期待ROI

Daily Brief生成の入力を確保できる。

### Priority 2

未取得

優先順位

2

理由

未取得

期待ROI

未取得

### Priority 3

未取得

優先順位

3

理由

未取得

期待ROI

未取得

## Blocker

SNS_REPORT.md未取得

## 明日の予定

・SNS_REPORT.mdを生成する。

## 制約確認

- 分析のみ
- SNS投稿禁止
- 画像生成禁止
"""

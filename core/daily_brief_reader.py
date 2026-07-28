from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional


DAILY_BRIEF_FILENAME = "DAILY_BRIEF.md"
IGNORED_DIRS = {
    ".git",
    ".secrets",
    ".venv",
    "__pycache__",
    ".pycache",
    "output",
}


@dataclass(frozen=True)
class DailyBrief:
    department: str
    path: Path
    content: str


def read_daily_briefs(workspace_root: Path) -> List[DailyBrief]:
    root = workspace_root.expanduser().resolve()
    briefs = []
    for path in sorted(root.rglob(DAILY_BRIEF_FILENAME)):
        relative_path = path.relative_to(root)
        if _is_ignored_path(relative_path):
            continue

        briefs.append(
            DailyBrief(
                department=_department_from_path(relative_path),
                path=path,
                content=path.read_text(encoding="utf-8"),
            )
        )

    return briefs


def build_ceo_daily_brief_report(
    briefs: Iterable[DailyBrief],
    workspace_root: Path,
    report_date: Optional[date] = None,
) -> str:
    current_date = report_date or date.today()
    brief_list = list(briefs)
    summaries = [_format_brief_summary(brief, workspace_root) for brief in brief_list]
    blockers = [_extract_section(brief.content, "Blocker") for brief in brief_list]
    blocker_lines = [
        f"- {brief.department}: {blocker.strip()}"
        for brief, blocker in zip(brief_list, blockers)
        if blocker.strip()
    ]

    return f"""# P005 AI社長 Daily Brief Reader REPORT

## 実行日

{current_date.isoformat()}

## Executive Summary

Daily Brief Readerを実行し、AI COMPANY内の`DAILY_BRIEF.md`を読み取った。

- 読み取り件数: {len(brief_list)}件
- 読み取り専用: OK
- WordPress更新: 未実行
- 投稿: 未実行

## 読み取り結果

{chr(10).join(summaries) if summaries else "未取得。"}

## Blocker一覧

{chr(10).join(blocker_lines) if blocker_lines else "- なし。"}

## CEO判断メモ

- 各Daily Briefを読み、当日の優先作業を確認する。
- 実行や更新は行わず、必要な判断と優先順位付けのみ行う。
- 次Taskでは複数部署のDaily BriefをCEOレポートへ統合する。
"""


def _format_brief_summary(brief: DailyBrief, workspace_root: Path) -> str:
    relative_path = brief.path.relative_to(workspace_root)
    top3 = _extract_section(brief.content, "今日やること TOP3")
    blocker = _extract_section(brief.content, "Blocker")
    tomorrow = _extract_section(brief.content, "明日の候補")

    return f"""### {brief.department}

- Path: {relative_path}
- 今日やること TOP3:
{_indent(top3 or "未取得。")}
- Blocker:
{_indent(blocker or "未取得。")}
- 明日の候補:
{_indent(tomorrow or "未取得。")}
"""


def _extract_section(content: str, heading: str) -> str:
    lines = content.splitlines()
    capture = False
    captured = []
    target = f"## {heading}".strip()

    for line in lines:
        if line.strip() == target:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)

    return "\n".join(captured).strip()


def _department_from_path(path: Path) -> str:
    if len(path.parts) >= 2:
        return path.parts[0]
    return "未分類"


def _indent(text: str) -> str:
    return "\n".join(f"  {line}" if line else "" for line in text.splitlines())


def _is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIRS or part.startswith(".") for part in path.parts)

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


EXPECTED_DEPARTMENTS = (
    ("P002 SNS事業部", Path("03_SNS事業部") / "04_Daily" / "DAILY_BRIEF.md"),
    ("P003 グラビア事業部", Path("04_グラビア事業部") / "DAILY_BRIEF.md"),
    ("P004 アダルト事業部", Path("04_アダルト事業部") / "DAILY_BRIEF.md"),
)


@dataclass(frozen=True)
class DepartmentBrief:
    department: str
    path: Path
    status: str
    content: str
    error: Optional[str] = None


@dataclass(frozen=True)
class PriorityItem:
    department: str
    title: str
    reason: str
    expected_roi: str
    work_time: str
    approval: str


@dataclass(frozen=True)
class KpiDashboard:
    path: Path
    status: str
    sources: Dict[str, Dict[str, str]]
    error: Optional[str] = None


def read_department_briefs(workspace_root: Path) -> List[DepartmentBrief]:
    briefs = []
    for department, relative_path in EXPECTED_DEPARTMENTS:
        path = workspace_root / relative_path
        if not path.exists():
            briefs.append(
                DepartmentBrief(
                    department=department,
                    path=relative_path,
                    status="未提出",
                    content="",
                    error="DAILY_BRIEF.md が存在しません。",
                )
            )
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            briefs.append(
                DepartmentBrief(
                    department=department,
                    path=relative_path,
                    status="読取失敗",
                    content="",
                    error=str(exc),
                )
            )
            continue

        briefs.append(
            DepartmentBrief(
                department=department,
                path=relative_path,
                status="提出済み",
                content=content,
            )
        )

    return briefs


def read_kpi_dashboard(workspace_root: Path) -> KpiDashboard:
    relative_path = Path("KPI_DASHBOARD.md")
    path = workspace_root / relative_path
    if not path.exists():
        return KpiDashboard(
            path=relative_path,
            status="未取得",
            sources={},
            error="KPI_DASHBOARD.md が存在しません。",
        )

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return KpiDashboard(
            path=relative_path,
            status="未取得",
            sources={},
            error=str(exc),
        )

    sources = _parse_source_kpi_table(content)
    return KpiDashboard(
        path=relative_path,
        status="取得済み" if sources else "未取得",
        sources=sources,
        error=None if sources else "Source KPI表を取得できません。",
    )


def build_ceo_report(
    briefs: List[DepartmentBrief],
    kpi_dashboard: Optional[KpiDashboard] = None,
    output_date: Optional[date] = None,
) -> str:
    current_date = output_date or date.today()
    priorities = _collect_priorities(briefs)
    blocker = _build_blocker(briefs)
    decisions = _build_management_decisions(briefs)
    tomorrow = _build_tomorrow_plan(briefs)

    return f"""# CEO REPORT

日付

{current_date.isoformat()}

---

## 本日の総評

{_build_overall_summary(briefs)}

---

## WordPress KPI

{_format_kpi_group(kpi_dashboard, "wordpress", ("posts", "published", "categories", "tags"))}

---

## Search Console KPI

{_format_kpi_group(kpi_dashboard, "search_console", ("clicks", "impressions", "ctr", "position"))}

---

## GA4 KPI

{_format_kpi_group(kpi_dashboard, "ga4", ("users", "sessions", "page_views", "engagement_time"))}

---

## Priority 1

{_format_priority(_priority_at(priorities, 0))}

---

## Priority 2

{_format_priority(_priority_at(priorities, 1))}

---

## Priority 3

{_format_priority(_priority_at(priorities, 2))}

---

## Blocker

{blocker}

---

## 本日の経営判断

新規記事作成

{decisions["新規記事作成"]}

既存記事改善

{decisions["既存記事改善"]}

CTR改善

{decisions["CTR改善"]}

SEO改善

{decisions["SEO改善"]}

---

## 明日の予定

{tomorrow}

---

## CTOコメント

AI社長は分析を行わず、各部署のDAILY_BRIEF.mdを要約し、経営判断のみを出力した。

WordPress更新、WordPress投稿、WordPress削除、SNS投稿、Google Drive変更、Google Drive削除、REPORT.md書き換え、DAILY_BRIEF.md書き換えは未実行。
"""


def save_ceo_report(
    workspace_root: Path,
    content: str,
    output_date: Optional[date] = None,
) -> Path:
    current_date = output_date or date.today()
    output_dir = workspace_root / "02_Daily_Output" / current_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "CEO_REPORT.md"
    output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return output_path


def _collect_priorities(briefs: List[DepartmentBrief]) -> List[PriorityItem]:
    department_items = []
    for brief in briefs:
        if brief.status != "提出済み":
            continue
        section = _extract_section(brief.content, "今日やること TOP3")
        items = []
        for block in _split_priority_blocks(section):
            items.append(
                PriorityItem(
                    department=brief.department,
                    title=_first_nonempty_line(block) or "未取得",
                    reason=_extract_label_value(block, "理由"),
                    expected_roi=(
                        _extract_label_value(block, "期待ROI")
                        if _extract_label_value(block, "期待ROI") != "未取得"
                        else _extract_label_value(block, "期待効果")
                    ),
                    work_time=_extract_label_value(block, "作業時間"),
                    approval="GO",
                )
            )
        if items:
            department_items.append(items)

    balanced = []
    max_length = max((len(items) for items in department_items), default=0)
    for index in range(max_length):
        for items in department_items:
            if index < len(items):
                balanced.append(items[index])
            if len(balanced) >= 3:
                return balanced
    return balanced[:3]


def _priority_at(priorities: List[PriorityItem], index: int) -> Optional[PriorityItem]:
    if index < len(priorities):
        return priorities[index]
    return None


def _format_priority(priority: Optional[PriorityItem]) -> str:
    if not priority:
        return """担当

未提出

理由

未提出

期待ROI

未提出

作業時間

未提出

承認（GO / STOP）

STOP"""

    return f"""担当

{priority.department}

タスク

{priority.title}

理由

{priority.reason}

期待ROI

{priority.expected_roi}

作業時間

{priority.work_time}

承認（GO / STOP）

{priority.approval}"""


def _build_overall_summary(briefs: List[DepartmentBrief]) -> str:
    submitted = [brief.department for brief in briefs if brief.status == "提出済み"]
    missing = [brief.department for brief in briefs if brief.status != "提出済み"]

    lines = [
        f"- 提出済み: {', '.join(submitted) if submitted else 'なし'}",
        f"- 未提出: {', '.join(missing) if missing else 'なし'}",
        "- 推測なし。提出済みDaily Briefのみを判断材料にする。",
    ]
    return "\n".join(lines)


def _format_kpi_group(
    kpi_dashboard: Optional[KpiDashboard], source: str, keys: tuple
) -> str:
    if not kpi_dashboard or kpi_dashboard.status != "取得済み":
        return "\n".join(f"- {key}: 未取得" for key in keys)

    source_values = kpi_dashboard.sources.get(source)
    if not source_values:
        return "\n".join(f"- {key}: 未取得" for key in keys)

    lines = []
    for key in keys:
        value = source_values.get(key)
        lines.append(f"- {key}: {value if value not in (None, '') else '未取得'}")
    return "\n".join(lines)


def _build_blocker(briefs: List[DepartmentBrief]) -> str:
    lines = []
    for brief in briefs:
        if brief.status != "提出済み":
            lines.append(f"- {brief.department}: 未提出")
            continue
        blocker = _extract_section(brief.content, "Blocker")
        lines.append(f"- {brief.department}: {blocker or '未取得'}")
    return "\n".join(lines)


def _build_tomorrow_plan(briefs: List[DepartmentBrief]) -> str:
    lines = []
    for brief in briefs:
        if brief.status != "提出済み":
            lines.append(f"- {brief.department}: 未提出")
            continue
        tomorrow = _extract_section(brief.content, "明日の予定")
        if not tomorrow:
            tomorrow = _extract_section(brief.content, "明日の候補")
        lines.append(f"- {brief.department}: {tomorrow or '未取得'}")
    return "\n".join(lines)


def _build_management_decisions(briefs: List[DepartmentBrief]) -> Dict[str, str]:
    submitted_text = "\n".join(
        brief.content for brief in briefs if brief.status == "提出済み"
    )
    return {
        "新規記事作成": _decision_from_keywords(submitted_text, ("新規記事",)),
        "既存記事改善": _decision_from_keywords(
            submitted_text, ("既存記事", "記事改善", "カテゴリ整理")
        ),
        "CTR改善": _decision_from_keywords(submitted_text, ("CTR",)),
        "SEO改善": _decision_from_keywords(submitted_text, ("SEO",)),
    }


def _decision_from_keywords(text: str, keywords: tuple) -> str:
    if not text:
        return "STOP"
    return "GO" if any(keyword in text for keyword in keywords) else "STOP"


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


def _split_priority_blocks(section: str) -> List[str]:
    if not section:
        return []
    if "### Priority" in section:
        blocks = []
        current = []
        for line in section.splitlines():
            if line.startswith("### Priority") and current:
                blocks.append("\n".join(current).strip())
                current = []
            current.append(line)
        if current:
            blocks.append("\n".join(current).strip())
        return [block for block in blocks if block]
    blocks = [block.strip() for block in section.split("----------------")]
    return [block for block in blocks if block]


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean.startswith("### Priority"):
            continue
        if clean:
            return clean
    return ""


def _extract_label_value(text: str, label: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != label:
            continue
        for value_line in lines[index + 1 :]:
            clean = value_line.strip()
            if not clean:
                continue
            if clean in ("理由", "期待ROI", "期待効果", "作業時間"):
                return "未取得"
            return clean
    return "未取得"


def _normalize_heading(line: str) -> str:
    return line.strip().replace(" ", "").replace("　", "")


def _parse_source_kpi_table(content: str) -> Dict[str, Dict[str, str]]:
    lines = content.splitlines()
    sources: Dict[str, Dict[str, str]] = {}
    in_source_section = False
    headers = []

    for line in lines:
        clean = line.strip()
        if clean == "## Source KPI":
            in_source_section = True
            continue
        if in_source_section and clean.startswith("## "):
            break
        if not in_source_section or not clean.startswith("|"):
            continue

        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or cells[0] == "---" or set(cells[0]) == {"-"}:
            continue
        if cells[0] == "source":
            headers = cells
            continue
        if not headers or len(cells) != len(headers):
            continue

        source_name = cells[0]
        sources[source_name] = {
            headers[index]: cells[index] for index in range(1, len(headers))
        }

    return sources

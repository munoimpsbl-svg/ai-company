from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
P003_PROJECT_DIR = WORKSPACE_ROOT / "01_グラビア事業部" / "P003_グラビア事業部"
APPROVALS_PATH = WORKSPACE_ROOT / "04_グラビア事業部" / "APPROVALS.md"
RESULT_PATH = P003_PROJECT_DIR / "PLAN_APPROVAL_SYNC_RESULT.md"


@dataclass(frozen=True)
class PlanTarget:
    task_id: str
    task_name: str
    path: Path


PLAN_TARGETS = (
    PlanTarget("101", "カテゴリ改善", P003_PROJECT_DIR / "CATEGORY_FIX_PLAN.md"),
    PlanTarget("102", "内部リンク改善", P003_PROJECT_DIR / "INTERNAL_LINK_PLAN.md"),
    PlanTarget("103", "タイトル改善", P003_PROJECT_DIR / "TITLE_IMPROVEMENT_PLAN.md"),
)


def main() -> int:
    result = sync_plan_approvals()
    print(result)
    return 0


def sync_plan_approvals() -> str:
    approvals = _parse_approvals(_read_text(APPROVALS_PATH))
    result_rows = []

    for target in PLAN_TARGETS:
        approval = approvals.get(target.task_id, {})
        state = approval.get("承認状態", "").strip()
        approved_at = approval.get("承認日時", "").strip() or "未取得"

        if state != "GO":
            result_rows.append(
                {
                    "ID": target.task_id,
                    "タスク": target.task_name,
                    "承認状態": state or "未承認",
                    "対象ファイル": target.path.name,
                    "同期結果": "未実行",
                    "同期件数": "0",
                    "理由": "APPROVALS.mdでGOではないため",
                }
            )
            continue

        before = _read_text(target.path)
        if not before:
            result_rows.append(
                {
                    "ID": target.task_id,
                    "タスク": target.task_name,
                    "承認状態": state,
                    "対象ファイル": target.path.name,
                    "同期結果": "失敗",
                    "同期件数": "0",
                    "理由": "対象PLANファイル未取得",
                }
            )
            continue

        after, changed_count = _apply_go_to_plan(before, target.task_id, approved_at)
        approved_count = _count_go_table_rows(after)
        if after != before:
            target.path.write_text(after, encoding="utf-8")

        result_rows.append(
            {
                "ID": target.task_id,
                "タスク": target.task_name,
                "承認状態": state,
                "対象ファイル": target.path.name,
                "同期結果": "成功",
                "同期件数": str(approved_count),
                "理由": f"タスクGOを記事単位GOへ反映。変更件数: {changed_count}",
            }
        )

    RESULT_PATH.write_text(_format_result(result_rows), encoding="utf-8")
    go_count = sum(1 for row in result_rows if row["同期結果"] == "成功")
    return f"Plan approval sync completed: GO tasks={go_count}"


def _apply_go_to_plan(content: str, task_id: str, approved_at: str) -> Tuple[str, int]:
    lines = content.splitlines()
    updated: List[str] = []
    in_table = False
    headers: List[str] = []
    changed_count = 0

    for line in lines:
        clean = line.strip()

        if clean.startswith("|") and "編集長確認欄" in clean:
            headers = [cell.strip() for cell in clean.strip("|").split("|")]
            in_table = True
            updated.append(line)
            continue

        if in_table and clean.startswith("|") and _is_separator_row(clean):
            updated.append(line)
            continue

        if in_table and clean.startswith("|"):
            cells = [cell.strip() for cell in clean.strip("|").split("|")]
            if headers and len(cells) == len(headers):
                approval_index = headers.index("編集長確認欄")
                current = cells[approval_index].strip()
                if _is_unresolved_approval(current):
                    cells[approval_index] = "GO"
                    changed_count += 1
                updated.append("| " + " | ".join(cells) + " |")
                continue

        if in_table and not clean.startswith("|"):
            in_table = False
            headers = []

        if "- 承認: GO / STOP / 要確認" in line:
            updated.append(line.replace("GO / STOP / 要確認", "GO"))
            changed_count += 1
            continue

        if "| GO / STOP / 要確認 |" in line and _is_task_summary_line(line, task_id):
            updated.append(line.replace("| GO / STOP / 要確認 |", "| GO |"))
            changed_count += 1
            continue

        updated.append(line)

    note = _sync_note(task_id, approved_at)
    if note not in "\n".join(updated):
        updated.extend(["", "---", "", note])

    return "\n".join(updated).rstrip() + "\n", changed_count


def _sync_note(task_id: str, approved_at: str) -> str:
    return (
        "## 承認同期\n\n"
        f"- 同期元: `04_グラビア事業部/APPROVALS.md`\n"
        f"- 対象タスクID: {task_id}\n"
        f"- 承認状態: GO\n"
        f"- 承認日時: {approved_at}\n"
        "- 同期内容: タスク単位GOをPLAN内の記事単位GOへ反映\n"
        "- WordPress更新: 未実行\n"
        "- 投稿・削除: 未実行\n"
    )


def _parse_approvals(content: str) -> Dict[str, Dict[str, str]]:
    rows = _parse_table(content)
    return {row.get("ID", ""): row for row in rows if row.get("ID", "")}


def _parse_table(content: str) -> List[Dict[str, str]]:
    headers: List[str] = []
    rows: List[Dict[str, str]] = []
    for line in content.splitlines():
        clean = line.strip()
        if not clean.startswith("|"):
            continue
        cells = [cell.strip() for cell in clean.strip("|").split("|")]
        if not cells or _is_separator_cells(cells):
            continue
        if cells[0] == "ID":
            headers = cells
            continue
        if headers and len(cells) == len(headers):
            rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def _count_go_table_rows(content: str) -> int:
    count = 0
    in_table = False
    headers: List[str] = []
    for line in content.splitlines():
        clean = line.strip()
        if clean.startswith("|") and "編集長確認欄" in clean:
            headers = [cell.strip() for cell in clean.strip("|").split("|")]
            in_table = True
            continue
        if in_table and clean.startswith("|") and _is_separator_row(clean):
            continue
        if in_table and clean.startswith("|"):
            cells = [cell.strip() for cell in clean.strip("|").split("|")]
            if headers and "編集長確認欄" in headers and len(cells) == len(headers):
                if cells[headers.index("編集長確認欄")] == "GO":
                    count += 1
                continue
        if in_table and not clean.startswith("|"):
            break
    return count


def _format_result(rows: List[Dict[str, str]]) -> str:
    today = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# PLAN APPROVAL SYNC RESULT",
        "",
        "## 実行日時",
        "",
        today,
        "",
        "## Executive Summary",
        "",
        "- 目的: `APPROVALS.md`のタスクGOを、各改善PLANの記事単位GOへ反映する。",
        "- WordPress更新: 未実行",
        "- 投稿: 未実行",
        "- 削除: 未実行",
        "- 同期対象: TASK-101 / TASK-102 / TASK-103",
        "",
        "## 同期結果",
        "",
        "| ID | タスク | 承認状態 | 対象ファイル | 同期結果 | 同期件数 | 理由 |",
        "|---:|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {ID} | {タスク} | {承認状態} | {対象ファイル} | {同期結果} | {同期件数} | {理由} |".format(
                **{key: _clean_cell(value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## 次アクション",
            "",
            "- WordPress更新を行う場合は、更新専用タスクでGO記事のみを対象にする。",
            "- タイトル改善は`execute_title_improvement.py`でGO記事のみ実行できる。",
            "- 内部リンク改善は更新専用タスクでGO記事のみを対象にする。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _is_unresolved_approval(value: str) -> bool:
    normalized = value.strip()
    return normalized in {"GO / STOP / 要確認", "GO/STOP/要確認", ""}


def _is_task_summary_line(line: str, task_id: str) -> bool:
    if task_id == "101":
        return "5件すべて`グラビア`へ移動する" in line
    return False


def _is_separator_row(line: str) -> bool:
    return _is_separator_cells([cell.strip() for cell in line.strip("|").split("|")])


def _is_separator_cells(cells: List[str]) -> bool:
    return bool(cells) and all(set(cell) <= {"-", ":"} for cell in cells)


def _clean_cell(value: str) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())

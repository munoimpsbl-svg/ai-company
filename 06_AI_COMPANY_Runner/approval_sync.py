from datetime import datetime
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
P003_PROJECT_DIR = WORKSPACE_ROOT / "01_グラビア事業部" / "P003_グラビア事業部"
APPROVALS_PATH = WORKSPACE_ROOT / "04_グラビア事業部" / "APPROVALS.md"
BACKLOG_PATH = P003_PROJECT_DIR / "IMPROVEMENT_BACKLOG.md"
EXECUTION_BOARD_PATH = P003_PROJECT_DIR / "EXECUTION_BOARD.md"
PROGRESS_STATES = {"実装済み", "効果測定中", "完了"}


def main() -> int:
    result = sync_approvals_to_execution_board()
    print(result)
    return 0


def sync_approvals_to_execution_board() -> str:
    approvals = _parse_approvals(_read_text(APPROVALS_PATH))
    backlog_rows = _parse_markdown_table(_read_text(BACKLOG_PATH), "改善バックログ")
    if not backlog_rows:
        EXECUTION_BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
        EXECUTION_BOARD_PATH.write_text(_empty_board("IMPROVEMENT_BACKLOG.md未取得"), encoding="utf-8")
        return "Approval sync completed: backlog未取得"

    go_ids = {
        item_id
        for item_id, row in approvals.items()
        if row.get("承認状態", "").strip().upper() == "GO"
    }
    today_rows = []
    weekly_rows = []
    pending_rows = []
    measuring_rows = []
    done_rows = []

    for row in backlog_rows:
        item_id = row.get("ID", "").strip()
        state = row.get("状態", "").strip()
        normalized = dict(row)
        if item_id in go_ids and state in PROGRESS_STATES:
            normalized["備考"] = _append_note(
                normalized.get("備考", ""),
                f"APPROVALS.mdでGO承認済み。承認日時: {approvals[item_id].get('承認日時', '未取得')}",
            )
            if state == "効果測定中":
                measuring_rows.append(normalized)
            elif state == "完了":
                done_rows.append(normalized)
            else:
                weekly_rows.append(normalized)
        elif item_id in go_ids:
            normalized["状態"] = "実装待ち"
            normalized["備考"] = _append_note(
                normalized.get("備考", ""),
                f"APPROVALS.mdでGO承認済み。承認日時: {approvals[item_id].get('承認日時', '未取得')}",
            )
            today_rows.append(normalized)
        elif state == "承認待ち":
            normalized["備考"] = _append_note(
                normalized.get("備考", ""),
                _approval_note(approvals.get(item_id)),
            )
            pending_rows.append(normalized)
        elif state == "効果測定中":
            measuring_rows.append(normalized)
        elif state == "完了":
            done_rows.append(normalized)
        else:
            weekly_rows.append(normalized)

    board = _format_execution_board(
        today_rows=today_rows,
        weekly_rows=weekly_rows,
        pending_rows=pending_rows,
        measuring_rows=measuring_rows,
        done_rows=done_rows,
        go_count=len(today_rows),
    )
    EXECUTION_BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXECUTION_BOARD_PATH.write_text(board, encoding="utf-8")
    return f"Approval sync completed: GO={len(today_rows)} 実装待ち"


def _format_execution_board(
    today_rows,
    weekly_rows,
    pending_rows,
    measuring_rows,
    done_rows,
    go_count: int,
) -> str:
    today = datetime.now().date().isoformat()
    return f"""# EXECUTION BOARD

日付

{today}

参照元

`IMPROVEMENT_BACKLOG.md`

承認元

`04_グラビア事業部/APPROVALS.md`

---

## 今日実行

{_format_rows(today_rows, empty_note="実装待ちの改善タスクはありません。編集長GO後に今日実行へ移動します。")}

---

## 今週実行

{_format_rows(weekly_rows, empty_note="今週実行候補はありません。")}

---

## 承認待ち

{_format_rows(pending_rows, empty_note="承認待ちの改善タスクはありません。")}

---

## 効果測定中

{_format_rows(measuring_rows, empty_note="実装済みの改善タスクはまだありません。")}

---

## 完了

{_format_rows(done_rows, empty_note="完了タスクはまだありません。")}

---

## Runner認識

- GO案件: {go_count}件
- Runner実行対象: 状態が`実装待ち`の案件
- WordPress更新: 未実行
- 投稿: 未実行
- 削除: 未実行

---

## 運用ルール

- `APPROVALS.md`で`GO`の案件のみ`今日実行`へ表示する。
- `GO`案件の状態は`実装待ち`へ変更する。
- `STOP`と`要確認`は実行対象にしない。
- WordPress更新、投稿、削除はこの同期処理では行わない。
"""


def _format_rows(rows, empty_note: str) -> str:
    lines = [
        "| ID | タスク | 優先度 | 状態 | 効果 | 備考 |",
        "|---:|---|---|---|---|---|",
    ]
    if not rows:
        lines.append(f"| - | なし | - | - | - | {empty_note} |")
        return "\n".join(lines)

    for row in rows:
        lines.append(
            "| {ID} | {タスク} | {優先度} | {状態} | {効果} | {備考} |".format(
                ID=_clean_cell(row.get("ID", "")),
                タスク=_clean_cell(row.get("タスク", "")),
                優先度=_clean_cell(row.get("優先度", "")),
                状態=_clean_cell(row.get("状態", "")),
                効果=_clean_cell(row.get("効果", "")),
                備考=_clean_cell(row.get("備考", "")),
            )
        )
    return "\n".join(lines)


def _parse_approvals(content: str):
    rows = _parse_plain_table(content)
    return {row.get("ID", ""): row for row in rows if row.get("ID", "")}


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


def _parse_plain_table(content: str):
    rows = []
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
            rows.append({headers[index]: cells[index] for index in range(len(headers))})
    return rows


def _approval_note(approval):
    if not approval:
        return ""
    state = approval.get("承認状態", "").strip()
    if state in {"STOP", "要確認"}:
        return f"APPROVALS.mdで{state}。実行対象外。"
    return ""


def _append_note(base: str, note: str) -> str:
    if not note:
        return base
    if not base:
        return note
    if note in base:
        return base
    return f"{base} {note}"


def _empty_board(reason: str) -> str:
    today = datetime.now().date().isoformat()
    return f"""# EXECUTION BOARD

日付

{today}

## 今日実行

| ID | タスク | 優先度 | 状態 | 効果 | 備考 |
|---:|---|---|---|---|---|
| - | なし | - | - | - | {reason} |
"""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _clean_cell(value: str) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def _normalize_heading(line: str) -> str:
    return line.strip().replace(" ", "").replace("　", "")


if __name__ == "__main__":
    raise SystemExit(main())

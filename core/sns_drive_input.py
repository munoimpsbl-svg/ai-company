from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List

from core.config import load_config
from core.drive import DriveClient, FOLDER_MIME_TYPE
from core.logger import setup_logger


DRIVE_ROOT_FOLDER = "AI_COMPANY_INPUT"
SNS_PATH_PARTS = ("03_SNS事業部", "03_Analytics", "MIKU", "X")
DRIVE_INPUT_LABEL = f"{DRIVE_ROOT_FOLDER}/{'/'.join(SNS_PATH_PARTS)}"
CSV_MIME_TYPE = "text/csv"


def local_input_dir(workspace_root: Path) -> Path:
    return workspace_root / "03_SNS事業部" / "03_Analytics" / "MIKU" / "X"


def result_path(workspace_root: Path) -> Path:
    return workspace_root / "03_SNS事業部" / "03_Analytics" / "DRIVE_INPUT_SYNC_RESULT.md"


def manifest_path(workspace_root: Path) -> Path:
    return workspace_root / "03_SNS事業部" / "03_Analytics" / "DRIVE_INPUT_MANIFEST.json"


def get_drive_client() -> DriveClient:
    return DriveClient(load_config(), setup_logger())


def ensure_drive_input_folder(client: DriveClient) -> Dict[str, str]:
    current = client.create_folder_if_not_exists(DRIVE_ROOT_FOLDER)
    for part in SNS_PATH_PARTS:
        current = client.create_folder_if_not_exists(part, parent_id=current["id"])
    return current


def list_drive_csv_files(workspace_root: Path) -> Dict[str, object]:
    client = get_drive_client()
    folder = ensure_drive_input_folder(client)
    files = [
        item
        for item in client.list_children(folder["id"])
        if item.get("mimeType") != FOLDER_MIME_TYPE
        and item.get("name", "").lower().endswith(".csv")
    ]
    return {"folder": folder, "files": files}


def upload_drive_csv(
    workspace_root: Path,
    filename: str,
    content: str,
    overwrite: bool = False,
) -> Dict[str, str]:
    safe_name = _safe_csv_name(filename)
    client = get_drive_client()
    folder = ensure_drive_input_folder(client)
    existing = client.find_file(safe_name, parent_id=folder["id"])
    if existing and not overwrite:
        raise RuntimeError(f"同名CSVが既にあります: {safe_name}")
    file_data = client.save_text_file(
        safe_name,
        content,
        folder_id=folder["id"],
        mime_type=CSV_MIME_TYPE,
        error_label="SNS CSV保存",
    )
    sync_drive_inputs(workspace_root)
    return file_data


def read_drive_text(file_id: str, mime_type: str) -> str:
    return get_drive_client().read_text_file(file_id, mime_type)


def sync_drive_inputs(workspace_root: Path) -> Dict[str, object]:
    target_dir = local_input_dir(workspace_root)
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        client = get_drive_client()
        folder = ensure_drive_input_folder(client)
        rows = _download_csv_files(workspace_root, client, folder["id"])
        _write_manifest(workspace_root, folder, rows, "")
        result_path(workspace_root).write_text(
            _format_result(workspace_root, folder, rows, ""),
            encoding="utf-8",
        )
        return {"success": True, "folder": folder, "rows": rows, "error": ""}
    except Exception as exc:
        _write_manifest(workspace_root, {}, [], str(exc))
        result_path(workspace_root).write_text(
            _format_result(workspace_root, {}, [], str(exc)),
            encoding="utf-8",
        )
        return {"success": False, "folder": {}, "rows": [], "error": str(exc)}


def _download_csv_files(workspace_root: Path, client: DriveClient, folder_id: str):
    rows = []
    for item in client.list_children(folder_id):
        name = item.get("name", "")
        mime_type = item.get("mimeType", "")
        if mime_type == FOLDER_MIME_TYPE or not name.lower().endswith(".csv"):
            continue

        target_path = local_input_dir(workspace_root) / name
        try:
            content = client.read_text_file(item["id"], mime_type)
            target_path.write_text(content, encoding="utf-8")
            rows.append(
                {
                    "name": name,
                    "file_id": item.get("id", "未取得"),
                    "local_path": str(target_path.relative_to(workspace_root)),
                    "success": True,
                    "error": "",
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "name": name,
                    "file_id": item.get("id", "未取得"),
                    "local_path": str(target_path.relative_to(workspace_root)),
                    "success": False,
                    "error": str(exc),
                }
            )
    return rows


def _write_manifest(workspace_root: Path, folder, rows, error: str) -> None:
    path = manifest_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_of_truth": "google_drive",
        "synced_at": datetime.now().isoformat(timespec="seconds"),
        "google_drive_folder": DRIVE_INPUT_LABEL,
        "folder_id": folder.get("id", "") if folder else "",
        "local_mirror": str(local_input_dir(workspace_root).relative_to(workspace_root)),
        "success": not error,
        "error": error,
        "files": rows,
    }
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _format_result(workspace_root: Path, folder, rows, error: str) -> str:
    lines = [
        "# DRIVE INPUT SYNC RESULT",
        "",
        "## Input Folder",
        "",
        f"- Google Drive: {DRIVE_INPUT_LABEL}",
        f"- Folder ID: {folder.get('id', '未取得') if folder else '未取得'}",
        f"- Local Mirror: {local_input_dir(workspace_root).relative_to(workspace_root)}",
        f"- Manifest: {manifest_path(workspace_root).relative_to(workspace_root)}",
        "- Source of Truth: Google Drive",
        "",
        "## Executive Summary",
        "",
        f"- CSV取得成功: {sum(1 for row in rows if row['success'])}件",
        f"- CSV取得失敗: {sum(1 for row in rows if not row['success'])}件",
        f"- Error: {error or 'なし'}",
        "",
        "## Files",
        "",
        "| File | Drive ID | Local Path | Status | Error |",
        "|---|---|---|---|---|",
    ]
    if not rows:
        lines.append("| 未取得 | 未取得 | 未取得 | 未取得 | CSVファイルなし |")
    for row in rows:
        lines.append(
            "| {name} | {file_id} | {local_path} | {status} | {error} |".format(
                name=_clean(row["name"]),
                file_id=_clean(row["file_id"]),
                local_path=_clean(row["local_path"]),
                status="SUCCESS" if row["success"] else "FAILED",
                error=_clean(row["error"] or ""),
            )
        )
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Google DriveからCSVを読む。",
            "- 分析対象は`DRIVE_INPUT_MANIFEST.json`に記録されたDrive同期済みCSVのみ。",
            "- ローカルに手動配置されたCSVは正としない。",
            "- SNS投稿は行わない。",
            "- SNSログインは行わない。",
            "- ローカルミラーは分析用コピーとして作成する。",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _safe_csv_name(filename: str) -> str:
    name = Path(filename or "").name.strip()
    if not name:
        raise ValueError("CSVファイル名が未入力です。")
    if not name.lower().endswith(".csv"):
        name += ".csv"
    if "/" in name or "\\" in name:
        raise ValueError("CSVファイル名にパスは指定できません。")
    return name


def _clean(value: str) -> str:
    return str(value).replace("|", "｜").replace("\n", " ").strip() or "なし"

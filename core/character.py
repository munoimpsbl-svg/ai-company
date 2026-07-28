from typing import Dict, List

from core.drive import DriveClient, DriveError


CHARACTER_FOLDER_CANDIDATES = [
    ("03_SNS事業部", "01_Characters"),
    (None, "01_Characters"),
]


def load_character_folder(
    drive: DriveClient, company_folder: Dict[str, str], character_name: str
) -> Dict[str, object]:
    characters_root = None
    character_folder = None
    resolved_path = None

    for department_name, characters_folder_name in CHARACTER_FOLDER_CANDIDATES:
        parent_folder = company_folder
        path_parts = [company_folder["name"]]

        if department_name:
            department_folder = drive.find_folder(
                department_name, parent_id=company_folder["id"]
            )
            if not department_folder:
                continue
            parent_folder = department_folder
            path_parts.append(department_folder["name"])

        characters_root = drive.find_folder(
            characters_folder_name, parent_id=parent_folder["id"]
        )
        if not characters_root:
            continue

        character_folder = drive.find_folder(
            character_name, parent_id=characters_root["id"]
        )
        if character_folder:
            path_parts.extend([characters_root["name"], character_folder["name"]])
            resolved_path = "/".join(path_parts)
            break

    if not character_folder or not characters_root:
        raise DriveError(
            f"03_SNS事業部/01_Characters または 01_Characters に"
            f"{character_name}フォルダが見つかりません。"
        )

    children = drive.list_children(character_folder["id"])
    text_files = _read_text_children(drive, children)

    return {
        "folder": character_folder,
        "path": resolved_path,
        "children": children,
        "text_files": text_files,
    }


def _read_text_children(
    drive: DriveClient, children: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    readable_files = []
    for child in children:
        mime_type = child.get("mimeType", "")
        if mime_type.startswith("text/") or mime_type in (
            "application/json",
            "application/vnd.google-apps.document",
        ):
            readable_files.append(
                {
                    "name": child["name"],
                    "mimeType": mime_type,
                    "content": drive.read_text_file(child["id"], mime_type),
                }
            )
    return readable_files

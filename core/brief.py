from typing import Dict

from core.drive import DriveClient, DriveError


def load_daily_brief(
    drive: DriveClient, company_folder: Dict[str, str], daily_brief_name: str
) -> str:
    brief_file = drive.find_file(daily_brief_name, parent_id=company_folder["id"])
    if not brief_file:
        raise DriveError(
            f"{company_folder['name']}直下に{daily_brief_name}が見つかりません。"
        )

    return drive.read_text_file(brief_file["id"], brief_file["mimeType"])

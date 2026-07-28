import json
import os
from pathlib import Path
from typing import Dict, List, Optional

try:
    from google.auth.exceptions import GoogleAuthError
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.http import MediaInMemoryUpload
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ModuleNotFoundError as exc:
    GoogleAuthError = Exception
    HttpError = Exception
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from core.config import AppConfig
from core.config import load_config
from core.google_credentials import (
    non_interactive_auth_enabled,
    oauth_credentials_from_env,
    service_account_credentials_from_env,
    token_file_has_required_scopes,
)
from core.logger import setup_logger


SCOPES = [
    "https://www.googleapis.com/auth/drive",
]
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME_TYPE = "application/vnd.google-apps.document"
MARKDOWN_MIME_TYPE = "text/markdown"
LOCAL_REPORTS_DIR = Path("output/reports")


class DriveError(RuntimeError):
    pass


class DriveClient:
    def __init__(self, config: AppConfig, logger):
        if _IMPORT_ERROR:
            raise DriveError(
                "Google Drive APIライブラリが未導入です。"
                " `python3 -m pip install -r requirements.txt` を実行してください。"
            ) from _IMPORT_ERROR

        self.config = config
        self.logger = logger
        credentials = self._load_credentials()
        self.service = build("drive", "v3", credentials=credentials)
        self.docs_service = build("docs", "v1", credentials=credentials)

    def _load_credentials(self):
        env_service_account = service_account_credentials_from_env(SCOPES)
        if env_service_account:
            return env_service_account

        if self.config.google_application_credentials:
            return self._load_service_account_credentials(
                self.config.google_application_credentials
            )

        env_oauth = oauth_credentials_from_env(
            SCOPES,
            json_names=("GOOGLE_DRIVE_OAUTH_TOKEN_JSON", "GOOGLE_OAUTH_TOKEN_JSON"),
            base64_names=(
                "GOOGLE_DRIVE_OAUTH_TOKEN_BASE64",
                "GOOGLE_OAUTH_TOKEN_BASE64",
            ),
        )
        if env_oauth:
            return env_oauth

        if self.config.google_oauth_client_secret:
            return self._load_oauth_credentials(
                self.config.google_oauth_client_secret,
                self.config.google_oauth_token,
            )

        raise DriveError(
            "Google Drive認証情報が未設定です。"
            " GOOGLE_APPLICATION_CREDENTIALS または GOOGLE_OAUTH_CLIENT_SECRET を設定してください。"
        )

    def _load_service_account_credentials(self, credentials_path: Path):
        if not credentials_path.exists():
            raise DriveError(f"サービスアカウント鍵が見つかりません: {credentials_path}")

        try:
            return service_account.Credentials.from_service_account_file(
                str(credentials_path), scopes=SCOPES
            )
        except (ValueError, GoogleAuthError) as exc:
            raise DriveError(f"サービスアカウント認証に失敗しました: {exc}") from exc

    def _load_oauth_credentials(self, client_secret_path: Path, token_path: Path):
        if not client_secret_path.exists():
            raise DriveError(f"OAuth client secretが見つかりません: {client_secret_path}")

        credentials = None
        if token_path.exists():
            if not token_file_has_required_scopes(token_path, SCOPES):
                self.logger.info("Google Drive書き込み権限のためOAuth再認証が必要です。")
            else:
                credentials = Credentials.from_authorized_user_file(
                    str(token_path), SCOPES
                )

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        if not credentials or not credentials.valid:
            if non_interactive_auth_enabled():
                raise DriveError(
                    "Google Drive OAuth tokenが未設定です。"
                    " GOOGLE_DRIVE_OAUTH_TOKEN_JSON または GOOGLE_OAUTH_TOKEN_JSON を設定してください。"
                )
            self.logger.info("OAuth認証を開始します。表示されたURLでGoogle認証してください。")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_path), SCOPES
            )
            credentials = flow.run_local_server(port=0, open_browser=False)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(credentials.to_json(), encoding="utf-8")

        return credentials

    def find_folder(
        self, name: str, parent_id: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        query_parts = [
            "trashed = false",
            f"name = '{self._escape_query_value(name)}'",
            f"mimeType = '{FOLDER_MIME_TYPE}'",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        return self._first_file(" and ".join(query_parts))

    def list_children(self, folder_id: str) -> List[Dict[str, str]]:
        try:
            response = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="files(id, name, mimeType, modifiedTime)",
                    orderBy="folder,name",
                    pageSize=100,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            return response.get("files", [])
        except HttpError as exc:
            raise DriveError(f"フォルダ内容の取得に失敗しました: {exc}") from exc

    def find_file(
        self, name: str, parent_id: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        query_parts = [
            "trashed = false",
            f"name = '{self._escape_query_value(name)}'",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        return self._first_file(" and ".join(query_parts))

    def create_folder_if_not_exists(
        self, folder_name: str, parent_id: Optional[str] = None
    ) -> Dict[str, str]:
        folder = self.find_folder(folder_name, parent_id=parent_id)
        if folder:
            return folder

        metadata = {
            "name": folder_name,
            "mimeType": FOLDER_MIME_TYPE,
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        try:
            return (
                self.service.files()
                .create(
                    body=metadata,
                    fields="id, name, mimeType, modifiedTime",
                    supportsAllDrives=True,
                )
                .execute()
            )
        except HttpError as exc:
            raise DriveError(f"フォルダ作成に失敗しました: {exc}") from exc

    def save_markdown(
        self, filename: str, content: str, folder_id: Optional[str] = None
    ) -> Dict[str, str]:
        return self.save_text_file(
            filename,
            content,
            folder_id=folder_id,
            mime_type=MARKDOWN_MIME_TYPE,
            error_label="Markdown保存",
        )

    def save_text_file(
        self,
        filename: str,
        content: str,
        folder_id: Optional[str] = None,
        mime_type: str = "text/plain",
        error_label: str = "テキスト保存",
    ) -> Dict[str, str]:
        existing_file = self.find_file(filename, parent_id=folder_id)
        media = MediaInMemoryUpload(
            _normalize_markdown(content).encode("utf-8"),
            mimetype=mime_type,
            resumable=False,
        )

        try:
            if existing_file:
                return (
                    self.service.files()
                    .update(
                        fileId=existing_file["id"],
                        media_body=media,
                        fields="id, name, mimeType, modifiedTime",
                        supportsAllDrives=True,
                    )
                    .execute()
                )

            metadata = {"name": filename, "mimeType": mime_type}
            if folder_id:
                metadata["parents"] = [folder_id]

            return (
                self.service.files()
                .create(
                    body=metadata,
                    media_body=media,
                    fields="id, name, mimeType, modifiedTime",
                    supportsAllDrives=True,
                )
                .execute()
            )
        except HttpError as exc:
            raise DriveError(f"{error_label}に失敗しました: {exc}") from exc

    def load_markdown(self, file_id: str) -> str:
        metadata = self._get_file_metadata(file_id)
        return self.read_text_file(file_id, metadata["mimeType"])

    def read_text_file(self, file_id: str, mime_type: str) -> str:
        try:
            if mime_type == GOOGLE_DOC_MIME_TYPE:
                request = self.service.files().export_media(
                    fileId=file_id, mimeType="text/plain"
                )
            else:
                request = self.service.files().get_media(fileId=file_id)
            return request.execute().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DriveError("ファイルのUTF-8読込に失敗しました。") from exc
        except HttpError as exc:
            raise DriveError(f"ファイル読込に失敗しました: {exc}") from exc

    def append_text_file(self, file_id: str, mime_type: str, text: str) -> None:
        try:
            if mime_type == GOOGLE_DOC_MIME_TYPE:
                self._append_google_doc(file_id, text)
                return

            current = self.read_text_file(file_id, mime_type)
            media = MediaInMemoryUpload(
                (current.rstrip() + "\n\n" + text.strip() + "\n").encode("utf-8"),
                mimetype="text/markdown",
                resumable=False,
            )
            self.service.files().update(
                fileId=file_id,
                media_body=media,
                supportsAllDrives=True,
            ).execute()
        except HttpError as exc:
            raise DriveError(f"ファイル追記に失敗しました: {exc}") from exc

    def _append_google_doc(self, document_id: str, text: str) -> None:
        document = self.docs_service.documents().get(documentId=document_id).execute()
        content = document.get("body", {}).get("content", [])
        if not content:
            insert_index = 1
        else:
            insert_index = max(1, content[-1].get("endIndex", 2) - 1)

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {"index": insert_index},
                            "text": "\n\n" + text.strip() + "\n",
                        }
                    }
                ]
            },
        ).execute()

    def _first_file(self, query: str) -> Optional[Dict[str, str]]:
        try:
            response = (
                self.service.files()
                .list(
                    q=query,
                    fields="files(id, name, mimeType, modifiedTime)",
                    pageSize=1,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            files = response.get("files", [])
            return files[0] if files else None
        except HttpError as exc:
            raise DriveError(f"Google Drive検索に失敗しました: {exc}") from exc

    def _get_file_metadata(self, file_id: str) -> Dict[str, str]:
        try:
            return (
                self.service.files()
                .get(
                    fileId=file_id,
                    fields="id, name, mimeType, modifiedTime",
                    supportsAllDrives=True,
                )
                .execute()
            )
        except HttpError as exc:
            raise DriveError(f"ファイル情報の取得に失敗しました: {exc}") from exc

    @staticmethod
    def _escape_query_value(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")


def create_folder_if_not_exists(
    folder_name: str, parent_id: Optional[str] = None
) -> Dict[str, str]:
    try:
        folder = _get_default_client().create_folder_if_not_exists(
            folder_name, parent_id=parent_id
        )
        return {"backend": "google_drive", **folder}
    except DriveError:
        path = _local_folder_path(folder_name, parent_id)
        path.mkdir(parents=True, exist_ok=True)
        return {"backend": "local", "id": str(path), "name": folder_name}


def save_markdown(
    filename: str, content: str, folder_id: Optional[str] = None
) -> Dict[str, str]:
    try:
        file_data = _get_default_client().save_markdown(filename, content, folder_id)
        return {"backend": "google_drive", **file_data}
    except DriveError:
        return _save_markdown_locally(filename, content, folder_id)


def load_markdown(file_id: str) -> str:
    try:
        return _get_default_client().load_markdown(file_id)
    except DriveError:
        path = Path(file_id).expanduser()
        if not path.exists():
            path = LOCAL_REPORTS_DIR / file_id
        return path.read_text(encoding="utf-8")


def save_report(project_id: str, filename: str, content: str) -> Dict[str, str]:
    return _save_project_markdown(project_id, "REPORT", filename, content)


def save_review(project_id: str, filename: str, content: str) -> Dict[str, str]:
    return _save_project_markdown(project_id, "REVIEW", filename, content)


def _save_project_markdown(
    project_id: str, document_type: str, filename: str, content: str
) -> Dict[str, str]:
    try:
        client = _get_default_client()
        root_folder = _resolve_drive_root(client)
        project_folder = client.create_folder_if_not_exists(
            project_id, parent_id=root_folder["id"]
        )
        type_folder = client.create_folder_if_not_exists(
            document_type, parent_id=project_folder["id"]
        )
        file_data = client.save_markdown(filename, content, type_folder["id"])
        return {"backend": "google_drive", **file_data}
    except DriveError:
        return _save_markdown_locally(
            filename, content, folder_id=f"{project_id}/{document_type}"
        )


def _get_default_client() -> DriveClient:
    config = load_config()
    logger = setup_logger()
    return DriveClient(config, logger)


def _resolve_drive_root(client: DriveClient) -> Dict[str, str]:
    root_id = os.getenv("AI_COMPANY_DRIVE_ROOT_ID")
    if root_id:
        return client._get_file_metadata(root_id)

    return client.create_folder_if_not_exists(client.config.company_folder_name)


def _save_markdown_locally(
    filename: str, content: str, folder_id: Optional[str] = None
) -> Dict[str, str]:
    folder = _local_folder_path("", folder_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    path.write_text(_normalize_markdown(content), encoding="utf-8")
    return {
        "backend": "local",
        "id": str(path),
        "name": filename,
        "path": str(path),
    }


def _local_folder_path(folder_name: str, parent_id: Optional[str] = None) -> Path:
    parts = []
    if parent_id:
        parts.extend(part for part in str(parent_id).split("/") if part)
    if folder_name:
        parts.append(folder_name)
    return LOCAL_REPORTS_DIR.joinpath(*parts)


def _normalize_markdown(content: str) -> str:
    return content.rstrip() + "\n"

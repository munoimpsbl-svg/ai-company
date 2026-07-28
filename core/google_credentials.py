import base64
import json
import os
from pathlib import Path
from typing import Iterable, Optional

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials


SERVICE_ACCOUNT_JSON_ENV_NAMES = (
    "GOOGLE_APPLICATION_CREDENTIALS_JSON",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
)
SERVICE_ACCOUNT_BASE64_ENV_NAMES = (
    "GOOGLE_APPLICATION_CREDENTIALS_BASE64",
    "GOOGLE_SERVICE_ACCOUNT_BASE64",
)


def service_account_credentials_from_env(scopes):
    info = _json_from_env(SERVICE_ACCOUNT_JSON_ENV_NAMES, SERVICE_ACCOUNT_BASE64_ENV_NAMES)
    if not info:
        return None
    try:
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except (ValueError, GoogleAuthError):
        return None


def oauth_credentials_from_env(scopes, json_names: Iterable[str], base64_names=()):
    info = _json_from_env(tuple(json_names), tuple(base64_names))
    if not info or not _info_has_required_scopes(info, scopes):
        return None
    try:
        credentials = Credentials.from_authorized_user_info(info, scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials if credentials.valid else None
    except (ValueError, GoogleAuthError, OSError):
        return None


def oauth_credentials_from_file(token_path: Path, scopes, persist_refresh=True):
    if not token_path.exists() or not token_file_has_required_scopes(token_path, scopes):
        return None
    try:
        credentials = Credentials.from_authorized_user_file(str(token_path), scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            if persist_refresh:
                token_path.write_text(credentials.to_json(), encoding="utf-8")
        return credentials if credentials.valid else None
    except (ValueError, GoogleAuthError, OSError):
        return None


def token_file_has_required_scopes(token_path: Path, scopes) -> bool:
    try:
        info = json.loads(token_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return _info_has_required_scopes(info, scopes)


def non_interactive_auth_enabled() -> bool:
    return os.getenv("AI_COMPANY_NON_INTERACTIVE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _json_from_env(json_names, base64_names) -> Optional[dict]:
    for name in json_names:
        value = os.getenv(name, "").strip()
        if not value:
            continue
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    for name in base64_names:
        value = os.getenv(name, "").strip()
        if not value:
            continue
        try:
            return json.loads(base64.b64decode(value).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None
    return None


def _info_has_required_scopes(info: dict, scopes) -> bool:
    token_scopes = info.get("scopes") or info.get("scope") or []
    if isinstance(token_scopes, str):
        token_scopes = token_scopes.split()
    return set(scopes).issubset(set(token_scopes))

import os
from datetime import date, timedelta
from pathlib import Path

from core.config import load_config
from core.google_credentials import (
    oauth_credentials_from_env,
    oauth_credentials_from_file,
    service_account_credentials_from_env,
    token_file_has_required_scopes,
)

try:
    from google.auth.exceptions import GoogleAuthError
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ModuleNotFoundError:
    GoogleAuthError = Exception
    HttpError = Exception
    _IMPORT_ERROR = True
else:
    _IMPORT_ERROR = False


SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def fetch():
    load_config()
    if _IMPORT_ERROR:
        return _empty()

    property_id = _property_id()
    if not property_id:
        return _empty()

    credentials = _credentials()
    if not credentials:
        return _empty()

    try:
        service = build("analyticsdata", "v1beta", credentials=credentials)
        response = (
            service.properties()
            .runReport(
                property=f"properties/{property_id}",
                body=_query_body(),
            )
            .execute()
        )
    except (HttpError, GoogleAuthError, OSError, ValueError):
        return _empty()

    rows = response.get("rows", [])
    if not rows:
        return _empty()

    return _normalize(rows[0])


def authorize(open_browser=True):
    load_config()
    if _IMPORT_ERROR:
        return False

    client_secret_path = _client_secret_path()
    if not client_secret_path or not client_secret_path.exists():
        return False

    token_path = _token_path()
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path), SCOPES
        )
        credentials = flow.run_local_server(port=0, open_browser=open_browser)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
        return True
    except (GoogleAuthError, OSError, ValueError):
        return False


def _credentials():
    env_service_account = service_account_credentials_from_env(SCOPES)
    if env_service_account:
        return env_service_account

    service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if service_account_path:
        credentials = _service_account_credentials(Path(service_account_path))
        if credentials:
            return credentials

    env_oauth = oauth_credentials_from_env(
        SCOPES,
        json_names=(
            "GOOGLE_GA4_TOKEN_JSON",
            "GOOGLE_OAUTH_TOKEN_JSON",
        ),
        base64_names=(
            "GOOGLE_GA4_TOKEN_BASE64",
            "GOOGLE_OAUTH_TOKEN_BASE64",
        ),
    )
    if env_oauth:
        return env_oauth

    token_path = _token_path()
    return oauth_credentials_from_file(token_path, SCOPES)


def _service_account_credentials(path):
    if not path.exists():
        return None
    try:
        return service_account.Credentials.from_service_account_file(
            str(path), scopes=SCOPES
        )
    except (GoogleAuthError, OSError, ValueError):
        return None


def _client_secret_path():
    value = os.getenv("GOOGLE_GA4_CLIENT_SECRET", "").strip() or os.getenv(
        "GOOGLE_OAUTH_CLIENT_SECRET", ""
    ).strip()
    return Path(value).expanduser() if value else None


def _token_path():
    return Path(
        os.getenv(
            "GOOGLE_GA4_TOKEN",
            ".secrets/ga4_token.json",
        )
    ).expanduser()


def _property_id():
    return (
        os.getenv("GA4_PROPERTY_ID", "").strip()
        or os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID", "").strip()
    )


def _query_body():
    yesterday = date.today() - timedelta(days=1)
    start_date = os.getenv(
        "GOOGLE_GA4_START_DATE",
        (yesterday - timedelta(days=27)).isoformat(),
    )
    end_date = os.getenv("GOOGLE_GA4_END_DATE", yesterday.isoformat())
    return {
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "metrics": [
            {"name": "totalUsers"},
            {"name": "sessions"},
            {"name": "screenPageViews"},
            {"name": "userEngagementDuration"},
        ],
    }


def _normalize(row):
    values = row.get("metricValues", [])
    return {
        "users": _metric(values, 0),
        "sessions": _metric(values, 1),
        "page_views": _metric(values, 2),
        "engagement_time": _metric(values, 3),
    }


def _metric(values, index):
    try:
        raw_value = values[index].get("value", 0)
    except (IndexError, AttributeError):
        return 0

    try:
        number = float(raw_value)
    except (TypeError, ValueError):
        return 0
    return int(number) if number.is_integer() else number


def _token_has_required_scopes(token_path):
    return token_file_has_required_scopes(token_path, SCOPES)


def _empty():
    return {
        "users": 0,
        "sessions": 0,
        "page_views": 0,
        "engagement_time": 0,
    }


if __name__ == "__main__":
    if authorize(open_browser=True):
        print(fetch())
    else:
        print(_empty())

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class AppConfig:
    company_folder_name: str
    daily_brief_name: str
    character_name: str
    google_application_credentials: Optional[Path]
    google_oauth_client_secret: Optional[Path]
    google_oauth_token: Path


def _optional_path(value: Optional[str]) -> Optional[Path]:
    if not value:
        return None
    return Path(value).expanduser()


def load_config() -> AppConfig:
    _load_env_file(Path(".env"))

    return AppConfig(
        company_folder_name=os.getenv("AI_COMPANY_FOLDER_NAME", "AI_COMPANY"),
        daily_brief_name=os.getenv("AI_COMPANY_DAILY_BRIEF", "Daily_Brief.md"),
        character_name=os.getenv("AI_COMPANY_CHARACTER", "MIKU"),
        google_application_credentials=_optional_path(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        ),
        google_oauth_client_secret=_optional_path(
            os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        ),
        google_oauth_token=Path(
            os.getenv("GOOGLE_OAUTH_TOKEN", ".secrets/google_token.json")
        ).expanduser(),
    )


def _load_env_file(path: Path) -> None:
    env_path = path.expanduser()
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

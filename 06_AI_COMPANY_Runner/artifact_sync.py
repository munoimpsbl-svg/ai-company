from dataclasses import dataclass
from pathlib import Path
import sys
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for site_packages in (Path(__file__).resolve().parents[1] / ".venv" / "lib").glob(
    "python*/site-packages"
):
    sys.path.insert(0, str(site_packages))

from core.config import load_config
from core.drive import DriveClient
from core.logger import setup_logger


TARGET_FILENAMES = {
    "REPORT.md",
    "DAILY_BRIEF.md",
    "CEO_REPORT.md",
    "RUN_REPORT.md",
    "KPI_DASHBOARD.md",
    "SNS_REPORT.md",
    "GENERATION_QUALITY_REPORT.md",
    "DRIVE_INPUT_SYNC_RESULT.md",
    "DRIVE_INPUT_MANIFEST.json",
    "README.md",
    "SPEC.md",
    "TASK.md",
    "REVIEW.md",
    "CHANGELOG.md",
    "DEPLOY_RENDER.md",
    "render.yaml",
    "Procfile",
    "runtime.txt",
    "config.toml",
}
IGNORED_PARTS = {
    ".git",
    ".secrets",
    ".venv",
    "__pycache__",
    ".pycache",
    "dist",
    "installer",
    "output",
}
ALLOWED_HIDDEN_PARTS = {".streamlit"}


@dataclass(frozen=True)
class ArtifactSyncResult:
    path: Path
    success: bool
    backend: str
    destination: str
    error: str


def sync_runner_artifacts(workspace_root: Path) -> List[ArtifactSyncResult]:
    artifacts = _collect_artifacts(workspace_root)
    results = []
    try:
        client = DriveClient(load_config(), setup_logger())
        root_folder = client.create_folder_if_not_exists("AI_COMPANY_RUNNER_ARTIFACTS")
    except Exception as exc:
        return [
            ArtifactSyncResult(
                path=artifact.relative_to(workspace_root),
                success=False,
                backend="google_drive",
                destination="未保存",
                error=f"Google Drive接続失敗: {exc}",
            )
            for artifact in artifacts
        ]

    for artifact in artifacts:
        results.append(_sync_artifact(workspace_root, artifact, client, root_folder))

    return results


def format_sync_results(results: List[ArtifactSyncResult]) -> str:
    if not results:
        return "- 対象成果物なし"

    lines = []
    for result in results:
        status = "SUCCESS" if result.success else "FAILED"
        lines.append(f"- {result.path}: {status} ({result.backend})")
        lines.append(f"  - Destination: {result.destination}")
        if result.error:
            lines.append(f"  - Error: {result.error}")
    return "\n".join(lines)


def _collect_artifacts(workspace_root: Path) -> List[Path]:
    artifacts = []
    for path in workspace_root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(workspace_root)
        if _is_ignored(relative_path):
            continue
        if path.name in TARGET_FILENAMES:
            artifacts.append(path)
    return sorted(set(artifacts), key=lambda item: str(item))


def _sync_artifact(
    workspace_root: Path,
    artifact: Path,
    client: DriveClient,
    root_folder,
) -> ArtifactSyncResult:
    relative_path = artifact.relative_to(workspace_root)
    try:
        content = artifact.read_text(encoding="utf-8")
        current_folder = root_folder
        for part in relative_path.parts[:-1]:
            current_folder = client.create_folder_if_not_exists(
                part, parent_id=current_folder["id"]
            )

        result = client.save_markdown(
            relative_path.name, content, folder_id=current_folder["id"]
        )
        return ArtifactSyncResult(
            path=relative_path,
            success=True,
            backend="google_drive",
            destination=result.get("id", "未取得"),
            error="",
        )
    except Exception as exc:
        return ArtifactSyncResult(
            path=relative_path,
            success=False,
            backend="error",
            destination="未取得",
            error=str(exc),
        )


def _is_ignored(path: Path) -> bool:
    return any(
        part in IGNORED_PARTS
        or (part.startswith(".") and part not in ALLOWED_HIDDEN_PARTS)
        for part in path.parts
    )

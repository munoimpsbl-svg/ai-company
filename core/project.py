from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


STANDARD_PROJECT_FILES = (
    "PROJECT.md",
    "SPEC.md",
    "TASK.md",
    "REPORT.md",
    "CHANGELOG.md",
)


@dataclass(frozen=True)
class ProjectStatus:
    project_id: str
    path: Path
    existing_files: List[str]
    missing_files: List[str]

    @property
    def is_complete(self) -> bool:
        return not self.missing_files


def discover_projects(root: Path) -> List[ProjectStatus]:
    workspace_root = root.expanduser().resolve()
    project_dirs = _candidate_project_dirs(workspace_root)
    return [inspect_project(path) for path in project_dirs]


def inspect_project(path: Path) -> ProjectStatus:
    existing_files = [
        filename for filename in STANDARD_PROJECT_FILES if (path / filename).is_file()
    ]
    missing_files = [
        filename for filename in STANDARD_PROJECT_FILES if filename not in existing_files
    ]

    return ProjectStatus(
        project_id=_project_id_from_path(path),
        path=path,
        existing_files=existing_files,
        missing_files=missing_files,
    )


def format_project_statuses(statuses: Iterable[ProjectStatus], root: Path) -> str:
    lines = []
    for status in statuses:
        relative_path = status.path.relative_to(root)
        state = "OK" if status.is_complete else "MISSING"
        lines.append(f"- {status.project_id}: {state} ({relative_path})")
        if status.missing_files:
            lines.append(f"  - Missing: {', '.join(status.missing_files)}")

    return "\n".join(lines) if lines else "- プロジェクトフォルダ未検出"


def _candidate_project_dirs(root: Path) -> List[Path]:
    candidates = []
    for project_file in root.rglob("PROJECT.md"):
        if _is_hidden_path(project_file.relative_to(root)):
            continue
        candidates.append(project_file.parent)

    return sorted(set(candidates), key=lambda path: str(path))


def _project_id_from_path(path: Path) -> str:
    name = path.name
    if "_" in name:
        return name.split("_", 1)[0]
    return name


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)

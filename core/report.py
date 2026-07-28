from pathlib import Path
from typing import Optional


class ReportError(RuntimeError):
    pass


def save_report(
    project_id: str,
    title: str,
    content: str,
    workspace_root: Optional[Path] = None,
) -> Path:
    root = Path(workspace_root or Path.cwd()).expanduser().resolve()
    project_dir = _find_project_dir(root, project_id)
    report_path = project_dir / "REPORT.md"

    body = _format_report(title, content)
    report_path.write_text(body, encoding="utf-8")
    return report_path


def append_changelog(
    project_id: str,
    entry: str,
    workspace_root: Optional[Path] = None,
) -> Path:
    root = Path(workspace_root or Path.cwd()).expanduser().resolve()
    project_dir = _find_project_dir(root, project_id)
    changelog_path = project_dir / "CHANGELOG.md"

    clean_entry = entry.strip()
    if not clean_entry:
        raise ReportError("entry は空にできません。")

    if changelog_path.exists():
        current = changelog_path.read_text(encoding="utf-8").rstrip()
        changelog_path.write_text(f"{current}\n\n{clean_entry}\n", encoding="utf-8")
    else:
        changelog_path.write_text(f"# {project_id} CHANGELOG\n\n{clean_entry}\n", encoding="utf-8")

    return changelog_path


def _find_project_dir(root: Path, project_id: str) -> Path:
    if not root.exists():
        raise ReportError(f"ワークスペースが見つかりません: {root}")

    candidates = [
        path
        for path in root.rglob(f"{project_id}*")
        if path.is_dir() and not _is_hidden_path(path.relative_to(root))
    ]

    if not candidates:
        raise ReportError(f"{project_id} のプロジェクトフォルダが見つかりません。")

    exact = [path for path in candidates if path.name == project_id]
    if exact:
        return sorted(exact, key=lambda path: len(path.parts))[0]

    return sorted(candidates, key=lambda path: (len(path.parts), str(path)))[0]


def _format_report(title: str, content: str) -> str:
    clean_title = title.strip()
    clean_content = content.strip()

    if not clean_title:
        raise ReportError("title は空にできません。")
    if not clean_content:
        raise ReportError("content は空にできません。")

    return f"# {clean_title}\n\n{clean_content}\n"


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)

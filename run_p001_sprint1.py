from datetime import date
from pathlib import Path

from core.platform import build_p001_sprint1_report
from core.report import append_changelog, save_report


def main() -> int:
    workspace_root = Path(__file__).resolve().parent
    sprint_report = build_p001_sprint1_report(
        workspace_root=workspace_root,
        report_date=date.today(),
    )

    report_path = save_report(
        project_id="P001",
        title=sprint_report.title,
        content=sprint_report.content,
        workspace_root=workspace_root,
    )
    changelog_path = append_changelog(
        project_id="P001",
        entry=(
            f"## {date.today().isoformat()}\n\n"
            "### Changed\n\n"
            "- P001 Sprint1を開始。\n"
            "- 標準プロジェクトファイル検出、日報生成、CHANGELOG追記を実装。\n"
            "- 投稿、公開、削除、移動、自動承認は未実行。"
        ),
        workspace_root=workspace_root,
    )

    print(f"REPORT saved: {report_path}")
    print(f"CHANGELOG updated: {changelog_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

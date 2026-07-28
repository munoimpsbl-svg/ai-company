from pathlib import Path

from core.daily_brief_reader import build_ceo_daily_brief_report, read_daily_briefs
from core.logger import setup_logger
from core.report import append_changelog, save_report


def main() -> int:
    logger = setup_logger()
    workspace_root = Path(__file__).resolve().parent

    logger.info("P005 TASK-001 Daily Brief Readerを開始します。")
    briefs = read_daily_briefs(workspace_root)
    logger.info("Daily Briefを%s件読み取りました。", len(briefs))

    report = build_ceo_daily_brief_report(briefs, workspace_root)
    report_path = save_report(
        project_id="P005",
        title="AI社長 Daily Brief Reader",
        content=report,
        workspace_root=workspace_root,
    )
    changelog_path = append_changelog(
        project_id="P005",
        entry=(
            "## 2026-07-05\n\n"
            "### Added\n\n"
            "- TASK-001 Daily Brief Readerを実装。\n"
            "- AI COMPANY内のDAILY_BRIEF.md読み取りに対応。\n"
            "- CEO向けREPORT.md生成に対応。"
        ),
        workspace_root=workspace_root,
    )

    logger.info("P005 REPORTを保存しました: %s", report_path)
    logger.info("P005 CHANGELOGを更新しました: %s", changelog_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

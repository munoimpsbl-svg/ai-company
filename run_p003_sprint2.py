from pathlib import Path

from core.config import load_config
from core.drive import save_report
from core.logger import setup_logger
from core.wordpress import build_wordpress_report, load_wordpress_analysis


def main() -> int:
    logger = setup_logger()
    load_config()

    logger.info("P003 WordPress解析を開始します。")
    analysis = load_wordpress_analysis()
    if analysis.error:
        logger.error("P003 WordPress解析で問題が発生しました: %s", analysis.error)
    else:
        logger.info(
            "P003 WordPress解析に成功しました: site=%s posts=%s",
            analysis.site_url,
            len(analysis.posts),
        )

    report = build_wordpress_report(analysis)
    local_report = (
        Path(__file__).resolve().parent
        / "01_グラビア事業部"
        / "P003_グラビア事業部"
        / "REPORT.md"
    )
    local_report.write_text(report.rstrip() + "\n", encoding="utf-8")
    try:
        result = save_report("P003", "REPORT.md", report)
    except Exception as exc:
        result = {"backend": "local", "error": str(exc)}
        logger.error("P003 REPORTのGoogle Drive保存に失敗しました。ローカルREPORTは保存済みです: %s", exc)
    logger.info("P003 REPORTを保存しました: %s", result)
    logger.info("P003 local REPORTを更新しました: %s", local_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

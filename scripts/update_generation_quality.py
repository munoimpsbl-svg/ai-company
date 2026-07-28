from __future__ import annotations

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.generation_quality import update_generation_quality


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update image generation quality SQLite DB and report."
    )
    parser.add_argument(
        "--date",
        dest="output_date",
        default=None,
        help="Limit scan to 02_Daily_Output/YYYY-MM-DD.",
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parents[1]
    summary = update_generation_quality(
        workspace_root=workspace_root,
        output_date=args.output_date,
    )

    print(f"GENERATION_QUALITY_DB: {summary.db_path}")
    print(f"GENERATION_QUALITY_REPORT: {summary.report_path}")
    print(f"SCANNED_ASSETS: {summary.scanned_assets}")
    print(f"EXPERIMENTS: {summary.experiments}")
    print(f"AVERAGE_SCORE: {summary.average_score}")
    if summary.blockers:
        print("BLOCKERS:")
        for blocker in summary.blockers:
            print(f"- {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

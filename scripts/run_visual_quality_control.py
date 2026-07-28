from __future__ import annotations

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.visual_quality_control import run_visual_quality_control


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run AI-VQC visual quality control for daily output images."
    )
    parser.add_argument("--date", required=True, help="Target date: YYYY-MM-DD")
    parser.add_argument(
        "--character",
        default="MIKU",
        choices=("MIKU", "RIO"),
        help="Target character.",
    )
    parser.add_argument(
        "--slot",
        default=None,
        help="Optional scene folder under the character folder.",
    )
    parser.add_argument(
        "--minimum-pass",
        type=int,
        default=3,
        help="Minimum PASS images required for post preparation.",
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Write reports only; do not copy images into pass/review/fail folders.",
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parents[1]
    summary = run_visual_quality_control(
        workspace_root=workspace_root,
        output_date=args.date,
        character=args.character,
        slot=args.slot,
        minimum_pass_required=args.minimum_pass,
        copy_images=not args.no_copy,
    )

    print(f"AI_VQC_SOURCE: {summary.source_dir}")
    print(f"TOTAL_IMAGES: {summary.total_images}")
    print(f"PASS: {summary.pass_count}")
    print(f"REVIEW: {summary.review_count}")
    print(f"FAIL: {summary.fail_count}")
    print(f"READY_FOR_POST_PREPARATION: {summary.ready_for_post_preparation}")
    if not summary.ready_for_post_preparation:
        print("CEO_CONFIRMATION_REQUIRED: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

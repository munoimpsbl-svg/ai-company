from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.sns_daily_brief import generate_sns_daily_brief


def main() -> int:
    project_root = Path(__file__).resolve().parent
    try:
        output_path = generate_sns_daily_brief(project_root)
        print(f"DAILY_BRIEF saved: {output_path}")
        return 0
    except Exception as exc:
        output_path = project_root / "04_Daily" / "DAILY_BRIEF.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            f"# Daily Brief\n\n## Blocker\n\n{exc}\n",
            encoding="utf-8",
        )
        print(f"DAILY_BRIEF saved with error: {output_path}")
        print(f"Error: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

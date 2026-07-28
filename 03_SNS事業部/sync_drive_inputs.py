from pathlib import Path
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from core.sns_drive_input import DRIVE_INPUT_LABEL, result_path, sync_drive_inputs


def main() -> int:
    result = sync_drive_inputs(WORKSPACE_ROOT)
    print(f"Drive input folder: {DRIVE_INPUT_LABEL}")
    print(f"Downloaded CSV: {sum(1 for item in result['rows'] if item['success'])}")
    if result["error"]:
        print(f"Error: {result['error']}")
    print(f"Result saved: {result_path(WORKSPACE_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

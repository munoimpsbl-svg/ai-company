from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.sns_report import build_sns_report, save_sns_report
from core.today_post import build_today_post, save_today_post


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    _sync_drive_inputs(workspace_root)
    try:
        report = build_sns_report(workspace_root)
        report_path = save_sns_report(workspace_root, report)
        print(f"SNS_REPORT saved: {report_path}")
    except Exception as exc:
        fallback = f"""# SNS REPORT

日付

未取得

---

## Blocker

・{exc}

---

## 制約確認

・SNS投稿: 未実行

・画像生成: 未実行

・WordPress更新: 未実行

・解析のみ: OK
"""
        report_path = save_sns_report(workspace_root, fallback)
        print(f"SNS_REPORT saved with error: {report_path}")
        print(f"Error: {exc}")

    try:
        today_post = build_today_post(workspace_root)
        today_post_path = save_today_post(workspace_root, today_post)
        print(f"TODAY_POST saved: {today_post_path}")
    except Exception as exc:
        fallback = f"""# TODAY POST

日付

未取得

## Blocker

- {exc}

## 制約確認

- 自動投稿: 未実行
- SNSログイン操作: 未実行
- ファイル削除: 未実行
- 表示と投稿補助のみ
"""
        today_post_path = save_today_post(workspace_root, fallback)
        print(f"TODAY_POST saved with error: {today_post_path}")
        print(f"Error: {exc}")
    return 0


def _sync_drive_inputs(workspace_root: Path) -> None:
    script = workspace_root / "03_SNS事業部" / "sync_drive_inputs.py"
    try:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(workspace_root),
            text=True,
            capture_output=True,
            timeout=120,
        )
        if completed.stdout.strip():
            print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip())
        if completed.returncode != 0:
            print(f"Drive input sync exited with {completed.returncode}")
    except Exception as exc:
        print(f"Drive input sync skipped: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.today_post import build_today_post, save_today_post


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    try:
        content = build_today_post(workspace_root)
        output_path = save_today_post(workspace_root, content)
        print(f"TODAY_POST saved: {output_path}")
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
        output_path = save_today_post(workspace_root, fallback)
        print(f"TODAY_POST saved with error: {output_path}")
        print(f"Error: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

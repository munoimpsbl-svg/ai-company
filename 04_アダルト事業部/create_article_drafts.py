import argparse
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from core.article_queue import create_drafts_from_queue
from core.wordpress_writer import WordPressWriteClient, load_env


def main() -> int:
    parser = argparse.ArgumentParser(description="Create P004 WordPress draft posts from ARTICLE_QUEUE.md")
    parser.add_argument("--dry-run", action="store_true", help="Validate queue without creating drafts")
    args = parser.parse_args()

    load_env(WORKSPACE_ROOT / ".env")
    try:
        client = WordPressWriteClient.from_env("P004_WORDPRESS_URL", fallback_site_url_env="P003_WORDPRESS_URL")
        client.verify_auth()
        result_path = create_drafts_from_queue(
            "P004 アダルト事業部",
            PROJECT_DIR,
            client,
            dry_run=args.dry_run,
        )
        print(f"ARTICLE_DRAFT_RESULT saved: {result_path}")
        return 0
    except Exception as exc:
        result_path = PROJECT_DIR / "ARTICLE_DRAFT_RESULT.md"
        result_path.write_text(
            "# ARTICLE DRAFT RESULT\n\n"
            f"- Project: P004 アダルト事業部\n"
            f"- Status: FAILED\n"
            f"- Error: {exc}\n\n"
            "## Safety\n\n"
            "- 公開は行っていない。\n"
            "- 既存記事の更新は行っていない。\n"
            "- 削除は行っていない。\n",
            encoding="utf-8",
        )
        print(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

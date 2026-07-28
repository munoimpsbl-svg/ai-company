from datetime import date
from pathlib import Path
import os
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.config import load_config
from core.wordpress import load_wordpress_analysis


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_DIR / "REPORT.md"

ADULT_SIGNALS = (
    "アダルト",
    "成人向け",
    "adult",
    "r18",
    "r-18",
    "18禁",
    "fanza",
    "dlsite",
    "同人",
)


def main() -> int:
    load_config()
    site_url = os.getenv("P004_WORDPRESS_URL") or os.getenv("P003_WORDPRESS_URL")
    analysis = load_wordpress_analysis(site_url=site_url, posts_limit=50)
    report = build_report(analysis)
    REPORT_PATH.write_text(report.rstrip() + "\n", encoding="utf-8")
    print(f"P004 REPORT saved: {REPORT_PATH}")
    return 0


def build_report(analysis) -> str:
    adult_posts = [
        post for post in analysis.posts if _has_direct_adult_signal(post.title, post.categories, post.tags)
    ]
    review_posts = [
        post
        for post in analysis.posts
        if post not in adult_posts and _has_excerpt_adult_signal(post.excerpt)
    ]
    blockers = []
    if analysis.error:
        blockers.append(f"WordPress取得エラー: {analysis.error}")
    if not adult_posts:
        blockers.append("アダルト対象記事を直接判定できるカテゴリ・タグ・タイトルが未取得。")

    return f"""# P004 ADULT REPORT

日付

{date.today().isoformat()}

---

## Executive Summary

- 目的: アダルト事業部のSEO / CTR / 回遊改善に必要な現状把握を行う。
- WordPress接続: {analysis.status}
- 取得記事数: {len(analysis.posts)}件
- アダルト候補記事数: {len(adult_posts)}件
- 要確認候補数: {len(review_posts)}件
- WordPress更新: 未実行
- 投稿: 未実行
- 削除: 未実行
- 推測: 禁止

---

## アダルト候補記事一覧

{_format_posts(adult_posts)}

---

## 要確認候補

{_format_review_posts(review_posts)}

---

## カテゴリ確認

{_format_list(analysis.categories)}

---

## タグ確認

{_format_list(analysis.tags)}

---

## 改善候補

{_build_improvement_candidates(adult_posts)}

---

## Blocker

{_format_blockers(blockers)}

---

## Tomorrow Task

- アダルト領域の専用カテゴリ・タグ設計を確認する。
- 対象記事が存在する場合、タイトル / メタディスクリプション / 内部リンク改善案を作る。
- 対象記事が存在しない場合、サイト方針に沿って新規作成の是非を編集長が判断する。

---

## 制約確認

- WordPress更新: 未実行
- WordPress投稿: 未実行
- WordPress削除: 未実行
- SNS投稿: 未実行
- 解析のみ
"""


def _has_adult_signal(title: str, categories, tags, excerpt: str) -> bool:
    text = " ".join([title or "", excerpt or "", " ".join(categories or []), " ".join(tags or [])]).lower()
    return any(signal.lower() in text for signal in ADULT_SIGNALS)


def _has_direct_adult_signal(title: str, categories, tags) -> bool:
    text = " ".join([title or "", " ".join(categories or []), " ".join(tags or [])]).lower()
    return any(signal.lower() in text for signal in ADULT_SIGNALS)


def _has_excerpt_adult_signal(excerpt: str) -> bool:
    text = (excerpt or "").lower()
    return any(signal.lower() in text for signal in ADULT_SIGNALS)


def _format_posts(posts) -> str:
    if not posts:
        return "未取得。"
    lines = []
    for post in posts:
        lines.extend(
            [
                f"### {post.title or '無題'}",
                "",
                f"- ID: {post.post_id}",
                f"- URL: {post.link or '未取得'}",
                f"- 公開日: {post.date or '未取得'}",
                f"- カテゴリ: {', '.join(post.categories) if post.categories else '未取得'}",
                f"- タグ: {', '.join(post.tags) if post.tags else '未取得'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _format_review_posts(posts) -> str:
    if not posts:
        return "未取得。"
    lines = []
    for post in posts:
        lines.extend(
            [
                f"### {post.title or '無題'}",
                "",
                f"- ID: {post.post_id}",
                f"- URL: {post.link or '未取得'}",
                f"- 判定: 抜粋内に対象語があるが、タイトル・カテゴリ・タグでは直接判定できないため要確認。",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _format_list(items) -> str:
    if not items:
        return "- 未取得"
    return "\n".join(f"- {item}" for item in items)


def _build_improvement_candidates(posts) -> str:
    if not posts:
        return "\n".join(
            [
                "- アダルト専用カテゴリの有無を確認する。",
                "- アダルト対象記事を判定できるタグ命名を統一する。",
                "- 対象記事が確認できるまで、WordPress更新は行わない。",
            ]
        )
    return "\n".join(
        [
            "- 対象記事のタイトル改善案を作る。",
            "- 対象記事のメタディスクリプション改善案を作る。",
            "- 関連記事・カテゴリページへの内部リンク改善案を作る。",
        ]
    )


def _format_blockers(blockers) -> str:
    if not blockers:
        return "- なし。"
    return "\n".join(f"- {blocker}" for blocker in blockers)


if __name__ == "__main__":
    raise SystemExit(main())

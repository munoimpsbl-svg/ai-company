import html
import json
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class WordPressError(RuntimeError):
    pass


@dataclass(frozen=True)
class WordPressPost:
    post_id: int
    title: str
    link: str
    date: str
    status: str
    categories: List[str]
    tags: List[str]
    excerpt: str


@dataclass(frozen=True)
class WordPressAnalysis:
    site_url: Optional[str]
    site_name: str
    status: str
    posts: List[WordPressPost]
    categories: List[str]
    tags: List[str]
    error: Optional[str] = None


def load_wordpress_analysis(
    site_url: Optional[str] = None,
    posts_limit: int = 20,
) -> WordPressAnalysis:
    resolved_site_url = (site_url or os.getenv("P003_WORDPRESS_URL") or "").strip()
    if not resolved_site_url:
        return WordPressAnalysis(
            site_url=None,
            site_name="未設定",
            status="未接続",
            posts=[],
            categories=[],
            tags=[],
            error="P003_WORDPRESS_URL が未設定です。",
        )

    try:
        site_info = _get_json(resolved_site_url, "/wp-json")
        categories = _load_terms(resolved_site_url, "categories")
        tags = _load_terms(resolved_site_url, "tags")
        posts = _load_posts(resolved_site_url, posts_limit, categories, tags)
        return WordPressAnalysis(
            site_url=resolved_site_url,
            site_name=site_info.get("name") or resolved_site_url,
            status="接続済み",
            posts=posts,
            categories=[term["name"] for term in categories.values()],
            tags=[term["name"] for term in tags.values()],
        )
    except WordPressError as exc:
        return WordPressAnalysis(
            site_url=resolved_site_url,
            site_name=resolved_site_url,
            status="取得失敗",
            posts=[],
            categories=[],
            tags=[],
            error=str(exc),
        )


def build_wordpress_report(analysis: WordPressAnalysis) -> str:
    report_date = date.today().isoformat()
    posts_text = _format_major_posts(analysis.posts)
    categories_text = _format_trends(_count_terms(post.categories for post in analysis.posts))
    tags_text = _format_trends(_count_terms(post.tags for post in analysis.posts))
    improvement_candidates = _format_improvement_candidates(analysis)
    internal_link_candidates = _format_internal_link_candidates(analysis.posts)
    blocker = _format_blocker(analysis)

    return f"""# REPORT

## 実行日

{report_date}

## Executive Summary

P003 TASK-004として、既存WordPressサイトの読み取り専用解析を実行した。

WordPressへの書き込み、投稿、更新は行っていない。

- 接続状況: {analysis.status}
- 取得記事数: {len(analysis.posts)}件
- カテゴリ数: {len(analysis.categories)}件
- タグ数: {len(analysis.tags)}件
- 保存: P001 Core Platform `save_report()` を使用

## 接続状況

- Site URL: {analysis.site_url or "未設定"}
- Site Name: {analysis.site_name}
- Status: {analysis.status}
- Error: {analysis.error or "なし"}

## 取得記事数

- 記事一覧取得: {len(analysis.posts)}件
- タイトル取得: {"OK" if analysis.posts else "未取得"}
- URL取得: {"OK" if analysis.posts else "未取得"}
- 公開日取得: {"OK" if analysis.posts else "未取得"}
- カテゴリ取得: {len(analysis.categories)}件
- タグ取得: {len(analysis.tags)}件
- 抜粋取得: {_count_available_excerpts(analysis.posts)}件

## 主要記事一覧

{posts_text}

## カテゴリ傾向

{categories_text}

## タグ傾向

{tags_text}

## 内部リンク候補

{internal_link_candidates}

## 改善候補

{improvement_candidates}

## Blocker

{blocker}

## Tomorrow Task

- TASK-005 SEO改善提案へ進む。
- 取得済み記事のタイトル、抜粋、カテゴリ、タグをもとにSEO改善候補を抽出する。
- Search Console未接続の場合、CTR改善は未取得として扱う。

## 禁止事項確認

- WordPress書き込み: 未実行
- 投稿: 未実行
- 更新: 未実行
- 削除: 未実行
"""


def _load_terms(site_url: str, taxonomy: str) -> Dict[int, Dict[str, str]]:
    terms = _get_json(
        site_url,
        f"/wp-json/wp/v2/{taxonomy}",
        {"per_page": "100", "hide_empty": "false"},
    )
    if not isinstance(terms, list):
        raise WordPressError(f"{taxonomy} の取得結果が不正です。")

    return {
        int(term["id"]): {"name": _clean_text(term.get("name", ""))}
        for term in terms
        if "id" in term
    }


def _load_posts(
    site_url: str,
    posts_limit: int,
    categories: Dict[int, Dict[str, str]],
    tags: Dict[int, Dict[str, str]],
) -> List[WordPressPost]:
    posts = _get_json(
        site_url,
        "/wp-json/wp/v2/posts",
        {
            "per_page": str(max(1, min(posts_limit, 100))),
            "orderby": "date",
            "order": "desc",
            "status": "publish",
        },
    )
    if not isinstance(posts, list):
        raise WordPressError("posts の取得結果が不正です。")

    return [
        WordPressPost(
            post_id=int(post["id"]),
            title=_clean_text(post.get("title", {}).get("rendered", "")),
            link=post.get("link", ""),
            date=post.get("date", ""),
            status=post.get("status", ""),
            categories=[
                categories[category_id]["name"]
                for category_id in post.get("categories", [])
                if category_id in categories
            ],
            tags=[
                tags[tag_id]["name"]
                for tag_id in post.get("tags", [])
                if tag_id in tags
            ],
            excerpt=_clean_text(post.get("excerpt", {}).get("rendered", "")),
        )
        for post in posts
        if "id" in post
    ]


def _get_json(
    site_url: str,
    path: str,
    params: Optional[Dict[str, str]] = None,
) -> object:
    url = urljoin(site_url.rstrip("/") + "/", path.lstrip("/"))
    if params:
        url = f"{url}?{urlencode(params)}"

    request = Request(url, headers={"User-Agent": "AI-COMPANY-P003/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return json.loads(response.read().decode(charset))
    except HTTPError as exc:
        raise WordPressError(f"WordPress API HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise WordPressError(f"WordPress API connection error: {exc.reason}") from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise WordPressError(f"WordPress API parse error: {exc}") from exc


def _format_major_posts(posts: List[WordPressPost]) -> str:
    if not posts:
        return "未取得。"

    lines = []
    for post in posts:
        categories = ", ".join(post.categories) if post.categories else "未取得"
        tags = ", ".join(post.tags) if post.tags else "未取得"
        excerpt = post.excerpt or "未取得"
        lines.extend(
            [
                f"### {post.title or '無題'}",
                "",
                f"- ID: {post.post_id}",
                f"- URL: {post.link or '未取得'}",
                f"- 公開日: {post.date or '未取得'}",
                f"- Status: {post.status}",
                f"- カテゴリ: {categories}",
                f"- Tags: {tags}",
                f"- 抜粋: {excerpt}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def _format_names(names: List[str]) -> str:
    if not names:
        return "未取得。"

    return "\n".join(f"- {name}" for name in names)


def _count_terms(term_groups: Iterable[List[str]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for terms in term_groups:
        for term in terms:
            counts[term] = counts.get(term, 0) + 1
    return counts


def _format_trends(counts: Dict[str, int]) -> str:
    if not counts:
        return "未取得。"

    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return "\n".join(f"- {name}: {count}件" for name, count in sorted_counts[:20])


def _format_internal_link_candidates(posts: List[WordPressPost]) -> str:
    candidates = _build_internal_link_candidates(posts)
    if not candidates:
        return "未取得。"

    lines = []
    for source, target, reason in candidates:
        lines.extend(
            [
                f"- From: {source.title or '無題'}",
                f"  To: {target.title or '無題'}",
                f"  Reason: {reason}",
            ]
        )
    return "\n".join(lines)


def _build_internal_link_candidates(
    posts: List[WordPressPost],
) -> List[Tuple[WordPressPost, WordPressPost, str]]:
    candidates: List[Tuple[WordPressPost, WordPressPost, str]] = []
    for source in posts:
        for target in posts:
            if source.post_id == target.post_id:
                continue

            shared_categories = sorted(set(source.categories) & set(target.categories))
            shared_tags = sorted(set(source.tags) & set(target.tags))
            if not shared_categories and not shared_tags:
                continue

            reasons = []
            if shared_categories:
                reasons.append(f"共通カテゴリ: {', '.join(shared_categories)}")
            if shared_tags:
                reasons.append(f"共通タグ: {', '.join(shared_tags[:5])}")
            candidates.append((source, target, " / ".join(reasons)))
            break

        if len(candidates) >= 10:
            break

    return candidates


def _format_improvement_candidates(analysis: WordPressAnalysis) -> str:
    if not analysis.posts:
        return "- 未取得。WordPress記事一覧取得後に作成する。"

    lines = []
    missing_excerpt = [post for post in analysis.posts if not post.excerpt]
    missing_terms = [
        post for post in analysis.posts if not post.categories and not post.tags
    ]

    if missing_excerpt:
        lines.append(f"- 抜粋未取得または空の記事: {len(missing_excerpt)}件")
    if missing_terms:
        lines.append(f"- カテゴリ/タグ未取得の記事: {len(missing_terms)}件")
    if not _build_internal_link_candidates(analysis.posts):
        lines.append("- 内部リンク候補: 未取得。共通カテゴリまたは共通タグが不足。")

    if not lines:
        lines.append("- TASK-005でSEO改善提案を作成可能。")

    return "\n".join(lines)


def _format_blocker(analysis: WordPressAnalysis) -> str:
    blockers = []
    if analysis.error:
        blockers.append(f"- {analysis.error}")
    if not analysis.posts:
        blockers.append("- 記事一覧が未取得。")
    if not analysis.categories:
        blockers.append("- カテゴリが未取得。")
    if not analysis.tags:
        blockers.append("- タグが未取得。")

    return "\n".join(blockers) if blockers else "- なし。"


def _count_available_excerpts(posts: List[WordPressPost]) -> int:
    return sum(1 for post in posts if post.excerpt)


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(text).strip()

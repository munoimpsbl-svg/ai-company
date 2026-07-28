from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class SocialPost:
    platform: str
    post_id: str
    title: str
    impressions: Optional[int]
    likes: Optional[int]
    comments: Optional[int]
    shares: Optional[int]

    @property
    def engagement(self) -> Optional[int]:
        values = (self.likes, self.comments, self.shares)
        if any(value is None for value in values):
            return None
        return sum(value or 0 for value in values)


@dataclass(frozen=True)
class SocialAccount:
    platform: str
    posts_count: Optional[int]
    followers_count: Optional[int]
    posts: List[SocialPost]
    source: str


def load_dummy_social_data() -> List[SocialAccount]:
    return [
        SocialAccount(
            platform="Instagram",
            posts_count=3,
            followers_count=1200,
            source="dummy",
            posts=[
                SocialPost("Instagram", "ig_dummy_001", "朝の投稿", 3200, 180, 12, 8),
                SocialPost("Instagram", "ig_dummy_002", "写真集紹介", 4100, 260, 18, 15),
                SocialPost("Instagram", "ig_dummy_003", "日常投稿", 1800, 90, 5, 3),
            ],
        ),
        SocialAccount(
            platform="X",
            posts_count=3,
            followers_count=850,
            source="dummy",
            posts=[
                SocialPost("X", "x_dummy_001", "更新告知", 2200, 80, 6, 20),
                SocialPost("X", "x_dummy_002", "写真集導線", 3600, 140, 11, 42),
                SocialPost("X", "x_dummy_003", "雑談投稿", 900, 30, 3, 5),
            ],
        ),
    ]


def build_sns_report(accounts: List[SocialAccount], output_date: Optional[date] = None) -> str:
    current_date = output_date or date.today()
    blocker = _build_blocker(accounts)

    return f"""# P002 SNS事業部 REPORT

## 実行日

{current_date.isoformat()}

## Executive Summary

SNS分析AI Sprint1を実行した。

現時点ではInstagram / Xの実APIは未接続のため、ダミーデータを使用してREPORT.md生成フローを確認した。

推測は禁止。ダミーデータはダミーとして明記する。

## 投稿数

{_format_posts_count(accounts)}

## フォロワー数

{_format_followers_count(accounts)}

## エンゲージメント

{_format_engagement(accounts)}

## 伸びた投稿

{_format_top_posts(accounts)}

## 改善候補

{_format_improvement_candidates(accounts)}

## Blocker

{blocker}

## 制約確認

- 投稿: 未実行
- 更新: 未実行
- 削除: 未実行
- 分析のみ: OK
"""


def save_report(report_path: Path, content: str) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return report_path


def _format_posts_count(accounts: List[SocialAccount]) -> str:
    return "\n".join(
        f"- {account.platform}: {_value_or_unknown(account.posts_count)}件"
        for account in accounts
    )


def _format_followers_count(accounts: List[SocialAccount]) -> str:
    return "\n".join(
        f"- {account.platform}: {_value_or_unknown(account.followers_count)}"
        for account in accounts
    )


def _format_engagement(accounts: List[SocialAccount]) -> str:
    lines = []
    for account in accounts:
        engagement = sum(
            post.engagement for post in account.posts if post.engagement is not None
        )
        lines.append(f"- {account.platform}: {engagement}")
    return "\n".join(lines)


def _format_top_posts(accounts: List[SocialAccount]) -> str:
    posts = [post for account in accounts for post in account.posts]
    ranked_posts = sorted(
        posts,
        key=lambda post: (
            post.engagement if post.engagement is not None else -1,
            post.impressions if post.impressions is not None else -1,
        ),
        reverse=True,
    )
    if not ranked_posts:
        return "未取得。"

    lines = []
    for post in ranked_posts[:3]:
        lines.extend(
            [
                f"- {post.platform}: {post.title}",
                f"  - Post ID: {post.post_id}",
                f"  - Impressions: {_value_or_unknown(post.impressions)}",
                f"  - Engagement: {_value_or_unknown(post.engagement)}",
            ]
        )
    return "\n".join(lines)


def _format_improvement_candidates(accounts: List[SocialAccount]) -> str:
    if not accounts:
        return "- 未取得。"

    return "\n".join(
        [
            "- 実API接続後、投稿別のCTR、保存数、プロフィール遷移を取得する。",
            "- 伸びた投稿のテーマを分類し、次回投稿案へ反映する。",
            "- InstagramとXで同じ写真集導線投稿の反応差を比較する。",
        ]
    )


def _build_blocker(accounts: List[SocialAccount]) -> str:
    blockers = []
    for account in accounts:
        if account.source == "dummy":
            blockers.append(f"- {account.platform}: 実API未接続。現在はダミーデータ。")
    return "\n".join(blockers) if blockers else "- なし。"


def _value_or_unknown(value: Optional[int]) -> str:
    return str(value) if value is not None else "未取得"

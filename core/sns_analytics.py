from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class SocialPlatform(str, Enum):
    X = "X"
    THREADS = "Threads"


@dataclass(frozen=True)
class AnalysisTarget:
    character: str
    platform: SocialPlatform


@dataclass(frozen=True)
class SnsPostMetric:
    date: str
    post_id: str
    text: str
    url: str
    impressions: int
    engagements: int
    likes: int
    replies: int
    reposts: int
    bookmarks: int
    profile_clicks: int
    link_clicks: int
    followers: int
    followers_delta: int


@dataclass(frozen=True)
class SnsAnalysis:
    target: AnalysisTarget
    status: str
    source_dir: Path
    source_files: tuple[Path, ...]
    posts: tuple[SnsPostMetric, ...]
    blockers: tuple[str, ...]
    totals: dict[str, float]
    best_post: SnsPostMetric | None


MIKU_X_TARGET = AnalysisTarget("MIKU", SocialPlatform.X)
SUPPORTED_TARGETS = (MIKU_X_TARGET,)

_HEADER_ALIASES = {
    "date": ("date", "日付", "投稿日", "投稿日時"),
    "post_id": ("post_id", "id", "tweet_id", "ポストid", "投稿id"),
    "text": ("text", "本文", "投稿文", "post_text", "tweet_text"),
    "url": ("url", "投稿url", "post_url", "tweet_url"),
    "impressions": ("impressions", "インプレッション", "表示回数"),
    "engagements": ("engagements", "engagement", "エンゲージメント", "反応数"),
    "likes": ("likes", "like", "いいね"),
    "replies": ("replies", "reply", "返信", "コメント"),
    "reposts": ("reposts", "retweets", "retweet", "リポスト", "リツイート"),
    "bookmarks": ("bookmarks", "bookmark", "ブックマーク"),
    "profile_clicks": ("profile_clicks", "profile_click", "プロフィールクリック"),
    "link_clicks": ("link_clicks", "url_clicks", "リンククリック", "クリック"),
    "followers": ("followers", "フォロワー", "フォロワー数"),
    "followers_delta": ("followers_delta", "フォロワー増減", "新規フォロワー"),
}


def analyze_sns_target(
    workspace_root: Path,
    target: AnalysisTarget = MIKU_X_TARGET,
) -> SnsAnalysis:
    if target not in SUPPORTED_TARGETS:
        return _empty_analysis(
            workspace_root,
            target,
            "未対応",
            (f"{target.character}/{target.platform.value} は現段階の分析対象外です。",),
        )

    source_dir = _source_dir(workspace_root, target)
    manifest = _load_drive_manifest(workspace_root, target)
    if not manifest:
        return _empty_analysis(
            workspace_root,
            target,
            "未取得",
            ("Google Drive同期manifestがありません。`03_SNS事業部/main.py`を実行してDrive入力を同期してください。",),
        )

    if not manifest.get("success", False):
        return _empty_analysis(
            workspace_root,
            target,
            "Drive同期失敗",
            (f"Google Drive入力同期に失敗しています: {manifest.get('error') or '未取得'}",),
        )

    source_files = tuple(_manifest_csv_paths(workspace_root, manifest))
    if not source_files:
        return _empty_analysis(
            workspace_root,
            target,
            "未取得",
            (f"Google Drive入力フォルダにCSVがありません: {manifest.get('google_drive_folder', '未取得')}",),
        )

    posts = tuple(_read_metric_files(source_files))
    blockers = []
    if not posts:
        blockers.append("CSVから有効な投稿指標を読み取れませんでした。")

    totals = _calculate_totals(posts)
    best_post = max(posts, key=_post_engagements, default=None)
    status = "正常" if posts else "未取得"

    return SnsAnalysis(
        target=target,
        status=status,
        source_dir=source_dir,
        source_files=source_files,
        posts=posts,
        blockers=tuple(blockers),
        totals=totals,
        best_post=best_post,
    )


def _empty_analysis(
    workspace_root: Path,
    target: AnalysisTarget,
    status: str,
    blockers: tuple[str, ...],
) -> SnsAnalysis:
    return SnsAnalysis(
        target=target,
        status=status,
        source_dir=_source_dir(workspace_root, target),
        source_files=(),
        posts=(),
        blockers=blockers,
        totals=_calculate_totals(()),
        best_post=None,
    )


def _source_dir(workspace_root: Path, target: AnalysisTarget) -> Path:
    return (
        workspace_root
        / "03_SNS事業部"
        / "03_Analytics"
        / target.character
        / target.platform.value
    )


def _manifest_path(workspace_root: Path, target: AnalysisTarget) -> Path:
    return workspace_root / "03_SNS事業部" / "03_Analytics" / "DRIVE_INPUT_MANIFEST.json"


def _load_drive_manifest(workspace_root: Path, target: AnalysisTarget) -> dict:
    path = _manifest_path(workspace_root, target)
    if not path.exists():
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "success": False,
            "error": f"Drive manifestを読めません: {path}",
            "files": [],
        }
    if manifest.get("source_of_truth") != "google_drive":
        return {
            "success": False,
            "error": "Drive manifestのsource_of_truthがgoogle_driveではありません。",
            "files": [],
        }
    return manifest


def _manifest_csv_paths(workspace_root: Path, manifest: dict) -> Iterable[Path]:
    for row in manifest.get("files", []):
        if not row.get("success"):
            continue
        relative_path = row.get("local_path", "")
        if not relative_path:
            continue
        path = workspace_root / relative_path
        if path.exists() and path.suffix.lower() == ".csv":
            yield path


def _read_metric_files(paths: Iterable[Path]) -> Iterable[SnsPostMetric]:
    for path in paths:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    metric = _metric_from_row(row)
                    if metric:
                        yield metric
        except OSError:
            continue


def _metric_from_row(row: dict[str, str]) -> SnsPostMetric | None:
    normalized = {_normalize_key(key): value for key, value in row.items()}
    values = {
        field: _value_for(normalized, aliases)
        for field, aliases in _HEADER_ALIASES.items()
    }
    if not any(values.get(field) for field in ("post_id", "text", "url")):
        return None

    return SnsPostMetric(
        date=values["date"],
        post_id=values["post_id"],
        text=values["text"],
        url=values["url"],
        impressions=_number(values["impressions"]),
        engagements=_number(values["engagements"]),
        likes=_number(values["likes"]),
        replies=_number(values["replies"]),
        reposts=_number(values["reposts"]),
        bookmarks=_number(values["bookmarks"]),
        profile_clicks=_number(values["profile_clicks"]),
        link_clicks=_number(values["link_clicks"]),
        followers=_number(values["followers"]),
        followers_delta=_number(values["followers_delta"]),
    )


def _calculate_totals(posts: Iterable[SnsPostMetric]) -> dict[str, float]:
    post_list = tuple(posts)
    impressions = sum(post.impressions for post in post_list)
    engagements = sum(
        post.engagements
        or post.likes + post.replies + post.reposts + post.bookmarks
        for post in post_list
    )
    link_clicks = sum(post.link_clicks for post in post_list)
    followers = max((post.followers for post in post_list), default=0)
    followers_delta = sum(post.followers_delta for post in post_list)
    return {
        "posts": len(post_list),
        "followers": followers or followers_delta,
        "followers_delta": followers_delta,
        "impressions": impressions,
        "engagement": engagements,
        "engagement_rate": _rate(engagements, impressions),
        "likes": sum(post.likes for post in post_list),
        "replies": sum(post.replies for post in post_list),
        "reposts": sum(post.reposts for post in post_list),
        "bookmarks": sum(post.bookmarks for post in post_list),
        "profile_clicks": sum(post.profile_clicks for post in post_list),
        "link_clicks": link_clicks,
        "ctr": _rate(link_clicks, impressions),
    }


def _post_engagements(post: SnsPostMetric) -> int:
    return post.engagements or post.likes + post.replies + post.reposts + post.bookmarks


def _value_for(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        value = row.get(_normalize_key(alias), "")
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _normalize_key(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _number(value: str) -> int:
    clean = str(value or "").replace(",", "").replace("%", "").strip()
    if not clean:
        return 0
    try:
        return int(float(clean))
    except ValueError:
        return 0


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator * 100, 2)

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Dict, List, Optional


CHARACTERS = ("MIKU", "RIO")
PLATFORM_FILES = {
    "Instagram": "instagram.txt",
    "X": "x.txt",
    "Threads": "threads.txt",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class TodayPost:
    character: str
    slot: str
    theme: str
    image_folder: str
    images: List[str]
    post_texts: Dict[str, str]


def build_today_post(
    workspace_root: Path,
    output_date: Optional[date] = None,
) -> str:
    current_date = output_date or date.today()
    daily_dir = workspace_root / "02_Daily_Output" / current_date.isoformat()
    posts = collect_today_posts(workspace_root, current_date)

    lines = [
        "# TODAY POST",
        "",
        "日付",
        "",
        current_date.isoformat(),
        "",
        "---",
        "",
    ]
    for character in CHARACTERS:
        lines.extend([f"## {character}", ""])
        character_posts = [post for post in posts if post.character == character]
        if not character_posts:
            lines.extend(
                [
                    "### 未取得",
                    "",
                    "- キャラクター名: " + character,
                    "- 今日のテーマ: 未取得",
                    "- 採用画像フォルダ: 未取得",
                    "- 採用画像一覧:",
                    "  - 未取得",
                    "- Instagram投稿文",
                    "",
                    "未取得",
                    "",
                    "- X投稿文",
                    "",
                    "未取得",
                    "",
                    "- Threads投稿文",
                    "",
                    "未取得",
                    "",
                    "- 投稿先: 未取得",
                    "- 投稿チェック欄:",
                    "  - [ ] 未取得",
                    "",
                ]
            )
            continue
        for post in character_posts:
            lines.extend(_format_post(post))

    lines.extend(
        [
            "---",
            "",
            "## 制約確認",
            "",
            "- 自動投稿: 未実行",
            "- SNSログイン操作: 未実行",
            "- ファイル削除: 未実行",
            "- 表示と投稿補助のみ",
            "",
            "## Blocker",
            "",
            _format_blocker(daily_dir, posts),
            "",
        ]
    )
    return "\n".join(lines)


def collect_today_posts(workspace_root: Path, output_date: date) -> List[TodayPost]:
    daily_dir = workspace_root / "02_Daily_Output" / output_date.isoformat()
    posts = []
    for character in CHARACTERS:
        character_dir = daily_dir / character
        if not character_dir.exists():
            continue
        slot_dirs = sorted(
            (path for path in character_dir.iterdir() if path.is_dir()),
            key=_slot_sort_key,
        )
        if not slot_dirs and character_dir.exists():
            slot_dirs = [character_dir]
        for slot_dir in slot_dirs:
            post_texts = {}
            for platform, filename in PLATFORM_FILES.items():
                post_text = _read_optional(slot_dir / filename)
                if post_text:
                    post_texts[platform] = post_text
            images = _adopted_images(slot_dir, _read_optional(slot_dir / "report.md"))
            prompt = _read_optional(slot_dir / "prompt.txt")
            posts.append(
                TodayPost(
                    character=character,
                    slot=slot_dir.name if slot_dir != character_dir else "default",
                    theme=_extract_theme(prompt),
                    image_folder=_relative(slot_dir / "images", workspace_root),
                    images=[_relative(path, workspace_root) for path in images],
                    post_texts=post_texts,
                )
            )
    return posts


def save_today_post(workspace_root: Path, content: str) -> Path:
    output_path = workspace_root / "03_SNS事業部" / "04_Daily" / "TODAY_POST.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return output_path


def _format_post(post: TodayPost) -> List[str]:
    targets = list(post.post_texts)
    lines = [
        f"### {post.slot}",
        "",
        f"- キャラクター名: {post.character}",
        f"- 今日のテーマ: {post.theme}",
        f"- 採用画像フォルダ: `{post.image_folder}`",
        "- 採用画像一覧:",
    ]
    if post.images:
        lines.extend(f"  - `{image}`" for image in post.images)
    else:
        lines.append("  - 未取得")

    for platform in PLATFORM_FILES:
        lines.extend(
            [
                f"- {platform}投稿文",
                "",
                "```text",
                post.post_texts.get(platform, "未取得").strip() or "未取得",
                "```",
                "",
            ]
        )

    lines.append(f"- 投稿先: {', '.join(targets) if targets else '未取得'}")
    lines.append("- 投稿チェック欄:")
    if targets:
        lines.extend(f"  - [ ] {platform}" for platform in targets)
    else:
        lines.append("  - [ ] 未取得")
    lines.extend(["", "---", ""])
    return lines


def _adopted_images(slot_dir: Path, report_text: str) -> List[Path]:
    image_dir = slot_dir / "images"
    if not image_dir.exists():
        return []
    candidates = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    priority_ids = _extract_priority_ids(report_text)
    if not priority_ids:
        return []
    return [
        path
        for candidate_id in priority_ids
        for path in candidates
        if re.search(rf"_{re.escape(candidate_id)}$", path.stem)
    ]


def _extract_priority_ids(report_text: str) -> List[str]:
    for line in report_text.splitlines():
        if "優先候補:" in line:
            return re.findall(r"`(\d+)`", line)
    return []


def _extract_theme(prompt_text: str) -> str:
    in_daily_brief = False
    for line in prompt_text.splitlines():
        clean = line.strip()
        if clean == "## Daily Brief":
            in_daily_brief = True
            continue
        if in_daily_brief and clean.startswith("## "):
            break
        if in_daily_brief and clean.startswith("- "):
            value = clean[2:].strip()
            if not value.startswith("衣装:"):
                return value
    return "未取得"


def _format_blocker(daily_dir: Path, posts: List[TodayPost]) -> str:
    blockers = []
    if not daily_dir.exists():
        blockers.append("当日出力フォルダ未取得")
    for post in posts:
        label = f"{post.character}/{post.slot}"
        if post.theme == "未取得":
            blockers.append(f"{label}: 今日のテーマ未取得")
        if not post.images:
            blockers.append(f"{label}: 採用画像未取得")
        if not post.post_texts:
            blockers.append(f"{label}: 投稿文未取得")
    return "\n".join(f"- {blocker}" for blocker in blockers) if blockers else "なし"


def _slot_sort_key(path: Path):
    order = {"morning": 0, "afternoon": 1, "night": 2}
    return (order.get(path.name.lower(), 9), path.name)


def _relative(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _read_optional(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return ""

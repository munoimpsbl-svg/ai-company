from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


CHARACTERS = ("MIKU", "RIO")
POST_TARGET_FILES = {
    "Instagram": "instagram.txt",
    "X": "x.txt",
    "Threads": "threads.txt",
}


@dataclass(frozen=True)
class CharacterSnsResult:
    name: str
    generated_images: int
    adopted_images: List[str]
    post_targets: List[str]
    post_texts: Dict[str, str]
    blockers: List[str]


def build_sns_report(
    workspace_root: Path,
    output_date: Optional[date] = None,
) -> str:
    current_date = output_date or date.today()
    daily_output_dir = workspace_root / "02_Daily_Output" / current_date.isoformat()
    results = [
        analyze_character(daily_output_dir, character_name)
        for character_name in CHARACTERS
    ]

    return f"""# SNS REPORT

日付

{current_date.isoformat()}

---

## 投稿実績

・Instagram

{_format_platform_status(results, "Instagram")}

・X

{_format_platform_status(results, "X")}

・Threads

{_format_platform_status(results, "Threads")}

---

## キャラクター別実績

### MIKU

{_format_character(results[0])}

---

### RIO

{_format_character(results[1])}

---

## 本日の成果

・生成画像数

{sum(result.generated_images for result in results)}

・採用画像数

{sum(len(result.adopted_images) for result in results)}

・投稿数

{sum(len(result.post_targets) for result in results)}

---

## Blocker

{_format_blockers(results)}

---

## 明日の改善候補

・採用候補の最終判断を行う。

・投稿先ごとの文面差分を確認する。

・SNS実投稿データ接続後、反応率を03_Analyticsへ保存する。

---

## 制約確認

・SNS投稿: 未実行

・画像生成: 未実行

・WordPress更新: 未実行

・解析のみ: OK
"""


def analyze_character(
    daily_output_dir: Path,
    character_name: str,
) -> CharacterSnsResult:
    character_dir = daily_output_dir / character_name
    blockers = []
    if not character_dir.exists():
        return CharacterSnsResult(
            name=character_name,
            generated_images=0,
            adopted_images=[],
            post_targets=[],
            post_texts={},
            blockers=[f"{character_name}: 日次出力フォルダ未取得"],
        )

    generated_images = len(
        [
            path
            for path in character_dir.rglob("*.png")
            if path.is_file() and not _is_hidden_path(path)
        ]
    )
    report_text = _read_optional(character_dir / "report.md")
    adopted_images = _extract_adopted_images(report_text)
    post_texts = {
        platform: _read_optional(character_dir / filename)
        for platform, filename in POST_TARGET_FILES.items()
        if (character_dir / filename).exists()
    }
    post_targets = list(post_texts.keys())

    if not report_text:
        blockers.append(f"{character_name}: report.md未取得")
    if not adopted_images:
        blockers.append(f"{character_name}: 採用画像未確定")
    if not post_targets:
        blockers.append(f"{character_name}: 投稿文未取得")

    return CharacterSnsResult(
        name=character_name,
        generated_images=generated_images,
        adopted_images=adopted_images,
        post_targets=post_targets,
        post_texts=post_texts,
        blockers=blockers,
    )


def save_sns_report(workspace_root: Path, content: str) -> Path:
    report_path = workspace_root / "03_SNS事業部" / "SNS_REPORT.md"
    report_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return report_path


def _format_platform_status(
    results: List[CharacterSnsResult],
    platform: str,
) -> str:
    characters = [result.name for result in results if platform in result.post_targets]
    if not characters:
        return "未取得"
    return "投稿文あり: " + ", ".join(characters)


def _format_character(result: CharacterSnsResult) -> str:
    adopted = "\n".join(f"・{image}" for image in result.adopted_images) or "・未確定"
    targets = "\n".join(f"・{target}" for target in result.post_targets) or "・未取得"
    post_texts = _format_post_texts(result.post_texts)

    return f"""・生成画像枚数

{result.generated_images}

・採用画像

{adopted}

・投稿先

{targets}

・投稿文

{post_texts}"""


def _format_post_texts(post_texts: Dict[str, str]) -> str:
    if not post_texts:
        return "未取得"

    lines = []
    for platform, text in post_texts.items():
        preview = " ".join(text.strip().split())[:160] if text.strip() else "未取得"
        lines.append(f"・{platform}: {preview}")
    return "\n".join(lines)


def _format_blockers(results: List[CharacterSnsResult]) -> str:
    blockers = [blocker for result in results for blocker in result.blockers]
    return "\n".join(f"・{blocker}" for blocker in blockers) if blockers else "なし"


def _extract_adopted_images(report_text: str) -> List[str]:
    if not report_text:
        return []

    adopted = []
    current_image = None
    for line in report_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- `") and ".png`" in stripped:
            current_image = stripped.split("`", 2)[1]
            continue
        if current_image and "判定:" in stripped and "採用候補" in stripped:
            adopted.append(current_image)
            current_image = None
    return adopted


def _read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)

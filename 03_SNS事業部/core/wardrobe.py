from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional


CHARACTERS = ("MIKU", "RIO")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
REPORT_PATH = Path("03_SNS事業部") / "03_Analytics" / "WARDROBE_ROTATION_REPORT.md"

OUTFIT_RULES = (
    ("swimwear", "水着・海", ("水着", "swimsuit", "bikini", "海", "seaside", "beach")),
    ("gym_yoga", "ジム・ヨガ", ("ジム", "ヨガ", "gym", "yoga", "training", "workout")),
    ("roomwear", "部屋着", ("部屋着", "ルームウェア", "roomwear", "homewear", "pajama", "パジャマ")),
    ("office", "仕事服", ("仕事服", "通勤", "office", "blazer", "ジャケット", "ブラウス", "blouse")),
    ("outing", "外出服", ("外出", "登校", "shopping", "dinner", "cafe", "drive", "outing", "commute")),
    ("casual", "カジュアル", ("普段着", "Tシャツ", "t-shirt", "shortpants", "ショートパンツ", "casual")),
)

COLOR_RULES = (
    ("black", "黒", ("黒", "black")),
    ("white", "白", ("白", "white")),
    ("gray", "グレー", ("グレー", "gray", "grey")),
    ("navy", "ネイビー", ("ネイビー", "navy")),
    ("blue", "青・水色", ("青", "水色", "blue")),
    ("beige", "ベージュ", ("ベージュ", "beige")),
    ("red", "赤", ("赤", "red")),
)

ROTATION_ORDER = {
    "MIKU": ("office", "casual", "gym_yoga", "roomwear", "outing"),
    "RIO": ("outing", "roomwear", "gym_yoga", "casual", "swimwear"),
}


@dataclass(frozen=True)
class WardrobeSlot:
    date_label: str
    character: str
    slot: str
    outfit_key: str
    outfit_label: str
    source: str
    image_count: int
    confidence: str
    relative_dir: str


def build_wardrobe_report(
    workspace_root: Path,
    output_date: Optional[date] = None,
    lookback_days: int = 14,
) -> str:
    current_date = output_date or date.today()
    slots = collect_wardrobe_slots(workspace_root, current_date, lookback_days)
    today_slots = [slot for slot in slots if slot.date_label == current_date.isoformat()]
    blockers = _build_blockers(today_slots)

    lines = [
        "# WARDROBE ROTATION REPORT",
        "",
        "日付",
        "",
        current_date.isoformat(),
        "",
        "---",
        "",
        "## 現在の選定方法",
        "",
        "- `TODAY_POST.md`は各時間帯の`report.md`にある優先候補IDを採用画像として読む。",
        "- 服装タグ、前回使用衣装、日別ローテーションはこれまで採用判定に入っていなかった。",
        "- このレポートでは、prompt/report/status/フォルダ名から衣装カテゴリを読み取れる範囲だけ記録する。",
        "- 取得できない衣装は推測せず`未取得`とする。",
        "",
        "## 今日の衣装タグ",
        "",
        "| キャラクター | 枠 | 衣装タグ | 根拠 | 画像数 | 信頼度 |",
        "|---|---|---|---|---:|---|",
    ]
    if today_slots:
        lines.extend(_format_slot_row(slot) for slot in today_slots)
    else:
        lines.append("| 未取得 | 未取得 | 未取得 | 当日出力未取得 | 0 | 低 |")

    lines.extend(
        [
            "",
            "## 直近ローテーション",
            "",
            "| 日付 | キャラクター | 枠 | 衣装タグ | 画像数 |",
            "|---|---|---|---|---:|",
        ]
    )
    if slots:
        lines.extend(
            f"| {slot.date_label} | {slot.character} | {slot.slot} | {slot.outfit_label} | {slot.image_count} |"
            for slot in sorted(slots, key=lambda item: (item.date_label, item.character, item.slot), reverse=True)
        )
    else:
        lines.append("| 未取得 | 未取得 | 未取得 | 未取得 | 0 |")

    lines.extend(
        [
            "",
            "## 明日の衣装候補",
            "",
            "| キャラクター | 推奨衣装 | 理由 |",
            "|---|---|---|",
        ]
    )
    for character in CHARACTERS:
        recommendation = recommend_next_outfit(slots, character)
        lines.append(
            f"| {character} | {recommendation['label']} | {recommendation['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Blocker",
            "",
            _format_blockers(blockers),
            "",
            "## 制約確認",
            "",
            "- SNS投稿: 未実行",
            "- 画像生成: 未実行",
            "- ファイル削除: 未実行",
            "- 分析のみ: OK",
            "",
        ]
    )
    return "\n".join(lines)


def collect_wardrobe_slots(
    workspace_root: Path,
    output_date: date,
    lookback_days: int = 14,
) -> List[WardrobeSlot]:
    output_root = workspace_root / "02_Daily_Output"
    if not output_root.exists():
        return []

    start_date = output_date - timedelta(days=lookback_days - 1)
    slots = []
    for daily_dir in sorted(path for path in output_root.iterdir() if path.is_dir()):
        try:
            daily_date = date.fromisoformat(daily_dir.name)
        except ValueError:
            continue
        if not start_date <= daily_date <= output_date:
            continue
        for character in CHARACTERS:
            slots.extend(_collect_character_slots(workspace_root, daily_dir, character))
    return slots


def infer_slot_outfit(slot_dir: Path) -> Dict[str, str]:
    context_parts = [slot_dir.name.replace("_", " ")]
    for filename in ("prompt.txt", "report.md", "status.json"):
        context_parts.append(_read_optional(slot_dir / filename))
    context = "\n".join(part for part in context_parts if part)

    key, label = _match_outfit(context)
    colors = _match_colors(context)
    if key == "unknown":
        return {
            "key": "unknown",
            "label": "未取得",
            "source": _source_label(slot_dir, context),
            "confidence": "低",
        }

    color_suffix = f" / {'・'.join(colors)}" if colors else ""
    return {
        "key": "-".join([key] + colors) if colors else key,
        "label": f"{label}{color_suffix}",
        "source": _source_label(slot_dir, context),
        "confidence": "中" if colors else "低",
    }


def recommend_next_outfit(slots: Iterable[WardrobeSlot], character: str) -> Dict[str, str]:
    recent_keys = [
        slot.outfit_key.split("-", 1)[0]
        for slot in slots
        if slot.character == character and slot.outfit_key != "unknown"
    ]
    for key in ROTATION_ORDER.get(character, ()):
        if key not in recent_keys[-4:]:
            return {
                "label": _outfit_label(key),
                "reason": "直近4枠で使用が少ないため、見た目の単調さを減らせる。",
            }
    return {
        "label": "要確認",
        "reason": "直近衣装タグが不足、または候補が一巡しているため編集長確認が必要。",
    }


def save_wardrobe_report(workspace_root: Path, content: str) -> Path:
    output_path = workspace_root / REPORT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return output_path


def _collect_character_slots(
    workspace_root: Path,
    daily_dir: Path,
    character: str,
) -> List[WardrobeSlot]:
    character_dir = daily_dir / character
    if not character_dir.exists():
        return []
    slot_dirs = [path for path in character_dir.iterdir() if path.is_dir()]
    if _image_count(character_dir) and not slot_dirs:
        slot_dirs = [character_dir]

    slots = []
    for slot_dir in sorted(slot_dirs):
        image_count = _image_count(slot_dir)
        if image_count == 0:
            continue
        outfit = infer_slot_outfit(slot_dir)
        slots.append(
            WardrobeSlot(
                date_label=daily_dir.name,
                character=character,
                slot=slot_dir.name if slot_dir != character_dir else "default",
                outfit_key=outfit["key"],
                outfit_label=outfit["label"],
                source=outfit["source"],
                image_count=image_count,
                confidence=outfit["confidence"],
                relative_dir=_relative(slot_dir, workspace_root),
            )
        )
    return slots


def _match_outfit(context: str) -> tuple[str, str]:
    lower = context.lower()
    for key, label, keywords in OUTFIT_RULES:
        if any(_keyword_matches(lower, keyword) for keyword in keywords):
            return key, label
    return "unknown", "未取得"


def _match_colors(context: str) -> List[str]:
    lower = context.lower()
    matches = []
    for key, label, keywords in COLOR_RULES:
        if any(_keyword_matches(lower, keyword) for keyword in keywords):
            matches.append(key)
    return matches[:2]


def _keyword_matches(lower_text: str, keyword: str) -> bool:
    keyword_lower = keyword.lower()
    if re.fullmatch(r"[a-z][a-z0-9_-]*", keyword_lower):
        return re.search(rf"(?<![a-z0-9_-]){re.escape(keyword_lower)}(?![a-z0-9_-])", lower_text) is not None
    return keyword_lower in lower_text


def _outfit_label(key: str) -> str:
    for rule_key, label, _keywords in OUTFIT_RULES:
        if rule_key == key:
            return label
    return "要確認"


def _source_label(slot_dir: Path, context: str) -> str:
    sources = [
        filename
        for filename in ("prompt.txt", "report.md", "status.json")
        if (slot_dir / filename).exists()
    ]
    if sources:
        return ", ".join(sources)
    if context.strip():
        return "folder"
    return "未取得"


def _format_slot_row(slot: WardrobeSlot) -> str:
    return (
        f"| {slot.character} | {slot.slot} | {slot.outfit_label} | "
        f"{slot.source} | {slot.image_count} | {slot.confidence} |"
    )


def _build_blockers(today_slots: List[WardrobeSlot]) -> List[str]:
    blockers = []
    if not today_slots:
        blockers.append("当日のMIKU/RIO画像フォルダ未取得")
    for slot in today_slots:
        if slot.outfit_key == "unknown":
            blockers.append(f"{slot.character}/{slot.slot}: 衣装タグ未取得")
    return blockers


def _format_blockers(blockers: List[str]) -> str:
    return "\n".join(f"- {blocker}" for blocker in blockers) if blockers else "なし"


def _image_count(directory: Path) -> int:
    image_dir = directory / "images"
    target = image_dir if image_dir.exists() else directory
    return sum(
        1
        for path in target.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
        and not _is_rejected_image(path)
    )


def _is_rejected_image(path: Path) -> bool:
    return any(part.lower() in {"fail", "failed", "reject", "rejected"} for part in path.parts)


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

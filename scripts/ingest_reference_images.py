from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
DEFAULT_REFERENCE_ROOT = Path("/Volumes/music/写真集/AI_COMPANY_Reference")
SKIP_DIR_NAMES = {"_index", ".DS_Store"}


def resolve_finder_alias(path: Path) -> Path:
    path = path.expanduser()
    if path.exists() and path.is_dir():
        return path.resolve()
    if not path.exists():
        return path

    escaped = str(path).replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Finder"
    set aliasFile to (POSIX file "{escaped}") as alias
    set originalFile to original item of aliasFile
    return POSIX path of (originalFile as alias)
end tell
'''
    result = subprocess.run(
        ["osascript", "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return path.resolve()
    return Path(result.stdout.strip()).expanduser().resolve()


def iter_images(source: Path, recursive: bool) -> list[Path]:
    source = resolve_finder_alias(source)
    if source.is_file() and source.suffix.lower() in IMAGE_EXTENSIONS:
        return [source]
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source}")

    pattern: Iterable[Path] = source.rglob("*") if recursive else source.glob("*")
    images: list[Path] = []
    for path in pattern:
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path.resolve())
    return sorted(set(images), key=lambda p: str(p))


def read_image_info(path: Path) -> dict[str, object]:
    info: dict[str, object] = {
        "path": str(path),
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "bytes": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
        "width": None,
        "height": None,
        "preview_status": "pending",
        "notes": "",
    }
    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image)
            info["width"], info["height"] = image.size
            info["preview_status"] = "ok"
    except Exception as exc:  # HEIC may not be readable depending on local Pillow plugins.
        info["preview_status"] = f"preview_unavailable: {exc.__class__.__name__}"
    return info


def relative_group(source: Path, path: Path) -> tuple[str, str]:
    try:
        relative = path.relative_to(source)
    except ValueError:
        relative = Path(path.name)
    group = relative.parts[0] if len(relative.parts) > 1 else "."
    return group, str(relative)


def classify_path(path: Path, purpose: str, character: str) -> dict[str, str]:
    text = str(path).lower()
    inferred_purpose = purpose
    inferred_character = character
    if purpose == "auto":
        if "quality" in text or "texture" in text or "質感" in text or "画質" in text:
            inferred_purpose = "quality_texture"
        elif "composition" in text or "構図" in text:
            inferred_purpose = "composition"
        else:
            inferred_purpose = "mixed"
    if character == "auto":
        if "miku" in text or "ミク" in text:
            inferred_character = "MIKU"
        elif "rio" in text or "リオ" in text:
            inferred_character = "RIO"
        else:
            inferred_character = "common"
    return {"purpose": inferred_purpose, "character": inferred_character}


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1]}…"


def draw_missing_tile(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str) -> None:
    draw.rectangle([x, y, x + w, y + h], fill=(242, 242, 242), outline=(170, 170, 170))
    draw.text((x + 12, y + 12), title, fill=(40, 40, 40))
    draw.text((x + 12, y + 38), "preview unavailable", fill=(120, 40, 40))


def create_contact_sheets(records: list[dict[str, object]], out_dir: Path) -> list[str]:
    if not records:
        return []

    sheet_paths: list[str] = []
    columns = 5
    rows = 4
    per_sheet = columns * rows
    thumb_w = 220
    thumb_h = 220
    pad = 18
    label_h = 64
    cell_w = thumb_w + pad * 2
    cell_h = thumb_h + label_h + pad
    header_h = 62

    for sheet_index, start in enumerate(range(0, len(records), per_sheet), start=1):
        chunk = records[start : start + per_sheet]
        sheet = Image.new("RGB", (columns * cell_w, header_h + rows * cell_h), (250, 250, 250))
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 18), f"AI COMPANY reference contact sheet {sheet_index}", fill=(20, 20, 20))

        for idx, record in enumerate(chunk, start=start + 1):
            col = (idx - start - 1) % columns
            row = (idx - start - 1) // columns
            x = col * cell_w + pad
            y = header_h + row * cell_h + pad
            source = Path(str(record["path"]))

            try:
                with Image.open(source) as image:
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                    bg = Image.new("RGB", (thumb_w, thumb_h), (235, 235, 235))
                    bx = (thumb_w - image.width) // 2
                    by = (thumb_h - image.height) // 2
                    bg.paste(image, (bx, by))
                    sheet.paste(bg, (x, y))
                    draw.rectangle([x, y, x + thumb_w, y + thumb_h], outline=(180, 180, 180))
            except Exception:
                draw_missing_tile(draw, x, y, thumb_w, thumb_h, f"{idx:03d}")

            label_y = y + thumb_h + 8
            draw.text((x, label_y), f"{idx:03d}", fill=(0, 0, 0))
            draw.text((x + 38, label_y), fit_text(draw, str(record["file_name"]), 25), fill=(0, 0, 0))
            draw.text((x, label_y + 22), f"{record.get('width')}x{record.get('height')}", fill=(80, 80, 80))

        out_path = out_dir / f"CONTACT_SHEET_{sheet_index:03d}.jpg"
        sheet.save(out_path, quality=90, optimize=True)
        sheet_paths.append(str(out_path))
    return sheet_paths


def write_markdown(
    out_dir: Path,
    label: str,
    source: Path,
    records: list[dict[str, object]],
    contact_sheets: list[str],
) -> Path:
    path = out_dir / "REFERENCE_INDEX.md"
    ok_count = sum(1 for record in records if str(record["preview_status"]) == "ok")
    lines = [
        "# Reference Image Batch Index",
        "",
        f"- Label: {label}",
        f"- Source: `{source}`",
        f"- Image count: {len(records)}",
        f"- Preview OK: {ok_count}",
        "",
        "## How To Use",
        "",
        "- This batch is reference material only.",
        "- Use composition, camera angle, pose rhythm, light direction, texture, and mood.",
        "- Do not copy the reference person's face, hair, body, age, outfit, logo, location, brand names, or exact scene.",
        "- Character identity sheets and Daily Brief rules always override these references.",
        "- When generating a series, keep outfit, hair, phone color, bag, accessories, and time of day consistent within the same scene.",
        "",
        "## Folder Summary",
        "",
    ]
    group_counts: dict[str, int] = {}
    for record in records:
        group = str(record.get("group", "."))
        group_counts[group] = group_counts.get(group, 0) + 1
    for group, count in sorted(group_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {count:4d} images: `{group}`")

    lines.extend(
        [
            "",
            "## Contact Sheets",
            "",
        ]
    )
    for sheet in contact_sheets:
        lines.append(f"- `{sheet}`")
    lines.extend(["", "## Images", ""])
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"### {index:03d}. {record['file_name']}",
                f"- Path: `{record['path']}`",
                f"- Relative: `{record.get('relative_path', record['file_name'])}`",
                f"- Group: `{record.get('group', '.')}`",
                f"- Size: {record['width']} x {record['height']}",
                f"- Purpose: {record['purpose']}",
                f"- Character: {record['character']}",
                f"- Preview: {record['preview_status']}",
                "- Use: composition / angle / expression rhythm / light / texture only",
                "- Do not use: face / body / exact outfit / exact place / text / logo / brand",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_usage_note(out_dir: Path) -> Path:
    path = out_dir / "PROMPT_USAGE_NOTE.md"
    path.write_text(
        "\n".join(
            [
                "# Prompt Usage Note",
                "",
                "Use this reference batch as a grouped source.",
                "",
                "Example:",
                "",
                "- Reference batch: `REFERENCE_INDEX.md` in this folder",
                "- Borrow only: camera distance, sequence feel, pose variation, natural smile, skin/photo texture",
                "- Never borrow: reference model identity, exact outfit, exact room/store/signage/logo, body type, age",
                "- Override priority: character profile > Daily Brief > wardrobe rules > this reference batch",
                "",
                "For MIKU:",
                "- Keep 35-year-old adult Japanese woman impression, mask rule, MIKU face sheet, B95/W60/H95.",
                "",
                "For RIO:",
                "- Keep RIO base face sheet, 22-year-old impression, B90/W60/H90, white phone when specified.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a grouped reference index and contact sheets.")
    parser.add_argument("--source", type=Path, default=DEFAULT_REFERENCE_ROOT / "_incoming")
    parser.add_argument("--out-root", type=Path, default=DEFAULT_REFERENCE_ROOT / "_index")
    parser.add_argument("--label", default="")
    parser.add_argument("--purpose", choices=["auto", "composition", "quality_texture", "mixed"], default="auto")
    parser.add_argument("--character", choices=["auto", "MIKU", "RIO", "common"], default="auto")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--max-images", type=int, default=120)
    parser.add_argument(
        "--exclude-text",
        action="append",
        default=[],
        help="Exclude images when this text appears in the full path. Can be repeated.",
    )
    args = parser.parse_args()

    source = resolve_finder_alias(args.source)
    images = iter_images(source, recursive=args.recursive)
    if args.exclude_text:
        excludes = [text.casefold() for text in args.exclude_text if text.strip()]
        images = [
            image
            for image in images
            if not any(exclude in str(image).casefold() for exclude in excludes)
        ]
    if args.max_images > 0:
        images = images[: args.max_images]
    if not images:
        print(f"No reference images found in: {source}")
        return 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = args.label.strip() or f"reference_batch_{timestamp}"
    safe_label = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in label)
    out_dir = args.out_root.expanduser().resolve() / f"{timestamp}_{safe_label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    for image in images:
        record = read_image_info(image)
        group, relative_path = relative_group(source, image)
        record["group"] = group
        record["relative_path"] = relative_path
        record.update(classify_path(image, args.purpose, args.character))
        records.append(record)

    contact_sheets = create_contact_sheets(records, out_dir)
    manifest_path = out_dir / "REFERENCE_MANIFEST.json"
    manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    index_path = write_markdown(out_dir, label, source, records, contact_sheets)
    usage_path = write_usage_note(out_dir)

    latest_path = args.out_root.expanduser().resolve() / "LATEST_INDEX.txt"
    latest_path.write_text(str(index_path), encoding="utf-8")

    print(f"Created reference batch: {out_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Index: {index_path}")
    print(f"Usage: {usage_path}")
    for sheet in contact_sheets:
        print(f"Contact sheet: {sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

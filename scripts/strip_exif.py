from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Iterable

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SIDECAR_SUFFIX = ".exifcleaned"


def iter_images(paths: Iterable[Path]) -> list[Path]:
    images: list[Path] = []
    for path in paths:
        path = path.expanduser().resolve()
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS:
                    images.append(child)
        elif path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)
        else:
            raise FileNotFoundError(f"Image path not found: {path}")
    return sorted(set(images))


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def strip_with_external_app(path: Path, command_template: str) -> None:
    command = command_template.replace("{path}", str(path))
    subprocess.run(shlex.split(command, posix=os.name != "nt"), check=True)


def strip_with_pillow(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    suffix = path.suffix.lower()

    with Image.open(path) as image:
        if suffix in {".jpg", ".jpeg"}:
            data = list(image.getdata())
            clean = Image.new(image.mode, image.size)
            clean.putdata(data)
            if clean.mode not in {"RGB", "L"}:
                clean = clean.convert("RGB")
            clean.save(path, quality=92, optimize=True, progressive=True)
        elif suffix == ".png":
            data = list(image.getdata())
            clean = Image.new(image.mode, image.size)
            clean.putdata(data)
            clean.save(path, optimize=True)
        elif suffix == ".webp":
            data = list(image.getdata())
            clean = Image.new(image.mode, image.size)
            clean.putdata(data)
            if clean.mode not in {"RGB", "RGBA"}:
                clean = clean.convert("RGB")
            clean.save(path, quality=92, method=6)

    after = path.stat().st_size
    return before, after


def is_file_stable(path: Path, stable_seconds: float) -> bool:
    try:
        first = path.stat()
        first_size = first.st_size
        first_mtime = first.st_mtime
        time.sleep(stable_seconds)
        second = path.stat()
    except FileNotFoundError:
        return False
    return first_size == second.st_size and first_mtime == second.st_mtime


def marker_path(path: Path) -> Path:
    return path.with_name(f"{path.name}{SIDECAR_SUFFIX}")


def is_already_cleaned(path: Path) -> bool:
    marker = marker_path(path)
    if not marker.exists():
        return False
    try:
        return marker.stat().st_mtime >= path.stat().st_mtime
    except FileNotFoundError:
        return False


def write_marker(path: Path) -> None:
    marker_path(path).write_text(
        f"exif-cleaned\nsource={path.name}\nmtime={path.stat().st_mtime}\n",
        encoding="utf-8",
    )


def strip_images(images: list[Path]) -> int:
    command_template = os.getenv("EXIF_CLEANER_COMMAND", "").strip()
    if command_template:
        print("Using external EXIF cleaner command.")
        for image_path in images:
            strip_with_external_app(image_path, command_template)
            write_marker(image_path)
            print(f"EXIF cleaned: {image_path}")
        return 0

    print("EXIF_CLEANER_COMMAND is not set. Using Pillow fallback.")
    total_before = 0
    total_after = 0
    for image_path in images:
        before, after = strip_with_pillow(image_path)
        write_marker(image_path)
        total_before += before
        total_after += after
        print(f"EXIF cleaned: {image_path} {before} -> {after} bytes")

    print(
        f"Processed {len(images)} image(s): "
        f"{total_before} -> {total_after} bytes "
        f"({total_before - total_after:+d})"
    )
    return 0


def watch_folder(path: Path, interval: float, stable_seconds: float) -> int:
    root = path.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Watch folder not found: {root}")

    print(f"Watching folder for images: {root}")
    print("Google Drive synced folder is treated as the source of truth.")
    while True:
        candidates = [
            image
            for image in iter_images([root])
            if not is_already_cleaned(image) and is_file_stable(image, stable_seconds)
        ]
        if candidates:
            strip_images(candidates)
        time.sleep(interval)


def main() -> int:
    load_env_file(Path(".env"))
    parser = argparse.ArgumentParser(description="Strip EXIF/metadata from images.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously watch a folder and strip EXIF when images appear.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=float(os.getenv("EXIF_WATCH_INTERVAL_SECONDS", "10")),
        help="Watch polling interval in seconds.",
    )
    parser.add_argument(
        "--stable-seconds",
        type=float,
        default=float(os.getenv("EXIF_WATCH_STABLE_SECONDS", "5")),
        help="Seconds a file must remain unchanged before processing.",
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    if args.watch:
        if len(args.paths) != 1:
            parser.error("--watch expects exactly one folder path")
        return watch_folder(args.paths[0], args.interval, args.stable_seconds)

    images = iter_images(args.paths)
    if not images:
        print("No images found.")
        return 0
    return strip_images(images)


if __name__ == "__main__":
    raise SystemExit(main())

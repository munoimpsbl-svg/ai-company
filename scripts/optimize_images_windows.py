from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


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


def optimize_image(path: Path) -> tuple[int, int]:
    before = path.stat().st_size
    suffix = path.suffix.lower()

    with Image.open(path) as image:
        if suffix in {".jpg", ".jpeg"}:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(path, quality=92, optimize=True, progressive=True)
        elif suffix == ".png":
            image.save(path, optimize=True)
        elif suffix == ".webp":
            image.save(path, quality=92, method=6)

    after = path.stat().st_size
    return before, after


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strip metadata and optimize image files on Windows."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    images = iter_images(args.paths)
    if not images:
        print("No images found.")
        return 0

    total_before = 0
    total_after = 0
    for image_path in images:
        before, after = optimize_image(image_path)
        total_before += before
        total_after += after
        delta = before - after
        print(f"{image_path} {before} -> {after} bytes ({delta:+d})")

    print(
        f"Optimized {len(images)} image(s): "
        f"{total_before} -> {total_after} bytes "
        f"({total_before - total_after:+d})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

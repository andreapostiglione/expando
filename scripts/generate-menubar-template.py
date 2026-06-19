#!/usr/bin/env python3
"""Build macOS menu bar template icons from assets/logo.png."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Install Pillow first: pip install pillow", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "logo.png"
OUT_DIR = ROOT / "assets"
SIZES = {
    "logoTemplate.png": 18,
    "logoTemplate@2x.png": 36,
    "logoTemplate@3x.png": 54,
}


def _to_template_rgba(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError(f"No opaque pixels in {image}")
    cropped = rgba.crop(bbox)
    width, height = cropped.size
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    src = cropped.load()
    dst = out.load()
    for y in range(height):
        for x in range(width):
            _, _, _, a = src[x, y]
            if a > 32:
                dst[x, y] = (0, 0, 0, a)
    return out


def _fit_square(image: Image.Image, size: int) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - fitted.width) // 2, (size - fitted.height) // 2)
    canvas.paste(fitted, offset, fitted)
    return canvas


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing source image: {SOURCE}")

    template = _to_template_rgba(Image.open(SOURCE))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, size in SIZES.items():
        path = OUT_DIR / name
        _fit_square(template, size).save(path)
        print(f"Wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
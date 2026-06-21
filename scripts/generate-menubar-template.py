#!/usr/bin/env python3
"""Build macOS menu bar template icons from the brand logo."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Install Pillow first: pip install pillow", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SOURCE_CANDIDATES = [
    ASSETS / "logo-source.jpg",
    ASSETS / "logo.png",
]
OUT_DIR = ASSETS
# 24pt logical size — large, crisp menubar glyph (E only, no icon frame)
SIZES = {
    "logoTemplate.png": 24,
    "logoTemplate@2x.png": 48,
    "logoTemplate@3x.png": 72,
}
FILL_RATIO = 0.98


def _resolve_source() -> Path:
    for path in SOURCE_CANDIDATES:
        if path.is_file():
            return path
    raise SystemExit("No source logo found (expected assets/logo-source.jpg or assets/logo.png)")


def _is_purple_e_glyph(r: int, g: int, b: int) -> bool:
    """Keep only the purple E letter — no dark rounded square, no white motion bars."""
    if r > 228 and g > 228 and b > 228:
        return False
    if r < 58 and g < 58 and b < 72:
        return False
    if r > 175 and g > 175 and b > 175:
        return False
    if b <= g or r <= g:
        return False
    if r < 75 or g < 48 or b < 78:
        return False
    if r > 170 or g > 130 or b > 200:
        return False
    return True


def _extract_mark_rgba(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    width, height = rgb.size
    rgba = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    src = rgb.load()
    dst = rgba.load()
    for y in range(height):
        for x in range(width):
            r, g, b = src[x, y]
            if not _is_purple_e_glyph(r, g, b):
                continue
            dst[x, y] = (0, 0, 0, 255)
    alpha = rgba.split()[3]
    rgba.putalpha(alpha)
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("Could not extract logo mark from source image")
    return rgba.crop(bbox)


def _fit_square(image: Image.Image, size: int) -> Image.Image:
    work = size * 8
    target = int(work * FILL_RATIO)
    fitted = image.copy()
    fitted.thumbnail((target, target), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (work, work), (0, 0, 0, 0))
    offset = ((work - fitted.width) // 2, (work - fitted.height) // 2)
    canvas.paste(fitted, offset, fitted)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    source = _resolve_source()
    template = _extract_mark_rgba(Image.open(source))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, size in SIZES.items():
        path = OUT_DIR / name
        _fit_square(template, size).save(path, optimize=True)
        print(f"Wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
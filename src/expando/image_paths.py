from __future__ import annotations

from pathlib import Path

_SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".tif", ".tiff", ".webp"}


def resolve_image_path(config_dir: Path, raw_path: str) -> Path:
    if not raw_path.strip():
        raise RuntimeError("Image path is empty")

    expanded = raw_path.replace("$CONFIG", str(config_dir))
    candidate = Path(expanded).expanduser()
    if not candidate.is_absolute():
        candidate = (config_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()

    base = config_dir.resolve()
    if not str(candidate).startswith(str(base)):
        raise RuntimeError(f"Image path must stay inside config directory: {raw_path}")

    if not candidate.exists():
        raise RuntimeError(f"Image file not found: {candidate}")

    if candidate.suffix.lower() not in _SUPPORTED_SUFFIXES:
        raise RuntimeError(
            f"Unsupported image format {candidate.suffix!r} — use PNG, JPEG, GIF, TIFF, or WebP"
        )
    return candidate


def macos_clipboard_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".png": "PNGf",
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".gif": "GIFf",
        ".tif": "TIFF",
        ".tiff": "TIFF",
        ".webp": "PNGf",
    }
    return mapping.get(suffix, "PNGf")
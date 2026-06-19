from __future__ import annotations

import sys
from pathlib import Path


def _candidate_dirs() -> list[Path]:
    module_root = Path(__file__).resolve().parent
    dirs = [
        module_root.parents[1] / "assets",
        module_root / "assets",
    ]
    if sys.platform == "darwin":
        argv0 = Path(sys.argv[0]).resolve()
        for parent in argv0.parents:
            resources = parent / "Resources"
            if (
                (resources / "logoTemplate.png").is_file()
                or (resources / "menubar-icon.png").is_file()
                or (resources / "AppIcon.icns").is_file()
            ):
                dirs.append(resources)
                break
    return dirs


def brand_asset_path(name: str) -> Path | None:
    for directory in _candidate_dirs():
        path = directory / name
        if path.is_file():
            return path
    return None


def menubar_template_icon() -> Path | None:
    base = brand_asset_path("logoTemplate.png")
    if base is None:
        return brand_asset_path("menubar-icon.png")

    if sys.platform == "darwin":
        try:
            from AppKit import NSScreen

            scale = NSScreen.mainScreen().backingScaleFactor()
            if scale >= 3:
                candidate = base.parent / "logoTemplate@3x.png"
            elif scale >= 2:
                candidate = base.parent / "logoTemplate@2x.png"
            else:
                candidate = base
            if candidate.is_file():
                return candidate
        except Exception:
            pass
    return base
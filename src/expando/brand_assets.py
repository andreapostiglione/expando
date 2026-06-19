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
            if (resources / "menubar-icon.png").is_file() or (resources / "AppIcon.icns").is_file():
                dirs.append(resources)
                break
    return dirs


def brand_asset_path(name: str) -> Path | None:
    for directory in _candidate_dirs():
        path = directory / name
        if path.is_file():
            return path
    return None
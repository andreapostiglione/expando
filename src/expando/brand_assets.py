from __future__ import annotations

import os
import sys
from pathlib import Path

MENUBAR_ICON_POINTS = 24.0


def _resources_has_brand_assets(resources: Path) -> bool:
    return (
        (resources / "logoTemplate.png").is_file()
        or (resources / "menubar-icon.png").is_file()
        or (resources / "AppIcon.icns").is_file()
    )


def _app_bundle_resources() -> Path | None:
    """Resolve Contents/Resources when expando runs via ``python -m expando``."""
    env = os.environ.get("EXPANDO_RESOURCES", "").strip()
    if env:
        resources = Path(env)
        if _resources_has_brand_assets(resources):
            return resources

    module_file = Path(__file__).resolve()
    parts = module_file.parts
    if "site-packages" in parts:
        resources = Path(*parts[: parts.index("site-packages")])
        if resources.name == "Resources" and _resources_has_brand_assets(resources):
            return resources
    return None


def _candidate_dirs() -> list[Path]:
    module_root = Path(__file__).resolve().parent
    dirs: list[Path] = []
    bundle_resources = _app_bundle_resources()
    if bundle_resources is not None:
        dirs.append(bundle_resources)
    dirs.extend(
        [
            module_root.parents[1] / "assets",
            module_root / "assets",
        ]
    )
    if sys.platform == "darwin":
        argv0 = Path(sys.argv[0]).resolve()
        for parent in argv0.parents:
            resources = parent / "Resources"
            if _resources_has_brand_assets(resources):
                dirs.append(resources)
                break
    return dirs


def brand_assets_dir() -> Path | None:
    for directory in _candidate_dirs():
        if (directory / "logoTemplate.png").is_file() or (directory / "logo.png").is_file():
            return directory
    return None


def brand_asset_path(name: str) -> Path | None:
    for directory in _candidate_dirs():
        path = directory / name
        if path.is_file():
            return path
    return None


def menubar_template_icon() -> Path | None:
    return brand_asset_path("logoTemplate.png") or brand_asset_path("menubar-icon.png")


def load_menubar_nsimage(points: float = MENUBAR_ICON_POINTS):
    if sys.platform != "darwin":
        return None

    directory = brand_assets_dir()
    if directory is None:
        fallback = menubar_template_icon()
        if fallback is None:
            return None
        directory = fallback.parent

    from AppKit import NSBitmapImageRep, NSImage

    image = NSImage.alloc().initWithSize_((points, points))
    added = False
    for suffix in ("", "@2x", "@3x"):
        path = directory / f"logoTemplate{suffix}.png"
        if not path.is_file():
            continue
        rep = NSBitmapImageRep.imageRepWithContentsOfFile_(str(path))
        if rep is None:
            continue
        rep.setSize_((points, points))
        image.addRepresentation_(rep)
        added = True

    if not added:
        fallback = menubar_template_icon()
        if fallback is None:
            return None
        image = NSImage.alloc().initByReferencingFile_(str(fallback))
        image.setScalesWhenResized_(True)
        image.setSize_((points, points))

    image.setTemplate_(True)
    return image
from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


def find_expando_app_bundle() -> Path | None:
    """Robust ancestor-walk + env detection for Expando.app.
    Works whether package is in Resources/site-packages (dist or dev .app),
    or using embedded python, or source layout.
    """
    # env markers first (set by launch scripts or user)
    for var in ("EXPANDO_RESOURCES", "EXPANDO_APP_BUNDLE", "EXPANDO_BUNDLE"):
        val = os.environ.get(var)
        if val:
            p = Path(val).expanduser().resolve()
            while p and p.name != "Expando.app" and p != p.parent:
                p = p.parent
            if p.name == "Expando.app":
                return p

    # from sys.executable (works for embedded or framework python inside bundle)
    try:
        p = Path(sys.executable).resolve()
        while p and p.name != "Expando.app" and p != p.parent:
            p = p.parent
        if p.name == "Expando.app":
            return p
    except (OSError, RuntimeError):
        pass

    # from this module (for PYTHONPATH=src or site-packages installs)
    try:
        p = Path(__file__).resolve()
        while p and p.name != "Expando.app" and p != p.parent:
            p = p.parent
        if p.name == "Expando.app":
            return p
    except (OSError, RuntimeError):
        pass

    # last resort standard install location
    p = Path("/Applications/Expando.app")
    if p.exists():
        return p
    return None


def default_config_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "expando"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "expando"
        return Path.home() / "AppData" / "Roaming" / "expando"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "expando"
    return Path.home() / ".config" / "expando"


def config_file(config_dir: Path) -> Path:
    return config_dir / "config" / "default.yml"


def match_dir(config_dir: Path) -> Path:
    return config_dir / "match"


def pid_file(config_dir: Path) -> Path:
    return config_dir / "expando.pid"


def lock_file(config_dir: Path) -> Path:
    return config_dir / "expando.lock"


def log_file(config_dir: Path) -> Path:
    return config_dir / "expando.log"


def crashes_dir(config_dir: Path) -> Path:
    return config_dir / "crashes"


def plugins_dir(config_dir: Path) -> Path:
    return config_dir / "plugins"


def app_bundle_path(package_root: Path) -> Path:
    return package_root / "Expando.app"


def ensure_default_config(config_dir: Path, package_root: Path) -> None:
    default_root = package_root / "default_config"
    files = (
        "config/default.yml",
        "config/terminal.yml",
        "match/base.yml",
        "match/dev.yml",
        "match/packages/core/snippets.yml",
        "plugins/example.py",
        "plugins/README.md",
    )
    for relative in files:
        source = default_root / relative
        target = config_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() and source.exists():
            shutil.copy2(source, target)


def package_root() -> Path:
    app = find_expando_app_bundle()
    if app:
        # walk up from __file__ to find the python package root inside bundle
        p = Path(__file__).resolve()
        for _ in range(6):  # limit walk
            if (p / "expando" / "__init__.py").exists():
                return p
            if p == p.parent:
                break
            p = p.parent
    return Path(__file__).resolve().parent.parent.parent
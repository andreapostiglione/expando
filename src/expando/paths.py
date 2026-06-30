from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path


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
    module_root = Path(__file__).resolve().parent
    candidates = [
        module_root.parent.parent,
        module_root.parent,
        Path(sys.prefix),
    ]
    for candidate in candidates:
        if (candidate / "default_config").exists():
            return candidate
    return module_root.parent.parent

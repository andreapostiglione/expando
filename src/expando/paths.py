from __future__ import annotations

import os
import platform
import shutil
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


def log_file(config_dir: Path) -> Path:
    return config_dir / "expando.log"


def ensure_default_config(config_dir: Path, package_root: Path) -> None:
    if (config_dir / "match").exists() and (config_dir / "config").exists():
        return

    default_root = package_root / "default_config"
    for relative in ("config/default.yml", "match/base.yml"):
        source = default_root / relative
        target = config_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() and source.exists():
            shutil.copy2(source, target)


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from .config import ConfigBundle, compile_matches, load_config

logger = logging.getLogger(__name__)


def last_good_dir(config_dir: Path) -> Path:
    return config_dir / ".last-good"


def validate_config_for_reload(config_dir: Path) -> ConfigBundle:
    bundle = load_config(config_dir)
    compile_matches(bundle.matches)
    return bundle


def save_last_good_config(config_dir: Path, bundle: ConfigBundle) -> Path:
    del bundle
    destination = last_good_dir(config_dir)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for relative in ("config", "match"):
        source = config_dir / relative
        if source.exists():
            shutil.copytree(source, destination / relative)
    return destination


def rollback_to_last_good(config_dir: Path) -> bool:
    source_root = last_good_dir(config_dir)
    if not source_root.exists():
        return False
    restored = False
    for relative in ("config", "match"):
        source = source_root / relative
        if not source.exists():
            continue
        target = config_dir / relative
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        restored = True
    return restored


def safe_reload_config(config_dir: Path, engine) -> ConfigBundle:
    try:
        bundle = validate_config_for_reload(config_dir)
    except Exception:
        logger.exception("Config validation failed before reload")
        if rollback_to_last_good(config_dir):
            bundle = load_config(config_dir)
            engine.reload(bundle)
            logger.warning("Rolled back to last-good configuration")
        raise

    engine.reload(bundle)
    save_last_good_config(config_dir, bundle)
    return bundle
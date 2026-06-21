from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from .config import ConfigBundle, compile_matches, load_config

logger = logging.getLogger(__name__)

_STABLE_SETTLE_SECONDS = 0.12
_STABLE_POLL_INTERVAL = 0.05
_STABLE_TIMEOUT_SECONDS = 2.0


class ConfigReloadError(Exception):
    """Reload failed; ``rolled_back`` is True when on-disk config was restored to last-good."""

    def __init__(self, message: str, *, rolled_back: bool = False) -> None:
        super().__init__(message)
        self.rolled_back = rolled_back


def last_good_dir(config_dir: Path) -> Path:
    return config_dir / ".last-good"


def _yaml_config_files(config_dir: Path) -> list[Path]:
    files: list[Path] = []
    for relative in ("config", "match"):
        root = config_dir / relative
        if not root.exists():
            continue
        files.extend(root.rglob("*.yml"))
        files.extend(root.rglob("*.yaml"))
    return sorted(files)


def _mtime_snapshot(paths: list[Path]) -> dict[str, int]:
    snapshot: dict[str, int] = {}
    for path in paths:
        try:
            snapshot[str(path)] = path.stat().st_mtime_ns
        except OSError:
            continue
    return snapshot


def wait_for_stable_config(
    config_dir: Path,
    *,
    settle_seconds: float = _STABLE_SETTLE_SECONDS,
    poll_interval: float = _STABLE_POLL_INTERVAL,
    timeout_seconds: float = _STABLE_TIMEOUT_SECONDS,
) -> None:
    """Wait until YAML files stop changing (editors often write in multiple steps)."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        files = _yaml_config_files(config_dir)
        if not files:
            return
        before = _mtime_snapshot(files)
        time.sleep(settle_seconds)
        after = _mtime_snapshot(_yaml_config_files(config_dir))
        if before and before == after:
            return
        time.sleep(poll_interval)
    logger.warning(
        "Config files under %s did not stabilize within %.1fs; reloading anyway",
        config_dir,
        timeout_seconds,
    )


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
    wait_for_stable_config(config_dir)
    try:
        bundle = validate_config_for_reload(config_dir)
    except Exception as exc:
        logger.exception("Config validation failed before reload")
        if rollback_to_last_good(config_dir):
            bundle = load_config(config_dir)
            engine.reload(bundle)
            logger.warning("Rolled back to last-good configuration")
            raise ConfigReloadError(
                "Configuration is invalid; rolled back to the last working copy",
                rolled_back=True,
            ) from exc
        raise ConfigReloadError("Configuration is invalid and could not be rolled back") from exc

    save_last_good_config(config_dir, bundle)
    engine.reload(bundle)
    return bundle
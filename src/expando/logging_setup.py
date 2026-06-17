from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .log_viewer import resolve_log_level


def setup_logging(config_dir: Path, level: int | None = None) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    log_path = config_dir / "expando.log"

    if level is None:
        try:
            from .config import load_config

            level = resolve_log_level(load_config(config_dir).app.log_level)
        except Exception:
            level = resolve_log_level()

    root = logging.getLogger()
    if getattr(root, "_expando_configured", False):
        return

    root.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.WARNING)
    root.addHandler(console)

    root._expando_configured = True  # type: ignore[attr-defined]
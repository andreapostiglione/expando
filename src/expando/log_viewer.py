from __future__ import annotations

import logging
import os
import time
from pathlib import Path


def resolve_log_level(name: str | None = None) -> int:
    raw = (name or os.environ.get("EXPANDO_LOG_LEVEL", "INFO")).upper()
    return getattr(logging, raw, logging.INFO)


def print_log_tail(
    log_path: Path,
    *,
    lines: int = 50,
    follow: bool = False,
    poll_interval: float = 0.5,
) -> None:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        if lines > 0:
            content = handle.read().splitlines()
            for line in content[-lines:]:
                print(line)
        else:
            for line in handle:
                print(line.rstrip("\n"))

        if not follow:
            return

        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                print(line.rstrip("\n"))
            else:
                time.sleep(poll_interval)
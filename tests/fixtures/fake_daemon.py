"""Minimal stand-in process for daemon integration tests."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path


def main() -> None:
    config_dir = Path(sys.argv[1])
    config_dir.mkdir(parents=True, exist_ok=True)
    pid_path = config_dir / "expando.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")

    running = True

    def stop(*_args) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while running:
        time.sleep(0.05)

    pid_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
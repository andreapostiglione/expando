from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .paths import log_file, pid_file


def is_running(config_dir: Path) -> tuple[bool, int | None]:
    path = pid_file(config_dir)
    if not path.exists():
        return False, None
    try:
        pid = int(path.read_text().strip())
    except ValueError:
        return False, None
    try:
        os.kill(pid, 0)
    except OSError:
        path.unlink(missing_ok=True)
        return False, None
    return True, pid


def start_daemon(config_dir: Path) -> int:
    running, pid = is_running(config_dir)
    if running:
        return pid or 0

    config_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_file(config_dir)
    log_handle = open(log_path, "a", encoding="utf-8")

    process = subprocess.Popen(
        [sys.executable, "-m", "expando.daemon", "foreground", str(config_dir)],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    pid_file(config_dir).write_text(str(process.pid), encoding="utf-8")
    return process.pid


def stop_daemon(config_dir: Path) -> bool:
    running, pid = is_running(config_dir)
    if not running or pid is None:
        pid_file(config_dir).unlink(missing_ok=True)
        return False
    os.kill(pid, signal.SIGTERM)
    for _ in range(20):
        time.sleep(0.1)
        if not is_running(config_dir)[0]:
            pid_file(config_dir).unlink(missing_ok=True)
            return True
    os.kill(pid, signal.SIGKILL)
    pid_file(config_dir).unlink(missing_ok=True)
    return True


def foreground(config_dir: Path) -> None:
    from .listener import run_service

    pid_file(config_dir).write_text(str(os.getpid()), encoding="utf-8")

    def cleanup(*_args) -> None:
        pid_file(config_dir).unlink(missing_ok=True)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    run_service(config_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: python -m expando.daemon foreground <config_dir>")
    foreground(Path(sys.argv[2]))
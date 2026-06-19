from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .lock import SingleInstanceLock
from .logging_setup import setup_logging
from .paths import lock_file, log_file, pid_file

logger = logging.getLogger(__name__)


def is_running(config_dir: Path) -> tuple[bool, int | None]:
    path = pid_file(config_dir)
    if not path.exists():
        return False, None
    try:
        pid = int(path.read_text().strip())
    except (ValueError, FileNotFoundError):
        return False, None
    try:
        os.kill(pid, 0)
    except OSError:
        path.unlink(missing_ok=True)
        return False, None
    return True, pid


def _daemon_command(config_dir: Path) -> list[str]:
    app_bundle = _app_bundle_executable()
    if app_bundle:
        return [str(app_bundle), "--config-dir", str(config_dir), "run"]
    return [sys.executable, "-m", "expando.daemon", "foreground", str(config_dir)]


def _app_bundle_executable() -> Path | None:
    if os.environ.get("EXPANDO_USE_APP_BUNDLE", "").lower() in {"0", "false", "no"}:
        return None

    root = Path(__file__).resolve().parent.parent.parent
    candidate = root / "Expando.app" / "Contents" / "MacOS" / "expando"
    if not candidate.exists() or not os.access(candidate, os.X_OK):
        return None

    # In a git checkout, prefer the local venv unless the app bundle is explicit.
    if (root / ".git").exists() and os.environ.get("EXPANDO_USE_APP_BUNDLE", "") != "1":
        return None

    return candidate


def start_daemon(config_dir: Path) -> int:
    config_dir.mkdir(parents=True, exist_ok=True)
    starter_lock = SingleInstanceLock(lock_file(config_dir).with_name("expando.starter.lock"))
    if not starter_lock.acquire(blocking=False):
        running, pid = is_running(config_dir)
        if running and pid is not None:
            return pid
        raise RuntimeError("Another start operation is in progress")

    try:
        running, pid = is_running(config_dir)
        if running and pid is not None:
            logger.info("Expando already running with pid %s", pid)
            return pid

        setup_logging(config_dir)
        log_path = log_file(config_dir)
        log_handle = open(log_path, "a", encoding="utf-8")
        process = subprocess.Popen(
            _daemon_command(config_dir),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()

        for _ in range(30):
            time.sleep(0.1)
            if is_running(config_dir)[0]:
                running, pid = is_running(config_dir)
                logger.info("Expando started with pid %s", pid or process.pid)
                return pid or process.pid
            if process.poll() is not None:
                raise RuntimeError(f"Expando process exited immediately with code {process.returncode}")

        pid_file(config_dir).write_text(str(process.pid), encoding="utf-8")
        logger.info("Expando started with pid %s", process.pid)
        return process.pid
    finally:
        starter_lock.release()


def restart_daemon(config_dir: Path) -> int:
    """Stop and start the background daemon; returns the new pid."""
    stop_daemon(config_dir)
    time.sleep(0.3)
    return start_daemon(config_dir)


def restart_foreground_daemon(config_dir: Path) -> None:
    """Replace the current foreground daemon process (menu bar mode)."""
    argv = [sys.executable, "-m", "expando.daemon", "foreground", str(config_dir)]
    os.execve(sys.executable, argv, os.environ)


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
    from .crash_loop import record_daemon_crash
    from .crash_reporting import install_crash_handlers
    from .listener import run_service

    setup_logging(config_dir)
    install_crash_handlers(config_dir)
    lock = SingleInstanceLock(lock_file(config_dir))
    if not lock.acquire():
        running, pid = is_running(config_dir)
        if running:
            logger.error("Another Expando instance is already running (pid %s)", pid)
            raise SystemExit(0)
        logger.error("Could not acquire single-instance lock")
        raise SystemExit(1)

    pid_file(config_dir).write_text(str(os.getpid()), encoding="utf-8")

    def cleanup(*_args) -> None:
        pid_file(config_dir).unlink(missing_ok=True)
        lock.release()

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    try:
        run_service(config_dir)
    except Exception:
        record_daemon_crash(config_dir, reason="foreground_exception")
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: python -m expando.daemon foreground <config_dir>")
    foreground(Path(sys.argv[2]))
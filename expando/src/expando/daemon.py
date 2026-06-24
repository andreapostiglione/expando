from __future__ import annotations

import logging
import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

from .lock import SingleInstanceLock
from .logging_setup import setup_logging
from .paths import lock_file, log_file, pid_file

logger = logging.getLogger(__name__)

_START_WAIT_ATTEMPTS = 30
_START_WAIT_INTERVAL_SECONDS = 0.1

_foreground_cleanup: Callable[[], None] | None = None


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

        for _ in range(_START_WAIT_ATTEMPTS):
            time.sleep(_START_WAIT_INTERVAL_SECONDS)
            if is_running(config_dir)[0]:
                running, pid = is_running(config_dir)
                if pid is None:
                    raise RuntimeError("Expando pid file is present but unreadable")
                logger.info("Expando started with pid %s", pid)
                return pid
            if process.poll() is not None:
                raise RuntimeError(
                    f"Expando process exited before writing pid file (code {process.returncode})"
                )

        if process.poll() is not None:
            raise RuntimeError(
                f"Expando process exited before writing pid file (code {process.returncode})"
            )
        raise RuntimeError(
            "Expando did not start within "
            f"{_START_WAIT_ATTEMPTS * _START_WAIT_INTERVAL_SECONDS:.1f}s "
            "(pid file not written)"
        )
    finally:
        starter_lock.release()


def register_foreground_cleanup(cleanup: Callable[[], None] | None) -> None:
    """Register cleanup invoked before a menu-bar restart replaces this process."""
    global _foreground_cleanup
    _foreground_cleanup = cleanup


def release_foreground_instance(config_dir: Path) -> None:
    """Release the single-instance lock so a replacement process can start."""
    global _foreground_cleanup
    cleanup = _foreground_cleanup
    _foreground_cleanup = None
    if cleanup is not None:
        cleanup()
    else:
        pid_file(config_dir).unlink(missing_ok=True)
        lock_file(config_dir).unlink(missing_ok=True)


def restart_foreground_daemon(
    config_dir: Path,
    *,
    wait_for_pid: int | None = None,
) -> None:
    """Spawn a replacement foreground daemon and exit the current process.

    Must be called from the AppKit main thread after stopping the keyboard
    service. ``os.execve`` is unsafe while ``NSApplication`` is running.

    When *wait_for_pid* is set, the replacement starts only after that process
    exits so two listeners never run at once.
    """
    argv = _daemon_command(config_dir)
    release_foreground_instance(config_dir)
    log_path = log_file(config_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = " ".join(shlex.quote(part) for part in argv)
    log_redirect = f" >> {shlex.quote(str(log_path))} 2>&1"

    if wait_for_pid is not None:
        shell_cmd = (
            f"while kill -0 {int(wait_for_pid)} 2>/dev/null; do sleep 0.1; done; "
            f"exec {cmd}{log_redirect}"
        )
        subprocess.Popen(
            ["/bin/bash", "-c", shell_cmd],
            start_new_session=True,
            close_fds=True,
            env=os.environ.copy(),
        )
        logger.info(
            "Scheduled replacement foreground daemon after pid %s exits: %s",
            wait_for_pid,
            " ".join(argv),
        )
        return

    log_handle = open(log_path, "a", encoding="utf-8")
    try:
        subprocess.Popen(
            argv,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
            env=os.environ.copy(),
        )
    except Exception:
        log_handle.close()
        raise
    log_handle.close()
    logger.info("Spawned replacement foreground daemon: %s", " ".join(argv))


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
        register_foreground_cleanup(None)
        pid_file(config_dir).unlink(missing_ok=True)
        lock.release()

    register_foreground_cleanup(cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    try:
        run_service(config_dir)
    finally:
        cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: python -m expando.daemon foreground <config_dir>")
    foreground(Path(sys.argv[2]))
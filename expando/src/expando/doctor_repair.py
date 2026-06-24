from __future__ import annotations

import fcntl
import os
import platform
import plistlib
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from .daemon import is_running
from .paths import lock_file, package_root, pid_file


def _find_expando_processes() -> list[int]:
    from .doctor_checks import find_expando_processes

    return find_expando_processes()


def _lock_paths(config_dir: Path) -> list[Path]:
    return [
        lock_file(config_dir),
        lock_file(config_dir).with_name("expando.starter.lock"),
    ]


def _lock_holder_pid(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        content = path.read_text(encoding="utf-8").strip()
        return int(content)
    except (OSError, ValueError):
        return None


def _is_stale_lock(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        handle = open(path, encoding="utf-8")
    except OSError:
        return False
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return True
        except BlockingIOError:
            holder = _lock_holder_pid(path)
            if holder is None:
                return True
            try:
                os.kill(holder, 0)
            except OSError:
                return True
            return False
    finally:
        handle.close()


def diagnose_daemon_state(config_dir: Path) -> dict[str, Any]:
    config_dir.mkdir(parents=True, exist_ok=True)
    running, pid = is_running(config_dir)
    processes = _find_expando_processes()
    pid_path = pid_file(config_dir)

    stale_pid_file = pid_path.exists() and not running
    orphan_processes = [
        process_pid
        for process_pid in processes
        if not (running and pid is not None and process_pid == pid)
    ]
    stale_locks = [str(path.name) for path in _lock_paths(config_dir) if _is_stale_lock(path)]

    needs_repair = bool(stale_pid_file or orphan_processes or stale_locks)
    return {
        "running": running,
        "pid": pid,
        "process_count": len(processes),
        "stale_pid_file": stale_pid_file,
        "orphan_processes": orphan_processes,
        "stale_locks": stale_locks,
        "needs_repair": needs_repair,
    }


def _installed_launch_agent_path() -> Path:
    return Path.home() / "Library/LaunchAgents/com.andreapostiglione.expando.plist"


def _source_launch_agent_path() -> Path:
    return package_root() / "scripts" / "com.andreapostiglione.expando.plist"


def launch_agent_needs_refresh() -> bool:
    if platform.system() != "Darwin":
        return False
    source = _source_launch_agent_path()
    installed = _installed_launch_agent_path()
    if not source.is_file():
        return False
    if not installed.is_file():
        return True
    try:
        source_data = plistlib.loads(source.read_bytes())
        installed_data = plistlib.loads(installed.read_bytes())
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException):
        return True
    for key in ("ThrottleInterval", "KeepAlive", "RunAtLoad", "Label"):
        if source_data.get(key) != installed_data.get(key):
            return True
    # AC1 this-round cleanup: removed dead assignment for the source program args var
    installed_args = installed_data.get("ProgramArguments") or []
    if not installed_args:
        return True
    if not str(installed_args[0]).endswith("launch-expando.sh"):
        return True
    return False


def repair_launch_agent() -> list[str]:
    if platform.system() != "Darwin":
        return []
    script = package_root() / "scripts" / "install-launch-agent.sh"
    if not script.is_file():
        return []
    if not launch_agent_needs_refresh() and _installed_launch_agent_path().is_file():
        return []
    try:
        subprocess.run(["bash", str(script)], check=True, timeout=120)
    except (subprocess.SubprocessError, OSError, FileNotFoundError):
        return []
    return ["reinstalled_launch_agent"]


def repair_daemon_state(config_dir: Path) -> dict[str, Any]:
    config_dir.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []
    running, pid = is_running(config_dir)
    pid_path = pid_file(config_dir)

    if pid_path.exists() and not running:
        pid_path.unlink(missing_ok=True)
        actions.append("removed_stale_pid_file")

    processes = _find_expando_processes()
    keep_pid = pid if running else None
    killed: list[int] = []
    for process_pid in processes:
        if keep_pid is not None and process_pid == keep_pid:
            continue
        try:
            os.kill(process_pid, signal.SIGTERM)
            killed.append(process_pid)
        except OSError:
            continue

    if killed:
        for _ in range(20):
            remaining = [
                process_pid
                for process_pid in _find_expando_processes()
                if keep_pid is None or process_pid != keep_pid
            ]
            if not remaining:
                break
            time.sleep(0.1)
        for process_pid in _find_expando_processes():
            if keep_pid is not None and process_pid == keep_pid:
                continue
            try:
                os.kill(process_pid, signal.SIGKILL)
                if process_pid not in killed:
                    killed.append(process_pid)
            except OSError:
                continue
        actions.append(f"killed_orphan_processes:{','.join(str(item) for item in killed)}")

    for path in _lock_paths(config_dir):
        if not _is_stale_lock(path):
            continue
        path.unlink(missing_ok=True)
        actions.append(f"released_stale_lock:{path.name}")

    try:
        from .crash_loop import clear_safe_mode, safe_mode_file

        if safe_mode_file(config_dir).exists():
            clear_safe_mode(config_dir)
            actions.append("cleared_safe_mode")
    except Exception:
        pass

    actions.extend(repair_launch_agent())

    running_after, pid_after = is_running(config_dir)
    diagnosis = diagnose_daemon_state(config_dir)
    return {
        "ok": not diagnosis["needs_repair"],
        "actions": actions,
        "running_after": running_after,
        "pid_after": pid_after,
        "process_count_after": diagnosis["process_count"],
        "diagnosis": diagnosis,
    }
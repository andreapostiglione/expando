from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .daemon import is_running
from .paths import log_file

HEALTH_VERSION = 1
RUNTIME_HEALTH_FILENAME = "runtime-health.json"


def runtime_health_file(config_dir: Path) -> Path:
    return config_dir / RUNTIME_HEALTH_FILENAME


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _default_health() -> dict[str, Any]:
    return {
        "version": HEALTH_VERSION,
        "daemon_started_at": None,
        "last_expansion_at": None,
        "last_expansion_trigger": None,
        "config_reload_count": 0,
        "last_config_reload_at": None,
        "listener_alive": None,
        "listener_restart_count": 0,
        "last_listener_dead_at": None,
        "last_sparkle_check_at": None,
        "updated_at": None,
    }


def load_runtime_health(config_dir: Path) -> dict[str, Any]:
    path = runtime_health_file(config_dir)
    if not path.exists():
        return _default_health()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{RUNTIME_HEALTH_FILENAME} must be a JSON object")
    merged = _default_health()
    merged.update(data)
    return merged


def _save_runtime_health(config_dir: Path, data: dict[str, Any]) -> None:
    from .atomic_io import atomic_write_text

    data["version"] = HEALTH_VERSION
    data["updated_at"] = _utc_now()
    path = runtime_health_file(config_dir)
    atomic_write_text(
        path,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


def _update_runtime_health(config_dir: Path, **updates: Any) -> dict[str, Any]:
    data = load_runtime_health(config_dir)
    data.update(updates)
    _save_runtime_health(config_dir, data)
    return data


def record_daemon_started(config_dir: Path) -> None:
    now = _utc_now()
    data = load_runtime_health(config_dir)
    if not data.get("daemon_started_at"):
        data["daemon_started_at"] = now
    data["listener_alive"] = True
    _save_runtime_health(config_dir, data)


def record_expansion(config_dir: Path, trigger: str) -> None:
    _update_runtime_health(
        config_dir,
        last_expansion_at=_utc_now(),
        last_expansion_trigger=trigger,
    )


def record_config_reload(config_dir: Path) -> None:
    data = load_runtime_health(config_dir)
    count = int(data.get("config_reload_count", 0) or 0) + 1
    _update_runtime_health(
        config_dir,
        config_reload_count=count,
        last_config_reload_at=_utc_now(),
    )


def record_listener_alive(config_dir: Path, *, alive: bool) -> None:
    updates: dict[str, Any] = {"listener_alive": alive}
    if not alive:
        updates["last_listener_dead_at"] = _utc_now()
    _update_runtime_health(config_dir, **updates)


def record_listener_restart(config_dir: Path) -> None:
    data = load_runtime_health(config_dir)
    count = int(data.get("listener_restart_count", 0) or 0) + 1
    _update_runtime_health(
        config_dir,
        listener_restart_count=count,
        listener_alive=True,
    )


def record_sparkle_check(config_dir: Path) -> None:
    _update_runtime_health(config_dir, last_sparkle_check_at=_utc_now())


def _uptime_seconds(started_at: str | None) -> float | None:
    if not started_at:
        return None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, datetime.now(timezone.utc).timestamp() - started.timestamp())


def _last_update_check_iso(config_dir: Path) -> str | None:
    marker = config_dir / ".last_update_check"
    if not marker.exists():
        return None
    try:
        ts = float(marker.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat()


def build_health_document(config_dir: Path) -> dict[str, Any]:
    config_dir = config_dir.expanduser()
    running, pid = is_running(config_dir)
    runtime = load_runtime_health(config_dir)
    uptime = _uptime_seconds(runtime.get("daemon_started_at"))
    log_path = log_file(config_dir)
    return {
        "version": 1,
        "generated_at": _utc_now(),
        "expando_version": __version__,
        "config_dir": str(config_dir),
        "daemon": {
            "running": running,
            "pid": pid,
            "started_at": runtime.get("daemon_started_at"),
            "uptime_seconds": uptime,
        },
        "listener": {
            "alive": runtime.get("listener_alive") if running else None,
            "restart_count": runtime.get("listener_restart_count", 0),
            "last_dead_at": runtime.get("last_listener_dead_at"),
        },
        "expansion": {
            "last_at": runtime.get("last_expansion_at"),
            "last_trigger": runtime.get("last_expansion_trigger"),
        },
        "config": {
            "reload_count": runtime.get("config_reload_count", 0),
            "last_reload_at": runtime.get("last_config_reload_at"),
        },
        "updates": {
            "last_sparkle_check_at": runtime.get("last_sparkle_check_at")
            or _last_update_check_iso(config_dir),
        },
        "runtime_health_updated_at": runtime.get("updated_at"),
        "log_file": str(log_path),
        "log_exists": log_path.exists(),
    }


def format_health_report(document: dict[str, Any]) -> str:
    daemon = document.get("daemon", {})
    listener = document.get("listener", {})
    expansion = document.get("expansion", {})
    config = document.get("config", {})
    updates = document.get("updates", {})

    lines = [
        "Expando runtime health",
        f"Config dir: {document.get('config_dir', '')}",
        f"Daemon running: {'yes' if daemon.get('running') else 'no'}",
    ]
    if daemon.get("pid"):
        lines.append(f"PID: {daemon['pid']}")
    uptime = daemon.get("uptime_seconds")
    if uptime is not None:
        lines.append(f"Uptime: {int(uptime)}s")
    if daemon.get("started_at"):
        lines.append(f"Started at: {daemon['started_at']}")

    if daemon.get("running"):
        alive = listener.get("alive")
        if alive is None:
            listener_state = "unknown"
        else:
            listener_state = "yes" if alive else "no"
        lines.append(f"Listener alive: {listener_state}")
        restarts = listener.get("restart_count", 0)
        if restarts:
            lines.append(f"Listener restarts: {restarts}")

    if expansion.get("last_at"):
        lines.append(f"Last expansion: {expansion['last_at']}")
        if expansion.get("last_trigger"):
            lines.append(f"Last trigger: {expansion['last_trigger']}")

    reload_count = config.get("reload_count", 0)
    lines.append(f"Config reloads: {reload_count}")
    if config.get("last_reload_at"):
        lines.append(f"Last config reload: {config['last_reload_at']}")

    sparkle = updates.get("last_sparkle_check_at")
    lines.append(f"Last update check: {sparkle or 'never'}")

    return "\n".join(lines)
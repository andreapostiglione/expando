from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .backup import backup_config
from .config import load_app_config
from .paths import config_file

BACKUP_STATE_FILENAME = "auto-backup-state.json"
DEFAULT_RETENTION = 7
DEFAULT_STALE_DAYS = 14
SCHEDULES = frozenset({"off", "daily", "weekly"})


def backup_state_file(config_dir: Path) -> Path:
    return config_dir / BACKUP_STATE_FILENAME


def backups_dir(config_dir: Path) -> Path:
    return config_dir / "backups"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_state(config_dir: Path) -> dict[str, Any]:
    path = backup_state_file(config_dir)
    if not path.exists():
        return {"last_backup_at": None, "last_backup_path": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{BACKUP_STATE_FILENAME} must be a JSON object")
    return data


def _save_state(config_dir: Path, data: dict[str, Any]) -> None:
    path = backup_state_file(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve_schedule(config_dir: Path) -> str:
    app = load_app_config(config_file(config_dir))
    schedule = str(getattr(app, "auto_backup", "weekly") or "weekly").lower()
    if schedule not in SCHEDULES:
        return "weekly"
    return schedule


def _resolve_retention(config_dir: Path) -> int:
    app = load_app_config(config_file(config_dir))
    value = int(getattr(app, "auto_backup_retention", DEFAULT_RETENTION) or DEFAULT_RETENTION)
    return max(1, value)


def stale_backup_days(config_dir: Path) -> int:
    app = load_app_config(config_file(config_dir))
    value = int(getattr(app, "auto_backup_stale_days", DEFAULT_STALE_DAYS) or DEFAULT_STALE_DAYS)
    return max(1, value)


def _should_run_backup(config_dir: Path, *, schedule: str, last_backup_at: str | None) -> bool:
    if schedule == "off":
        return False
    if not last_backup_at:
        return True
    try:
        last = datetime.fromisoformat(last_backup_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    age_seconds = datetime.now(timezone.utc).timestamp() - last.timestamp()
    if schedule == "daily":
        return age_seconds >= 86400
    if schedule == "weekly":
        return age_seconds >= 7 * 86400
    return False


def _prune_backups(directory: Path, *, keep: int) -> None:
    archives = sorted(
        directory.glob("auto-backup-*.tar.gz"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in archives[keep:]:
        path.unlink(missing_ok=True)


def create_auto_backup(config_dir: Path) -> Path | None:
    config_dir = config_dir.expanduser()
    schedule = _resolve_schedule(config_dir)
    if schedule == "off":
        return None

    state = _load_state(config_dir)
    if not _should_run_backup(config_dir, schedule=schedule, last_backup_at=state.get("last_backup_at")):
        return None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = backups_dir(config_dir) / f"auto-backup-{stamp}.tar.gz"
    archive = backup_config(config_dir, destination)
    _prune_backups(backups_dir(config_dir), keep=_resolve_retention(config_dir))
    _save_state(
        config_dir,
        {
            "last_backup_at": _utc_now(),
            "last_backup_path": str(archive),
            "schedule": schedule,
        },
    )
    return archive


def maybe_run_auto_backup(config_dir: Path) -> Path | None:
    try:
        return create_auto_backup(config_dir)
    except Exception:
        return None


def latest_backup_age_days(config_dir: Path) -> float | None:
    state = _load_state(config_dir)
    last_backup_at = state.get("last_backup_at")
    if not last_backup_at:
        directory = backups_dir(config_dir)
        if directory.exists():
            archives = sorted(directory.glob("*.tar.gz"), key=lambda item: item.stat().st_mtime, reverse=True)
            if archives:
                age_seconds = datetime.now(timezone.utc).timestamp() - archives[0].stat().st_mtime
                return age_seconds / 86400
        return None
    try:
        last = datetime.fromisoformat(str(last_backup_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    age_seconds = datetime.now(timezone.utc).timestamp() - last.timestamp()
    return max(0.0, age_seconds / 86400)


def backup_stale_warning(config_dir: Path) -> str | None:
    schedule = _resolve_schedule(config_dir)
    if schedule == "off":
        return None
    age_days = latest_backup_age_days(config_dir)
    if age_days is None:
        return "No automatic backup found — consider `expando backup` or enable auto_backup."
    threshold = stale_backup_days(config_dir)
    if age_days > threshold:
        return (
            f"Last backup is {int(age_days)} days old (threshold {threshold} days). "
            "Run `expando backup` or check auto_backup settings."
        )
    return None


def backup_before_mutation(config_dir: Path, label: str) -> Path:
    config_dir = config_dir.expanduser()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = re.sub(r"[^\w.-]+", "-", label).strip("-") or "mutation"
    destination = backups_dir(config_dir) / f"pre-{safe_label}-{stamp}.tar.gz"
    return backup_config(config_dir, destination)
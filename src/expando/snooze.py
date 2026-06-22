from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SNOOZE_FILENAME = "snooze.json"
SNOOZE_VERSION = 1


def snooze_file(config_dir: Path) -> Path:
    return config_dir.expanduser() / SNOOZE_FILENAME


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_snooze(config_dir: Path) -> dict[str, Any]:
    path = snooze_file(config_dir)
    if not path.exists():
        return {"version": SNOOZE_VERSION, "until": None, "reason": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{SNOOZE_FILENAME} must be a JSON object")
    return data


def _save_snooze(config_dir: Path, data: dict[str, Any]) -> None:
    from .atomic_io import atomic_write_text

    data["version"] = SNOOZE_VERSION
    data["updated_at"] = _utc_now()
    atomic_write_text(
        snooze_file(config_dir),
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


def clear_snooze(config_dir: Path) -> None:
    path = snooze_file(config_dir)
    if path.exists():
        path.unlink(missing_ok=True)


def set_snooze(config_dir: Path, *, minutes: int, reason: str = "manual") -> datetime:
    if minutes <= 0:
        raise ValueError("snooze minutes must be positive")
    until = datetime.now(timezone.utc).timestamp() + (minutes * 60)
    until_dt = datetime.fromtimestamp(until, tz=timezone.utc).replace(microsecond=0)
    _save_snooze(
        config_dir,
        {
            "until": until_dt.isoformat(),
            "reason": reason,
        },
    )
    return until_dt


def snooze_until(config_dir: Path) -> datetime | None:
    data = load_snooze(config_dir)
    raw = data.get("until")
    if not isinstance(raw, str) or not raw.strip():
        return None
    until = _parse_iso(raw)
    if until is None:
        return None
    if until <= datetime.now(timezone.utc):
        clear_snooze(config_dir)
        return None
    return until


def snooze_active(config_dir: Path) -> bool:
    return snooze_until(config_dir) is not None


def snooze_remaining_seconds(config_dir: Path) -> int | None:
    until = snooze_until(config_dir)
    if until is None:
        return None
    remaining = until.timestamp() - datetime.now(timezone.utc).timestamp()
    return max(0, int(remaining))


def format_snooze_remaining(config_dir: Path) -> str | None:
    seconds = snooze_remaining_seconds(config_dir)
    if seconds is None:
        return None
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if rem_minutes:
        return f"{hours}h {rem_minutes}m"
    return f"{hours}h"
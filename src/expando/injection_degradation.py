from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEALTH_VERSION = 1
DEFAULT_WARN_THRESHOLD = 3
DEFAULT_DISABLE_THRESHOLD = 10


def injection_health_file(config_dir: Path) -> Path:
    return config_dir / "injection-health.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _warn_threshold() -> int:
    raw = os.environ.get("EXPANDO_INJECTION_WARN_THRESHOLD", "")
    if raw.isdigit():
        return int(raw)
    return DEFAULT_WARN_THRESHOLD


def _disable_threshold() -> int:
    raw = os.environ.get("EXPANDO_INJECTION_DISABLE_THRESHOLD", "")
    if raw.isdigit():
        return int(raw)
    return DEFAULT_DISABLE_THRESHOLD


def auto_disable_enabled() -> bool:
    return os.environ.get("EXPANDO_AUTO_DISABLE_INJECTION", "").lower() in {
        "1",
        "true",
        "yes",
    }


def _load_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": HEALTH_VERSION, "consecutive_failures": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("injection-health.json must be a JSON object")
    data.setdefault("consecutive_failures", 0)
    data["version"] = HEALTH_VERSION
    return data


def _save_document(path: Path, data: dict[str, Any]) -> None:
    from .atomic_io import atomic_write_text

    atomic_write_text(
        path,
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


def record_injection_success(config_dir: Path) -> dict[str, Any]:
    path = injection_health_file(config_dir)
    data = _load_document(path)
    data["consecutive_failures"] = 0
    data["last_success_at"] = _utc_now()
    _save_document(path, data)
    return degradation_status(config_dir)


def record_injection_failure(config_dir: Path) -> dict[str, Any]:
    path = injection_health_file(config_dir)
    data = _load_document(path)
    data["consecutive_failures"] = int(data.get("consecutive_failures", 0)) + 1
    data["last_failure_at"] = _utc_now()
    _save_document(path, data)
    return degradation_status(config_dir)


def degradation_status(config_dir: Path) -> dict[str, Any]:
    path = injection_health_file(config_dir)
    data = _load_document(path)
    consecutive_failures = int(data.get("consecutive_failures", 0))
    warn_threshold = _warn_threshold()
    disable_threshold = _disable_threshold()
    auto_disable = auto_disable_enabled()
    should_warn = consecutive_failures >= warn_threshold
    should_disable = auto_disable and consecutive_failures >= disable_threshold
    return {
        "consecutive_failures": consecutive_failures,
        "warn_threshold": warn_threshold,
        "disable_threshold": disable_threshold,
        "auto_disable_enabled": auto_disable,
        "should_warn": should_warn,
        "should_disable": should_disable,
        "last_success_at": data.get("last_success_at"),
        "last_failure_at": data.get("last_failure_at"),
    }
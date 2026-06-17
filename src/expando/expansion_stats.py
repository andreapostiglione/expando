from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import load_app_config
from .i18n import t
from .paths import config_file


def stats_file(config_dir: Path) -> Path:
    return config_dir / "expansion_stats.json"


@dataclass
class ExpansionStats:
    enabled: bool
    total: int
    by_trigger: dict[str, int]
    updated_at: str


def _load_raw(config_dir: Path) -> dict:
    path = stats_file(config_dir)
    if not path.exists():
        return {"enabled": False, "total": 0, "by_trigger": {}, "updated_at": ""}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_raw(config_dir: Path, data: dict) -> None:
    path = stats_file(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_tracking_enabled(config_dir: Path) -> bool:
    app = load_app_config(config_file(config_dir))
    if not app.track_expansions:
        return False
    return bool(_load_raw(config_dir).get("enabled", False))


def set_tracking_enabled(config_dir: Path, enabled: bool) -> None:
    data = _load_raw(config_dir)
    data["enabled"] = enabled
    if enabled and not data.get("updated_at"):
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_raw(config_dir, data)


def record_expansion(config_dir: Path, trigger: str) -> None:
    if not is_tracking_enabled(config_dir):
        return
    data = _load_raw(config_dir)
    data["total"] = int(data.get("total", 0)) + 1
    by_trigger = dict(data.get("by_trigger", {}) or {})
    by_trigger[trigger] = int(by_trigger.get(trigger, 0)) + 1
    data["by_trigger"] = by_trigger
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    _save_raw(config_dir, data)


def load_stats(config_dir: Path) -> ExpansionStats:
    data = _load_raw(config_dir)
    return ExpansionStats(
        enabled=bool(data.get("enabled", False)),
        total=int(data.get("total", 0)),
        by_trigger={str(k): int(v) for k, v in (data.get("by_trigger", {}) or {}).items()},
        updated_at=str(data.get("updated_at", "")),
    )


def format_stats_report(config_dir: Path) -> str:
    app = load_app_config(config_file(config_dir))
    stats = load_stats(config_dir)
    lines = [
        f"{t('stats.config')}: {'on' if app.track_expansions else 'off'}",
        f"{t('stats.recording')}: {'on' if stats.enabled else 'off'}",
        f"{t('stats.total')}: {stats.total}",
    ]
    if stats.updated_at:
        lines.append(f"{t('stats.updated')}: {stats.updated_at}")
    if stats.by_trigger:
        lines.append(t("stats.by_trigger"))
        for trigger, count in sorted(
            stats.by_trigger.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(f"  {trigger:20} {count}")
    return "\n".join(lines)
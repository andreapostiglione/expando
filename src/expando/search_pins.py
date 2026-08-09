"""Pinned search triggers (user favorites in the fuzzy picker)."""

from __future__ import annotations

import json
from pathlib import Path


def pins_file(config_dir: Path) -> Path:
    return config_dir / "search_pins.json"


def load_pins(config_dir: Path) -> list[str]:
    path = pins_file(config_dir)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    pins = data.get("pins", data if isinstance(data, list) else [])
    result: list[str] = []
    seen: set[str] = set()
    for item in pins:
        trigger = str(item).strip()
        if not trigger or trigger in seen:
            continue
        seen.add(trigger)
        result.append(trigger)
    return result


def save_pins(config_dir: Path, pins: list[str]) -> None:
    path = pins_file(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in pins:
        trigger = str(item).strip()
        if not trigger or trigger in seen:
            continue
        seen.add(trigger)
        cleaned.append(trigger)
    path.write_text(
        json.dumps({"pins": cleaned}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def pin_trigger(config_dir: Path, trigger: str) -> list[str]:
    pins = load_pins(config_dir)
    if trigger not in pins:
        pins.insert(0, trigger)
    save_pins(config_dir, pins)
    return pins


def unpin_trigger(config_dir: Path, trigger: str) -> list[str]:
    pins = [item for item in load_pins(config_dir) if item != trigger]
    save_pins(config_dir, pins)
    return pins


def is_pinned(config_dir: Path, trigger: str) -> bool:
    return trigger in load_pins(config_dir)

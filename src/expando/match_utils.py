from __future__ import annotations

from typing import Any, Protocol


class _HasTriggers(Protocol):
    triggers: list[str]
    regex: bool


def extract_triggers(raw: dict[str, Any]) -> list[str]:
    triggers: list[str] = []
    if "trigger" in raw:
        triggers.append(str(raw["trigger"]))
    if "triggers" in raw:
        triggers.extend(str(item) for item in raw["triggers"])
    return triggers


def find_duplicate_literal_triggers(matches: list[_HasTriggers]) -> list[str]:
    return find_conflicting_literal_triggers(matches)


def find_conflicting_literal_triggers(matches: list[_HasTriggers]) -> list[str]:
    grouped: dict[str, list[Any]] = {}
    for match in matches:
        if match.regex:
            continue
        when = getattr(match, "when", None) or {}
        for trigger in match.triggers:
            grouped.setdefault(trigger, []).append(when)

    conflicts: list[str] = []
    for trigger, conditions in grouped.items():
        if len(conditions) < 2:
            continue
        unconditional = sum(1 for when in conditions if not when)
        if unconditional > 1:
            conflicts.append(trigger)
    return sorted(conflicts)
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
    counts: dict[str, int] = {}
    for match in matches:
        if match.regex:
            continue
        for trigger in match.triggers:
            counts[trigger] = counts.get(trigger, 0) + 1
    return sorted(trigger for trigger, count in counts.items() if count > 1)
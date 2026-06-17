from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RaycastSnippet:
    name: str
    text: str
    keyword: str = ""


def load_raycast_snippets(path: Path) -> list[RaycastSnippet]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    raw_items: list[Any]
    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        raw_items = list(data.get("snippets") or data.get("items") or [])
    else:
        raise ValueError("Raycast export must be a JSON array or object with snippets")

    snippets: list[RaycastSnippet] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        snippets.append(
            RaycastSnippet(
                name=str(item.get("name") or "").strip(),
                text=str(item.get("text") or ""),
                keyword=str(item.get("keyword") or "").strip(),
            )
        )
    return snippets


def convert_raycast_snippet(snippet: RaycastSnippet) -> dict[str, Any] | None:
    trigger = snippet.keyword.strip()
    if not trigger:
        return None

    converted: dict[str, Any] = {
        "trigger": trigger,
        "replace": snippet.text,
    }
    label = snippet.name.strip() or trigger
    converted["label"] = label
    return converted
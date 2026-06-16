from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .app_context import get_frontmost_app, is_app_allowed
from .config import AppConfig, Match
from .renderer import render_match_interactive


@dataclass
class SearchItem:
    trigger: str
    match: Match


def _escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_search_items(matches: list[Match], app_config: AppConfig) -> list[SearchItem]:
    app_name = get_frontmost_app()
    items: list[SearchItem] = []
    for match in matches:
        if not is_app_allowed(
            app_name,
            global_blacklist=app_config.app_blacklist,
            if_app=match.if_app or None,
            unless_app=match.unless_app or None,
        ):
            continue
        for trigger in match.triggers:
            items.append(SearchItem(trigger=trigger, match=match))
    return sorted(items, key=lambda item: item.trigger)


def pick_snippet(items: list[SearchItem]) -> SearchItem | None:
    if not items:
        return None

    labels = [item.trigger for item in items]
    list_literal = ", ".join(f'"{_escape_applescript(label)}"' for label in labels)
    script = f'''
        set choices to {{{list_literal}}}
        set picked to choose from list choices with prompt "Expando — scegli uno snippet"
        if picked is false then
            return ""
        end if
        return item 1 of picked
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    trigger = result.stdout.strip()
    if not trigger:
        return None
    for item in items:
        if item.trigger == trigger:
            return item
    return None


def resolve_snippet_text(item: SearchItem) -> str | None:
    return render_match_interactive(item.match)
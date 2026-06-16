from __future__ import annotations

from dataclasses import dataclass

from .app_context import get_frontmost_context, match_allowed
from .config import AppConfig, Match
from .renderer import render_match
from .ui_bridge import show_search_picker


@dataclass
class SearchItem:
    trigger: str
    match: Match


def build_search_items(matches: list[Match], app_config: AppConfig) -> list[SearchItem]:
    context = get_frontmost_context()
    items: list[SearchItem] = []
    for match in matches:
        if not match_allowed(
            context,
            global_blacklist=app_config.app_blacklist,
            if_app=match.if_app or None,
            unless_app=match.unless_app or None,
            if_bundle=match.if_bundle or None,
            unless_bundle=match.unless_bundle or None,
            if_title=match.if_title or None,
            unless_title=match.unless_title or None,
        ):
            continue
        for trigger in match.triggers:
            items.append(SearchItem(trigger=trigger, match=match))
    return sorted(items, key=lambda item: item.trigger)


def _preview_text(item: SearchItem, app_config: AppConfig) -> str:
    if item.match.form:
        return item.match.replace
    try:
        return render_match(item.match, app_config=app_config)
    except Exception:
        return item.match.replace


def _item_label(item: SearchItem, app_config: AppConfig, trigger_counts: dict[str, int]) -> str:
    if item.match.label:
        return item.match.label
    if trigger_counts.get(item.trigger, 0) <= 1:
        return item.trigger
    preview = _preview_text(item, app_config).strip().splitlines()[0]
    if len(preview) > 48:
        preview = preview[:47] + "…"
    return f"{item.trigger} — {preview}" if preview else item.trigger


def pick_snippet(items: list[SearchItem], app_config: AppConfig | None = None) -> SearchItem | None:
    if not items:
        return None

    app_config = app_config or AppConfig()
    trigger_counts: dict[str, int] = {}
    for item in items:
        trigger_counts[item.trigger] = trigger_counts.get(item.trigger, 0) + 1

    payload = [
        {
            "id": str(index),
            "trigger": item.trigger,
            "label": _item_label(item, app_config, trigger_counts),
            "preview": _preview_text(item, app_config),
            "search_terms": item.match.search_terms,
        }
        for index, item in enumerate(items)
    ]
    picked = show_search_picker(payload)
    if not picked:
        return None

    try:
        index = int(picked.get("id", ""))
    except ValueError:
        return None
    if 0 <= index < len(items):
        return items[index]
    return None


def resolve_snippet_text(item: SearchItem, app_config: AppConfig | None = None) -> str | None:
    from .renderer import render_match_interactive

    return render_match_interactive(item.match, app_config=app_config)
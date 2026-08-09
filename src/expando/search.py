from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .app_context import get_frontmost_context, match_allowed
from .config import AppConfig, Match
from .renderer import render_match
from .ui_bridge import show_search_picker


@dataclass
class SearchItem:
    trigger: str
    match: Match


def build_search_items(
    matches: list[Match],
    app_config: AppConfig,
    *,
    config_dir: Path | None = None,
) -> list[SearchItem]:
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
    return rank_search_items(items, config_dir=config_dir)


def rank_search_items(
    items: list[SearchItem],
    *,
    config_dir: Path | None = None,
) -> list[SearchItem]:
    """Pinned first, then most-used, then alphabetical."""
    pins: list[str] = []
    usage: dict[str, int] = {}
    if config_dir is not None:
        try:
            from .search_pins import load_pins

            pins = load_pins(config_dir)
        except Exception:
            pins = []
        try:
            from .expansion_stats import load_stats

            usage = load_stats(config_dir).by_trigger
        except Exception:
            usage = {}
    pin_rank = {trigger: index for index, trigger in enumerate(pins)}

    def sort_key(item: SearchItem) -> tuple:
        pinned = 0 if item.trigger in pin_rank else 1
        pin_order = pin_rank.get(item.trigger, 10_000)
        freq = -int(usage.get(item.trigger, 0))
        return (pinned, pin_order, freq, item.trigger.casefold())

    return sorted(items, key=sort_key)


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


def pick_snippet(
    items: list[SearchItem],
    app_config: AppConfig | None = None,
    *,
    config_dir: Path | None = None,
) -> SearchItem | None:
    if not items:
        return None

    app_config = app_config or AppConfig()
    if config_dir is not None:
        items = rank_search_items(items, config_dir=config_dir)
    trigger_counts: dict[str, int] = {}
    for item in items:
        trigger_counts[item.trigger] = trigger_counts.get(item.trigger, 0) + 1

    pins: set[str] = set()
    if config_dir is not None:
        try:
            from .search_pins import load_pins

            pins = set(load_pins(config_dir))
        except Exception:
            pins = set()

    payload = [
        {
            "id": str(index),
            "trigger": item.trigger,
            "label": (
                f"★ {_item_label(item, app_config, trigger_counts)}"
                if item.trigger in pins
                else _item_label(item, app_config, trigger_counts)
            ),
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
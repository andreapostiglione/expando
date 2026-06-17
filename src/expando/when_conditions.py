from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from .app_context import AppContext, pattern_matches


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _parse_hour_range(value: str) -> tuple[int, int] | None:
    if "-" not in value:
        return None
    start_raw, end_raw = value.split("-", 1)
    try:
        return int(start_raw.strip()), int(end_raw.strip())
    except ValueError:
        return None


def _hour_in_range(hour: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def evaluate_when(
    when: dict[str, Any],
    context: AppContext,
    *,
    form_values: dict[str, str] | None = None,
    require_form: bool = False,
) -> bool:
    if not when:
        return True

    form_values = form_values or {}

    if "app" in when:
        apps = _as_list(when.get("app"))
        if apps and not pattern_matches(context.name, apps):
            return False

    if "unless_app" in when:
        blocked = _as_list(when.get("unless_app"))
        if blocked and pattern_matches(context.name, blocked):
            return False

    if "bundle" in when:
        bundles = _as_list(when.get("bundle"))
        if bundles and not pattern_matches(context.bundle_id, bundles):
            return False

    if "unless_bundle" in when:
        blocked = _as_list(when.get("unless_bundle"))
        if blocked and pattern_matches(context.bundle_id, blocked):
            return False

    if "title" in when:
        titles = _as_list(when.get("title"))
        if titles and not pattern_matches(context.window_title, titles):
            return False

    hour_spec = when.get("hour")
    if hour_spec is not None:
        parsed = _parse_hour_range(str(hour_spec))
        if parsed is None:
            return False
        start, end = parsed
        if not _hour_in_range(datetime.now().hour, start, end):
            return False

    weekday_spec = when.get("weekday")
    if weekday_spec is not None:
        allowed = {item.casefold()[:3] for item in _as_list(weekday_spec)}
        current = datetime.now().strftime("%a").casefold()
        if allowed and current not in allowed:
            return False

    env_rules = when.get("env") or {}
    if isinstance(env_rules, dict):
        for key, expected in env_rules.items():
            if os.environ.get(str(key), "") != str(expected):
                return False

    form_rules = when.get("form") or {}
    if isinstance(form_rules, dict) and form_rules:
        if require_form and not form_values:
            return False
        for key, expected in form_rules.items():
            if form_values.get(str(key), "") != str(expected):
                return False

    return True


def when_needs_form(when: dict[str, Any]) -> bool:
    form_rules = when.get("form") or {}
    return isinstance(form_rules, dict) and bool(form_rules)
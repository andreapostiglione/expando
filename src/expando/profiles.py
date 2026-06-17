from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from .app_context import app_matches_pattern, get_frontmost_app
from .config import AppConfig


def _load_profile_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _profile_matches_app(profile_data: dict[str, Any], app_name: str | None) -> bool:
    filter_data = profile_data.get("filter", {}) or {}
    app_names = [str(item) for item in filter_data.get("app_names", []) or []]
    if not app_names:
        return False
    return app_matches_pattern(app_name, app_names)


def resolve_app_config(
    config_dir: Path,
    base: AppConfig,
    *,
    app_name: str | None = None,
) -> AppConfig:
    config_directory = config_dir / "config"
    if not config_directory.exists():
        return base

    if app_name is None:
        app_name = get_frontmost_app()
    profile_files = [
        path
        for path in sorted(config_directory.glob("*.yml")) + sorted(config_directory.glob("*.yaml"))
        if path.name != "default.yml"
    ]

    active_data: dict[str, Any] | None = None
    for path in profile_files:
        data = _load_profile_file(path)
        if _profile_matches_app(data, app_name):
            active_data = data
            break

    if not active_data:
        return base

    return replace(
        base,
        toggle_key=str(active_data.get("toggle_key", base.toggle_key)),
        backend=str(active_data.get("backend", base.backend)).lower(),
        auto_restart=bool(active_data.get("auto_restart", base.auto_restart)),
        clipboard_threshold=int(active_data.get("clipboard_threshold", base.clipboard_threshold)),
        max_regex_buffer_size=int(active_data.get("max_regex_buffer_size", base.max_regex_buffer_size)),
        enabled=bool(active_data.get("enabled", base.enabled)),
        app_blacklist=[str(item) for item in active_data.get("app_blacklist", base.app_blacklist) or base.app_blacklist],
        shell_allowlist=[str(item) for item in active_data.get("shell_allowlist", base.shell_allowlist) or base.shell_allowlist],
        search_shortcut=str(active_data.get("search_shortcut", base.search_shortcut)),
    )
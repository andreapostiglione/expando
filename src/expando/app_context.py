from __future__ import annotations

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def get_frontmost_app() -> str | None:
    if platform.system() != "Darwin":
        return None
    try:
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get name of first application process whose frontmost is true',
            ],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode != 0:
            return None
        name = result.stdout.strip()
        return name or None
    except Exception:
        logger.debug("Could not detect frontmost app", exc_info=True)
        return None


def app_matches_pattern(app_name: str | None, patterns: list[str]) -> bool:
    if not patterns:
        return False
    if not app_name:
        return False
    lowered = app_name.casefold()
    return any(pattern.casefold() in lowered or lowered in pattern.casefold() for pattern in patterns)


def is_app_allowed(
    app_name: str | None,
    *,
    global_blacklist: list[str],
    if_app: list[str] | None = None,
    unless_app: list[str] | None = None,
) -> bool:
    if app_matches_pattern(app_name, global_blacklist):
        return False
    if unless_app and app_matches_pattern(app_name, unless_app):
        return False
    if if_app:
        return app_matches_pattern(app_name, if_app)
    return True
from __future__ import annotations

import logging
import platform
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppContext:
    name: str | None = None
    bundle_id: str | None = None
    window_title: str | None = None


def _run_applescript(script: str) -> str | None:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None
    except Exception:
        logger.debug("AppleScript call failed", exc_info=True)
        return None


def get_frontmost_context() -> AppContext:
    if platform.system() != "Darwin":
        return AppContext()

    script = '''
        tell application "System Events"
            set frontProc to first application process whose frontmost is true
            set appName to name of frontProc
            set bundleId to bundle identifier of frontProc
            set winTitle to ""
            try
                if (count of windows of frontProc) > 0 then
                    set winTitle to name of front window of frontProc
                end if
            end try
            return appName & linefeed & bundleId & linefeed & winTitle
        end tell
    '''
    raw = _run_applescript(script)
    if not raw:
        return AppContext()

    parts = raw.splitlines()
    name = parts[0] if len(parts) > 0 and parts[0] else None
    bundle_id = parts[1] if len(parts) > 1 and parts[1] else None
    window_title = parts[2] if len(parts) > 2 and parts[2] else None
    return AppContext(name=name, bundle_id=bundle_id, window_title=window_title)


def get_frontmost_app() -> str | None:
    return get_frontmost_context().name


def pattern_matches(value: str | None, patterns: list[str]) -> bool:
    return _pattern_matches(value, patterns)


def app_matches_pattern(app_name: str | None, patterns: list[str]) -> bool:
    return _pattern_matches(app_name, patterns)


def _pattern_matches(value: str | None, patterns: list[str]) -> bool:
    if not patterns:
        return False
    if not value:
        return False
    lowered = value.casefold()
    return any(
        pattern.casefold() in lowered or lowered in pattern.casefold()
        for pattern in patterns
    )


def is_context_allowed(
    context: AppContext,
    *,
    global_blacklist: list[str],
    if_app: list[str] | None = None,
    unless_app: list[str] | None = None,
    if_bundle: list[str] | None = None,
    unless_bundle: list[str] | None = None,
    if_title: list[str] | None = None,
    unless_title: list[str] | None = None,
) -> bool:
    if pattern_matches(context.name, global_blacklist):
        return False
    if unless_app and pattern_matches(context.name, unless_app):
        return False
    if unless_bundle and pattern_matches(context.bundle_id, unless_bundle):
        return False
    if unless_title and pattern_matches(context.window_title, unless_title):
        return False

    if if_app and not pattern_matches(context.name, if_app):
        return False
    if if_bundle and not pattern_matches(context.bundle_id, if_bundle):
        return False
    if if_title and not pattern_matches(context.window_title, if_title):
        return False
    return True


def is_app_allowed(
    app_name: str | None,
    *,
    global_blacklist: list[str],
    if_app: list[str] | None = None,
    unless_app: list[str] | None = None,
    if_bundle: list[str] | None = None,
    unless_bundle: list[str] | None = None,
    if_title: list[str] | None = None,
    unless_title: list[str] | None = None,
) -> bool:
    return is_context_allowed(
        AppContext(name=app_name),
        global_blacklist=global_blacklist,
        if_app=if_app,
        unless_app=unless_app,
        if_bundle=if_bundle,
        unless_bundle=unless_bundle,
        if_title=if_title,
        unless_title=unless_title,
    )


match_allowed = is_context_allowed
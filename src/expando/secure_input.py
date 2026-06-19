from __future__ import annotations

import ctypes
import logging
import platform
import subprocess

from .runtime_cache import TimedCache

logger = logging.getLogger(__name__)

_SECURE_INPUT_CACHE = TimedCache[bool](ttl_seconds=0.5)


def invalidate_secure_input_cache() -> None:
    _SECURE_INPUT_CACHE.invalidate()


def _probe_secure_input_native() -> bool | None:
    if platform.system() != "Darwin":
        return None
    try:
        carbon = ctypes.CDLL(
            "/System/Library/Frameworks/Carbon.framework/Carbon",
            use_errno=True,
        )
        carbon.IsSecureEventInputEnabled.restype = ctypes.c_bool
        return bool(carbon.IsSecureEventInputEnabled())
    except Exception:
        logger.debug("Native secure input probe failed", exc_info=True)
        return None


def _probe_secure_input_ax() -> bool:
    script = '''
        tell application "System Events"
            set frontProc to first application process whose frontmost is true
            try
                set frontWindow to front window of frontProc
                set focusedElement to value of attribute "AXFocusedUIElement" of frontWindow
                set elementRole to value of attribute "AXRole" of focusedElement
                set elementSubrole to ""
                try
                    set elementSubrole to value of attribute "AXSubrole" of focusedElement
                end try
                return elementRole & linefeed & elementSubrole
            on error
                return ""
            end try
        end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
        if result.returncode != 0:
            return False
        parts = result.stdout.strip().splitlines()
        role = parts[0] if parts else ""
        subrole = parts[1] if len(parts) > 1 else ""
        if "AXSecureTextField" in subrole:
            return True
        if subrole in {"AXPasswordField", "AXSecureTextField"}:
            return True
        if role == "AXTextField" and "secure" in subrole.casefold():
            return True
    except Exception:
        logger.debug("Secure input check failed", exc_info=True)
    return False


def _probe_secure_input_active() -> bool:
    native = _probe_secure_input_native()
    if native is True:
        return True
    ax = _probe_secure_input_ax()
    if native is False:
        return ax
    return ax


def is_secure_input_active() -> bool:
    if platform.system() != "Darwin":
        return False
    return _SECURE_INPUT_CACHE.get(_probe_secure_input_active)
from __future__ import annotations

import logging
import platform
import subprocess

logger = logging.getLogger(__name__)


def is_secure_input_active() -> bool:
    if platform.system() != "Darwin":
        return False

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
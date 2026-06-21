from __future__ import annotations

import logging
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def notify(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return
    script = (
        f'display notification {_applescript_string(message)} '
        f"with title {_applescript_string(title)}"
    )
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.debug(
            "osascript notification failed (%s): %s",
            result.returncode,
            (result.stderr or result.stdout).strip(),
        )


def show_info_alert(title: str, message: str) -> None:
    """Show a native macOS alert (reliable in dev/menu-bar mode)."""
    if platform.system() != "Darwin":
        return

    def _show() -> None:
        from AppKit import NSAlert, NSInformationalAlertStyle

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSInformationalAlertStyle)
        alert.runModal()

    try:
        from .ui_main_thread import call_on_main_thread

        call_on_main_thread(_show, wait=True)
    except Exception:
        logger.debug("Native alert failed; falling back to notification", exc_info=True)
        notify(title, message)


def reveal_in_finder(path: Path | str) -> None:
    if platform.system() != "Darwin":
        return
    subprocess.run(["open", "-R", str(path)], check=False)


def notify_toggle(enabled: bool) -> None:
    from .i18n import t

    key = "menubar.toggle_enabled" if enabled else "menubar.toggle_disabled"
    notify("Expando", t(key))


def _applescript_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'
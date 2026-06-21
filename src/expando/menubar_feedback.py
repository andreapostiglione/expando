from __future__ import annotations

import logging
from pathlib import Path

from .backup import backup_label
from .i18n import t, tf
from .notifications import reveal_in_finder, show_info_alert

logger = logging.getLogger(__name__)

__all__ = ["backup_label", "user_confirm", "user_error", "user_info", "user_success"]


def user_success(message: str, *, reveal: Path | None = None) -> None:
    show_info_alert("Expando", message)
    if reveal is not None:
        reveal_in_finder(reveal)


def user_info(message: str) -> None:
    show_info_alert("Expando", message)


def user_error(message: str) -> None:
    show_info_alert("Expando", message)


def user_confirm(message: str, informative: str = "") -> bool:
    """Return True when the user accepts the confirmation dialog."""

    def _ask() -> bool:
        from AppKit import (
            NSAlert,
            NSAlertFirstButtonReturn,
            NSAlertSecondButtonReturn,
            NSWarningAlertStyle,
        )

        alert = NSAlert.alloc().init()
        alert.setMessageText_(message)
        if informative:
            alert.setInformativeText_(informative)
        alert.setAlertStyle_(NSWarningAlertStyle)
        alert.addButtonWithTitle_(t("ui.cancel"))
        alert.addButtonWithTitle_(t("ui.confirm"))
        return alert.runModal() == NSAlertSecondButtonReturn

    try:
        from .ui_main_thread import call_on_main_thread

        return bool(call_on_main_thread(_ask, wait=True))
    except Exception as exc:
        logger.exception("Confirm dialog failed")
        user_error(tf("menubar.action_failed", error=exc))
        return False
from __future__ import annotations

import threading
import time

_UI_ACTIVE_TIMEOUT_SECONDS = 320.0

_ui_active = threading.Event()
_ui_active_since = 0.0


def set_ui_active(active: bool) -> None:
    global _ui_active_since
    if active:
        _ui_active.set()
        _ui_active_since = time.monotonic()
    else:
        _ui_active.clear()
        _ui_active_since = 0.0


def clear_ui_active() -> None:
    set_ui_active(False)


def is_ui_active() -> bool:
    if not _ui_active.is_set():
        return False
    if _ui_active_since and (time.monotonic() - _ui_active_since) > _UI_ACTIVE_TIMEOUT_SECONDS:
        clear_ui_active()
        return False
    return True
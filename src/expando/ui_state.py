from __future__ import annotations

import threading

_ui_active = threading.Event()


def set_ui_active(active: bool) -> None:
    if active:
        _ui_active.set()
    else:
        _ui_active.clear()


def is_ui_active() -> bool:
    return _ui_active.is_set()
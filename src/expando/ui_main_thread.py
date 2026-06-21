from __future__ import annotations

import logging
import sys
import threading
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _ns_app_running() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        from AppKit import NSApplication

        return bool(NSApplication.sharedApplication().isRunning())
    except Exception:
        return False


def _on_appkit_main_thread() -> bool:
    if sys.platform != "darwin":
        return threading.current_thread() is threading.main_thread()
    try:
        from Foundation import NSThread

        return bool(NSThread.isMainThread())
    except Exception:
        return threading.current_thread() is threading.main_thread()


def call_on_main_thread(func: Callable[[], T], *, wait: bool = True, timeout: float = 300.0) -> T | None:
    """Run *func* on the AppKit main thread."""
    if _on_appkit_main_thread():
        return func()

    result: list[T] = []
    error: list[BaseException] = []
    done = threading.Event()

    def _runner() -> None:
        try:
            result.append(func())
        except BaseException as exc:  # pragma: no cover - propagated to caller
            error.append(exc)
        finally:
            done.set()

    try:
        from PyObjCTools.AppHelper import callAfter
    except Exception as exc:
        if wait:
            raise RuntimeError(
                "PyObjCTools unavailable; cannot run main-thread UI work"
            ) from exc
        logger.warning("PyObjCTools unavailable; skipping main-thread UI work", exc_info=True)
        return None

    callAfter(_runner)
    if not wait:
        return None
    if not done.wait(timeout):
        raise TimeoutError("Timed out waiting for main-thread UI work")
    if error:
        raise error[0]
    return result[0] if result else None
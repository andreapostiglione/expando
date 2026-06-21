from __future__ import annotations

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 2.0
DEFAULT_STALE_SECONDS = 5.0
DEFAULT_RETRY_SECONDS = 30.0


class ListenerWatchdog:
    """Monitors pynput listener liveness and restarts it when the thread dies."""

    def __init__(
        self,
        *,
        is_alive: Callable[[], bool],
        restart: Callable[[], None],
        on_dead: Callable[[], None] | None = None,
        on_recovered: Callable[[], None] | None = None,
        interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        retry_seconds: float = DEFAULT_RETRY_SECONDS,
    ) -> None:
        self._is_alive = is_alive
        self._restart = restart
        self._on_dead = on_dead
        self._on_recovered = on_recovered
        self._interval = interval_seconds
        self._retry_seconds = retry_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._dead_notified = False
        self._last_heartbeat = time.monotonic()
        self._last_restart_attempt = 0.0

    def touch(self) -> None:
        self._last_heartbeat = time.monotonic()

    def listener_dead(self) -> bool:
        if self._is_alive():
            return False
        return (time.monotonic() - self._last_heartbeat) >= DEFAULT_STALE_SECONDS

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="expando-listener-watchdog", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            alive = self._is_alive()
            if alive:
                self.touch()
                if self._dead_notified:
                    self._dead_notified = False
                    if self._on_recovered:
                        try:
                            self._on_recovered()
                        except Exception:
                            logger.exception("Listener watchdog recovery callback failed")
                continue

            now = time.monotonic()
            if self._dead_notified and (now - self._last_restart_attempt) < self._retry_seconds:
                continue

            if not self._dead_notified:
                logger.warning("Keyboard listener thread is not alive; attempting restart")
                self._dead_notified = True
                if self._on_dead:
                    try:
                        self._on_dead()
                    except Exception:
                        logger.exception("Listener watchdog dead callback failed")
            else:
                logger.warning(
                    "Keyboard listener still dead; retrying restart (interval=%ss)",
                    self._retry_seconds,
                )

            self._last_restart_attempt = now
            try:
                self._restart()
                if self._is_alive():
                    logger.info("Keyboard listener restarted successfully")
                    self.touch()
                    self._dead_notified = False
                    if self._on_recovered:
                        try:
                            self._on_recovered()
                        except Exception:
                            logger.exception("Listener watchdog recovery callback failed")
                else:
                    logger.error("Keyboard listener restart did not recover liveness")
            except Exception:
                logger.exception("Failed to restart keyboard listener")
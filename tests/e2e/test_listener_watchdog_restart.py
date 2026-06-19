from __future__ import annotations

import platform
import time
from unittest.mock import MagicMock

import pytest

from expando.listener import KeyboardService
from expando.listener_watchdog import ListenerWatchdog

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only"),
]


def test_listener_watchdog_restarts_dead_listener(e2e_config_dir):
    from expando.engine import build_engine

    engine = build_engine(e2e_config_dir)
    service = KeyboardService(e2e_config_dir, engine)
    restarts: list[str] = []

    original_restart = service.restart_listener

    def traced_restart() -> None:
        restarts.append("restart")
        original_restart()

    service.restart_listener = traced_restart  # type: ignore[method-assign]
    service._listener = None
    watchdog = ListenerWatchdog(
        is_alive=service.is_listener_alive,
        restart=service.restart_listener,
        interval_seconds=0.05,
    )
    watchdog.start()
    try:
        time.sleep(0.25)
        assert restarts
        assert service.is_listener_alive()
    finally:
        watchdog.stop()
        if service._listener:
            service._listener.stop()


@pytest.mark.integration
def test_service_watchdog_recovers(require_full_e2e, e2e_config_dir):
    from expando.engine import build_engine

    engine = build_engine(e2e_config_dir)
    service = KeyboardService(e2e_config_dir, engine)
    service.restart_listener()
    service._watchdog.start()
    try:
        if service._listener:
            service._listener.stop()
            service._listener = None
        time.sleep(3.0)
        assert service.is_listener_alive()
    finally:
        service.stop()
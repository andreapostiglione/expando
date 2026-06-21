from unittest.mock import MagicMock

from expando.listener_watchdog import ListenerWatchdog


def test_watchdog_restarts_dead_listener():
    alive = {"value": True}
    restarts: list[str] = []

    def is_alive() -> bool:
        return alive["value"]

    def restart() -> None:
        restarts.append("restart")
        alive["value"] = True

    alive["value"] = False
    watchdog = ListenerWatchdog(
        is_alive=is_alive,
        restart=restart,
        interval_seconds=0.05,
    )
    watchdog.start()
    import time

    time.sleep(0.2)
    watchdog.stop()
    assert restarts
    assert alive["value"] is True


def test_watchdog_calls_on_dead_callback():
    dead_calls: list[str] = []
    watchdog = ListenerWatchdog(
        is_alive=lambda: False,
        restart=MagicMock(),
        on_dead=lambda: dead_calls.append("dead"),
        interval_seconds=0.05,
    )
    watchdog.start()
    import time

    time.sleep(0.2)
    watchdog.stop()
    assert dead_calls == ["dead"]


def test_watchdog_retries_after_failed_restart():
    alive = {"value": False}
    restart_attempts: list[str] = []

    def restart() -> None:
        restart_attempts.append("restart")

    watchdog = ListenerWatchdog(
        is_alive=lambda: alive["value"],
        restart=restart,
        interval_seconds=0.05,
        retry_seconds=0.12,
    )
    watchdog.start()
    import time

    time.sleep(0.35)
    watchdog.stop()
    assert len(restart_attempts) >= 2
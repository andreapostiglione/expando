from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from expando.app_context import AppContext
from expando.listener import build_service


class _KeyChar:
    def __init__(self, char: str) -> None:
        self.char = char


@pytest.fixture
def worker_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "toggle_key: ALT\nauto_restart: false\nrespect_secure_input: false\n",
        encoding="utf-8",
    )
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':hi'\n    replace: 'Hello'\n",
        encoding="utf-8",
    )
    return config_dir


def test_async_worker_expands_trigger(worker_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="TextEdit"),
    )
    # Avoid real pynput listener / permissions in unit tests.
    service = build_service(worker_config)
    service.engine.injector.inject = MagicMock()
    service.engine.injector.delete_chars = MagicMock()
    service.restart_listener = MagicMock()  # type: ignore[method-assign]
    service._schedule_permission_check = MagicMock()  # type: ignore[method-assign]
    service._sync_file_watcher = MagicMock()  # type: ignore[method-assign]
    service._watchdog.start = MagicMock()  # type: ignore[method-assign]
    service._watchdog.stop = MagicMock()  # type: ignore[method-assign]
    service.is_listener_alive = MagicMock(return_value=True)  # type: ignore[method-assign]

    service._start_key_worker()
    try:
        assert service._async_enabled
        assert service._worker is not None and service._worker.is_alive()
        for char in ":hi":
            service._on_press(_KeyChar(char))
        # Barrier: wait until the queue has drained past our key events.
        import threading

        done = threading.Event()
        service._event_queue.put(done.set)
        assert done.wait(3.0), "key worker did not drain queue"
        assert service.engine.injector.inject.called
    finally:
        service._stop_key_worker()

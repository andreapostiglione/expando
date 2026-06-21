from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from expando.listener import KeyboardService


@pytest.fixture
def keyboard_service(monkeypatch: pytest.MonkeyPatch) -> KeyboardService:
    engine = MagicMock()
    engine.enabled = True
    engine.config.app.clipboard_threshold = 9999
    engine._base_bundle.app.toggle_key = "OFF"
    engine._base_bundle.app.auto_restart = False
    engine._base_bundle.matches = []
    service = KeyboardService(config_dir=MagicMock(), engine=engine)
    monkeypatch.setattr("expando.listener.pick_snippet", lambda *_a, **_k: SimpleNamespace(
        trigger=":a", match=SimpleNamespace(force_clipboard=False)
    ))
    monkeypatch.setattr("expando.listener.resolve_snippet_text", lambda *_a, **_k: "A")
    monkeypatch.setattr("expando.listener.build_search_items", lambda *_a, **_k: [])
    monkeypatch.setattr("expando.app_context.restore_frontmost_application", lambda *_a, **_k: None)
    monkeypatch.setattr("expando.app_context.capture_frontmost_application_pid", lambda: None)
    monkeypatch.setattr("expando.listener.threading.Timer", lambda *_a, **_k: SimpleNamespace(start=lambda: None))
    return service


def test_injecting_depth_tracks_overlapping_sessions(keyboard_service: KeyboardService) -> None:
    keyboard_service._set_injecting(True)
    keyboard_service._set_injecting(True)
    assert keyboard_service._is_injecting() is True
    keyboard_service._set_injecting(False)
    assert keyboard_service._is_injecting() is True
    keyboard_service._set_injecting(False)
    assert keyboard_service._is_injecting() is False
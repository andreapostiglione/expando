from __future__ import annotations

import threading
from unittest.mock import patch

from expando.ui_main_thread import call_on_main_thread


def test_call_on_main_thread_schedules_from_background(monkeypatch) -> None:
    monkeypatch.setattr("expando.ui_main_thread._on_appkit_main_thread", lambda: False)
    monkeypatch.setattr("expando.ui_main_thread._ns_app_running", lambda: False)
    calls: list[str] = []

    def fake_call_after(func):
        calls.append("scheduled")
        func()

    with patch("PyObjCTools.AppHelper.callAfter", side_effect=fake_call_after):
        assert call_on_main_thread(lambda: calls.append("ran")) is None

    assert calls == ["scheduled", "ran"]


def test_call_on_main_thread_inline_on_appkit_main(monkeypatch) -> None:
    monkeypatch.setattr("expando.ui_main_thread._on_appkit_main_thread", lambda: True)
    assert call_on_main_thread(lambda: "ok", wait=False) == "ok"


def test_call_on_main_thread_waits_for_result(monkeypatch) -> None:
    monkeypatch.setattr("expando.ui_main_thread._on_appkit_main_thread", lambda: False)

    def fake_call_after(func):
        func()

    with patch(
        "expando.ui_main_thread.threading.current_thread",
        return_value=threading.Thread(),
    ), patch("PyObjCTools.AppHelper.callAfter", side_effect=fake_call_after):
        assert call_on_main_thread(lambda: "scheduled") == "scheduled"
from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pynput.keyboard import Key

from expando.listener import ConfigReloader, KeyboardService


class _KeyChar:
    def __init__(self, char: str) -> None:
        self.char = char


def _type_chars(service: KeyboardService, text: str) -> None:
    for char in text:
        service._on_release(_KeyChar(char))


def test_listener_expands_on_char_release(keyboard_service: KeyboardService):
    _type_chars(keyboard_service, ":hi")
    keyboard_service.engine.injector.delete_chars.assert_called_once_with(3)
    keyboard_service.engine.injector.inject.assert_called_once_with(
        "Hello",
        force_clipboard=False,
        cursor_left=None,
    )


def test_listener_double_alt_toggles(keyboard_service: KeyboardService):
    toggled: list[bool] = []
    keyboard_service.on_toggle = lambda: toggled.append(keyboard_service.engine.enabled)

    now = time.time()
    with patch("expando.listener.time.time", side_effect=[now, now + 0.1]):
        keyboard_service._on_press(Key.alt)
        keyboard_service._on_press(Key.alt)

    assert keyboard_service.engine.enabled is False
    assert toggled == [False]


def test_listener_undo_shortcut(keyboard_service: KeyboardService):
    _type_chars(keyboard_service, ":hi")
    inject = keyboard_service.engine.injector.inject
    delete_chars = keyboard_service.engine.injector.delete_chars
    inject.reset_mock()
    delete_chars.reset_mock()

    keyboard_service._track_modifier_press(Key.cmd)
    keyboard_service._track_modifier_press(Key.shift)
    keyboard_service._on_press(_KeyChar("z"))

    delete_chars.assert_called()
    inject.assert_called_with(":hi")


def test_listener_skips_expansion_while_injecting(keyboard_service: KeyboardService):
    keyboard_service._set_injecting(True)
    _type_chars(keyboard_service, ":hi")
    keyboard_service.engine.injector.inject.assert_not_called()


def test_listener_skips_when_ui_active(keyboard_service: KeyboardService, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("expando.listener.is_ui_active", lambda: True)
    _type_chars(keyboard_service, ":hi")
    keyboard_service.engine.injector.inject.assert_not_called()


def test_listener_config_reload_picks_up_new_match(
    keyboard_service: KeyboardService,
    isolated_config_dir: Path,
):
    match_file = isolated_config_dir / "match" / "base.yml"
    match_file.write_text(
        "matches:\n  - trigger: ':bye'\n    replace: 'Goodbye'\n",
        encoding="utf-8",
    )
    keyboard_service.apply_config_reload()
    keyboard_service.engine.injector.inject.reset_mock()
    keyboard_service.engine.injector.delete_chars.reset_mock()
    _type_chars(keyboard_service, ":bye")
    keyboard_service.engine.injector.inject.assert_called_once_with(
        "Goodbye",
        force_clipboard=False,
        cursor_left=None,
    )


def test_listener_open_search_injects_picked_snippet(keyboard_service: KeyboardService, monkeypatch: pytest.MonkeyPatch):
    picked = SimpleNamespace(trigger=":hi", match=keyboard_service.engine._base_bundle.matches[0])
    monkeypatch.setattr("expando.listener.pick_snippet", lambda *_args, **_kwargs: picked)
    monkeypatch.setattr("expando.listener.resolve_snippet_text", lambda *_args, **_kwargs: "Hello")

    keyboard_service.open_search()

    keyboard_service.engine.injector.inject.assert_called_once()


def test_config_reloader_invokes_callback():
    calls: list[str] = []

    class Handler(ConfigReloader):
        def on_any_event(self, event) -> None:
            super().on_any_event(event)

    handler = ConfigReloader(lambda: calls.append("reload"))
    event = SimpleNamespace(is_directory=False, src_path="/tmp/match/base.yml")
    handler.on_any_event(event)
    assert calls == ["reload"]
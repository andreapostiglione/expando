from __future__ import annotations

import threading
from contextlib import contextmanager

from pynput.keyboard import Key

from expando.injector import InjectorSettings, TextInjector


class _FakeKeyboard:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    def type(self, char: str) -> None:
        self.events.append(("type", char))

    def press(self, key: object) -> None:
        self.events.append(("press", key))

    def release(self, key: object) -> None:
        self.events.append(("release", key))

    @contextmanager
    def pressed(self, key: object):
        self.press(key)
        try:
            yield
        finally:
            self.release(key)


def test_inject_with_cursor_hint_does_not_deadlock():
    injector = TextInjector(InjectorSettings(backend="inject"))
    keyboard = _FakeKeyboard()
    injector.keyboard = keyboard  # type: ignore[assignment]

    thread = threading.Thread(target=lambda: injector.inject("ab", cursor_left=1))
    thread.start()
    thread.join(timeout=1)

    assert not thread.is_alive()
    assert ("press", Key.left) in keyboard.events

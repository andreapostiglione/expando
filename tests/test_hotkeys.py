from pynput.keyboard import Key

from expando.hotkeys import parse_shortcut, shortcut_pressed


def test_parse_shortcut():
    keys = parse_shortcut("CMD+SHIFT+E")
    assert Key.cmd in keys
    assert Key.shift in keys
    assert "e" in keys


def test_shortcut_pressed():
    pressed = {Key.cmd, Key.shift}
    assert shortcut_pressed("CMD+SHIFT+E", pressed, KeyCodeMock("e")) is True


class KeyCodeMock:
    def __init__(self, char: str):
        self.char = char
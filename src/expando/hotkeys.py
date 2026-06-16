from __future__ import annotations

from pynput.keyboard import Key


MODIFIER_MAP = {
    "CMD": Key.cmd,
    "CTRL": Key.ctrl,
    "ALT": Key.alt,
    "SHIFT": Key.shift,
}


def parse_shortcut(spec: str) -> set:
    parts = [part.strip().upper() for part in spec.split("+") if part.strip()]
    keys: set = set()
    for part in parts:
        if part in MODIFIER_MAP:
            keys.add(MODIFIER_MAP[part])
        elif len(part) == 1:
            keys.add(part.lower())
        else:
            special = getattr(Key, part.lower(), None)
            if special is not None:
                keys.add(special)
    return keys


def shortcut_pressed(spec: str, pressed_modifiers: set, key) -> bool:
    expected = parse_shortcut(spec)
    expected_modifiers = {item for item in expected if item in MODIFIER_MAP.values()}
    expected_keys = expected - expected_modifiers

    if expected_modifiers and not expected_modifiers.issubset(pressed_modifiers):
        return False

    if not expected_keys:
        return False

    if hasattr(key, "char") and key.char is not None:
        actual = key.char.lower()
    else:
        actual = key

    return actual in expected_keys
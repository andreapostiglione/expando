from __future__ import annotations

import re


def _trigger_letters(typed_trigger: str) -> str:
    return "".join(char for char in typed_trigger if char.isalpha())


def apply_propagate_case(trigger: str, replacement: str, typed_trigger: str, uppercase_style: str = "") -> str:
    if not typed_trigger or typed_trigger.lower() != trigger.lower():
        return replacement

    letters = _trigger_letters(typed_trigger)
    if not letters:
        return replacement

    if letters.isupper():
        if uppercase_style == "capitalize_words":
            return replacement.title()
        return replacement.upper()
    if letters[0].isupper():
        if uppercase_style == "capitalize_words":
            return replacement.title()
        return replacement[0].upper() + replacement[1:] if replacement else replacement
    return replacement


def decode_unicode_escapes(text: str) -> str:
    def replace_surrogate_pair(match: re.Match[str]) -> str:
        high = int(match.group(1), 16)
        low = int(match.group(2), 16)
        codepoint = (high - 0xD800) * 0x400 + (low - 0xDC00) + 0x10000
        return chr(codepoint)

    def replace_hex(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    def replace_unicode_short(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    def replace_unicode_long(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    text = re.sub(
        r"\\u([Dd][89aAbB][0-9A-Fa-f]{2})\\u([Dd][c-fC-F][0-9A-Fa-f]{2})",
        replace_surrogate_pair,
        text,
    )
    text = re.sub(r"\\x([0-9A-Fa-f]{2})", replace_hex, text)
    text = re.sub(r"\\u([0-9A-Fa-f]{4})", replace_unicode_short, text)
    text = re.sub(r"\\U([0-9A-Fa-f]{8})", replace_unicode_long, text)
    return text


def strip_cursor_hint(text: str) -> tuple[str, int | None]:
    marker = "$|$"
    if marker not in text:
        return text, None
    index = text.index(marker)
    cleaned = text.replace(marker, "", 1)
    chars_after = len(cleaned) - index
    return cleaned, chars_after


def apply_trim(text: str) -> str:
    return text.strip()
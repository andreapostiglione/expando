from expando.text_transform import (
    apply_propagate_case,
    apply_trim,
    decode_unicode_escapes,
    strip_cursor_hint,
)


def test_propagate_case_upper():
    assert apply_propagate_case(":hi", "hello", ":HI") == "HELLO"


def test_propagate_case_capitalize():
    assert apply_propagate_case(":hi", "hello world", ":Hi", uppercase_style="capitalize_words") == "Hello World"


def test_decode_unicode_escapes():
    assert decode_unicode_escapes(r"\u0041\ud83d\ude00") == "A😀"


def test_strip_cursor_hint():
    text, offset = strip_cursor_hint("Hello $|$world")
    assert text == "Hello world"
    assert offset == 5


def test_apply_trim():
    assert apply_trim("  spaced  ") == "spaced"
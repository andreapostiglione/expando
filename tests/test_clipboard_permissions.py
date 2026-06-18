from expando.permissions import clipboard_injection_ready


def test_clipboard_injection_ready_returns_bool_or_none():
    result = clipboard_injection_ready()
    assert result is None or isinstance(result, bool)
from expando.inject_profiles import (
    STANDARD_PROFILE,
    TERMINAL_PROFILE,
    is_terminal_app,
    resolve_inject_profile,
)


def test_terminal_detection_by_name_and_bundle():
    assert is_terminal_app("Warp")
    assert is_terminal_app("iTerm2")
    assert is_terminal_app(None, "com.apple.Terminal")
    assert is_terminal_app(None, "com.todesktop.230313mzl4w4u92")
    assert not is_terminal_app("Safari")
    assert not is_terminal_app(None, "com.apple.Safari")


def test_resolve_profiles():
    assert resolve_inject_profile("Terminal").name == TERMINAL_PROFILE.name
    assert resolve_inject_profile("TextEdit").name == STANDARD_PROFILE.name
    assert resolve_inject_profile("Terminal").force_clipboard is True
    assert resolve_inject_profile("Notes").force_clipboard is False


def test_extra_terminal_apps():
    assert is_terminal_app("MyCustomTerm", extra_apps=["MyCustomTerm"])
    assert resolve_inject_profile("MyCustomTerm", extra_terminal_apps=["MyCustomTerm"]).name == "terminal"

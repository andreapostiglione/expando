from expando.app_context import app_matches_pattern, is_app_allowed


def test_app_matches_pattern_partial():
    assert app_matches_pattern("Terminal", ["terminal"]) is True
    assert app_matches_pattern("iTerm2", ["iTerm"]) is True


def test_is_app_allowed_with_if_app():
    assert is_app_allowed("Terminal", global_blacklist=[], if_app=["Terminal"]) is True
    assert is_app_allowed("Safari", global_blacklist=[], if_app=["Terminal"]) is False


def test_is_app_allowed_with_blacklist():
    assert is_app_allowed("1Password", global_blacklist=["1Password"]) is False
    assert is_app_allowed("Terminal", global_blacklist=["1Password"]) is True
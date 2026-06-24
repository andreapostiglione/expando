from expando.app_context import (
    AppContext,
    app_matches_pattern,
    is_context_allowed,
    pattern_matches,
)


def test_app_matches_pattern_partial():
    assert app_matches_pattern("Terminal", ["terminal"]) is True
    assert app_matches_pattern("iTerm2", ["iTerm"]) is True


def test_is_context_allowed_with_if_app():
    ctx = AppContext(name="Terminal")
    assert is_context_allowed(ctx, global_blacklist=[], if_app=["Terminal"]) is True
    ctx2 = AppContext(name="Safari")
    assert is_context_allowed(ctx2, global_blacklist=[], if_app=["Terminal"]) is False


def test_is_context_allowed_with_blacklist():
    ctx = AppContext(name="1Password")
    assert is_context_allowed(ctx, global_blacklist=["1Password"]) is False
    ctx2 = AppContext(name="Terminal")
    assert is_context_allowed(ctx2, global_blacklist=["1Password"]) is True


def test_context_bundle_filter():
    context = AppContext(name="Terminal", bundle_id="com.apple.Terminal")
    assert is_context_allowed(
        context,
        global_blacklist=[],
        if_bundle=["com.apple.Terminal"],
    )
    assert not is_context_allowed(
        context,
        global_blacklist=[],
        unless_bundle=["com.apple.Terminal"],
    )


def test_context_title_filter():
    context = AppContext(name="Cursor", window_title="expando — README.md")
    assert is_context_allowed(
        context,
        global_blacklist=[],
        if_title=["README"],
    )
    assert not is_context_allowed(
        context,
        global_blacklist=[],
        unless_title=["README"],
    )


def test_pattern_matches_partial_bundle_id():
    assert pattern_matches("com.apple.Terminal", ["Terminal"]) is True
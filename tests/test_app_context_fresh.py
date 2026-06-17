from unittest.mock import patch

from expando.app_context import AppContext, get_frontmost_context


def test_nsworkspace_context_is_not_cached_across_app_switches():
    iterm = AppContext(name="iTerm2", bundle_id="com.googlecode.iterm2")
    claude = AppContext(name="Claude", bundle_id="com.anthropic.claudefordesktop")

    with patch(
        "expando.app_context._fetch_frontmost_context_nsworkspace",
        side_effect=[claude, iterm],
    ) as fetch:
        first = get_frontmost_context()
        second = get_frontmost_context()

    assert first == claude
    assert second == iterm
    assert fetch.call_count == 2
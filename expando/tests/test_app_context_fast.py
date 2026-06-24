from unittest.mock import patch

from expando.app_context import AppContext, get_frontmost_context, _CONTEXT_CACHE


def test_frontmost_context_prefers_nsworkspace_over_applescript():
    _CONTEXT_CACHE.invalidate()
    fast = AppContext(name="Cursor", bundle_id="com.todesktop.cursor")
    with patch(
        "expando.app_context._fetch_frontmost_context_nsworkspace",
        return_value=fast,
    ), patch("expando.app_context._run_applescript") as applescript:
        context = get_frontmost_context()
    assert context == fast
    applescript.assert_not_called()
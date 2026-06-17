import time
from unittest.mock import patch

from expando.app_context import (
    AppContext,
    get_frontmost_context,
    invalidate_frontmost_context_cache,
)
from expando.secure_input import invalidate_secure_input_cache, is_secure_input_active


def test_frontmost_context_cache_reuses_result_within_ttl():
    invalidate_frontmost_context_cache()
    with patch(
        "expando.app_context._fetch_frontmost_context_nsworkspace",
        return_value=None,
    ), patch(
        "expando.app_context._fetch_frontmost_context_slow",
        return_value=AppContext(name="Terminal"),
    ) as fetch:
        first = get_frontmost_context()
        second = get_frontmost_context()
        assert first == second
        fetch.assert_called_once()


def test_frontmost_context_cache_refreshes_after_ttl():
    invalidate_frontmost_context_cache()
    with patch(
        "expando.app_context._fetch_frontmost_context_nsworkspace",
        return_value=None,
    ), patch(
        "expando.app_context._fetch_frontmost_context_slow",
        side_effect=[
            AppContext(name="Terminal"),
            AppContext(name="Cursor"),
        ],
    ) as fetch:
        first = get_frontmost_context()
        time.sleep(1.1)
        second = get_frontmost_context()
        assert first.name == "Terminal"
        assert second.name == "Cursor"
        assert fetch.call_count == 2


def test_secure_input_cache_reuses_probe_within_ttl():
    invalidate_secure_input_cache()
    with patch(
        "expando.secure_input.platform.system",
        return_value="Darwin",
    ), patch(
        "expando.secure_input._probe_secure_input_active",
        return_value=True,
    ) as probe:
        assert is_secure_input_active() is True
        assert is_secure_input_active() is True
        probe.assert_called_once()
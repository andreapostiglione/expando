from __future__ import annotations

import os
from unittest.mock import patch

from expando.sparkle_native import check_for_updates_via_sparkle, sparkle_update_mode


def test_sparkle_update_mode_native() -> None:
    with patch("expando.sparkle_native.sparkle_available", return_value=True):
        assert sparkle_update_mode() == "native"


def test_sparkle_update_mode_python_fallback(monkeypatch) -> None:
    monkeypatch.delenv("EXPANDO_SPARKLE_FORCE_PYTHON", raising=False)
    with patch("expando.sparkle_native.sparkle_available", return_value=False):
        with patch("expando.sparkle_native.resolve_distribution_app_bundle", return_value=None):
            assert sparkle_update_mode() == "python_fallback"


def test_sparkle_update_mode_force_python(monkeypatch) -> None:
    monkeypatch.setenv("EXPANDO_SPARKLE_FORCE_PYTHON", "1")
    with patch("expando.sparkle_native.sparkle_available", return_value=True):
        assert sparkle_update_mode() == "python_fallback"


def test_interactive_sparkle_check_launches_without_waiting(tmp_path) -> None:
    bundle = tmp_path / "Expando.app"
    helper = bundle / "Contents" / "MacOS" / "expando-sparkle"
    helper.parent.mkdir(parents=True)
    helper.touch()

    with patch("expando.sparkle_native.resolve_distribution_app_bundle", return_value=bundle):
        with patch("expando.sparkle_native.sparkle_helper_path", return_value=helper):
            with patch("expando.sparkle_native.subprocess.Popen") as popen:
                with patch("expando.sparkle_native.subprocess.run") as run:
                    assert check_for_updates_via_sparkle(background=False) is True

    run.assert_not_called()
    popen.assert_called_once()
    assert popen.call_args.args[0] == [str(helper), "interactive"]

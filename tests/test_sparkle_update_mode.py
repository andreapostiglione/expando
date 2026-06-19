from __future__ import annotations

import os
from unittest.mock import patch

from expando.sparkle_native import sparkle_update_mode


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
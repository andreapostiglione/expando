from pathlib import Path
from unittest.mock import patch

from expando.onboarding import (
    is_onboarding_complete,
    mark_onboarding_complete,
    should_show_onboarding,
)


def test_onboarding_flag(tmp_path: Path):
    config_dir = tmp_path / "expando"
    assert is_onboarding_complete(config_dir) is False
    with patch("expando.onboarding.permissions_ready", return_value=False):
        assert should_show_onboarding(config_dir) is True
    mark_onboarding_complete(config_dir)
    assert is_onboarding_complete(config_dir) is True
    with patch("expando.onboarding.permissions_ready", return_value=True):
        assert should_show_onboarding(config_dir) is False


def test_onboarding_reappears_when_permissions_break(tmp_path: Path):
    config_dir = tmp_path / "expando"
    mark_onboarding_complete(config_dir)
    with patch("expando.onboarding.permissions_ready", return_value=False):
        assert should_show_onboarding(config_dir) is True


def test_should_show_onboarding_force(tmp_path: Path):
    config_dir = tmp_path / "expando"
    mark_onboarding_complete(config_dir)
    assert should_show_onboarding(config_dir, force=True) is True

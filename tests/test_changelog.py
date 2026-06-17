from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from expando.changelog import maybe_show_whats_new


def test_whats_new_skips_first_run(tmp_path: Path):
    config_dir = tmp_path / "expando"
    with patch("expando.changelog.notify") as notify:
        maybe_show_whats_new(config_dir, current_version="1.6.0")
        notify.assert_not_called()
    assert (config_dir / ".last_seen_version").read_text() == "1.6.0"


def test_whats_new_notifies_on_upgrade(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    (config_dir / ".last_seen_version").write_text("1.5.0", encoding="utf-8")

    with patch("expando.changelog.notify") as notify, patch(
        "expando.changelog._open_release_page"
    ):
        maybe_show_whats_new(config_dir, current_version="1.6.0")
        notify.assert_called_once()
        assert (config_dir / ".last_seen_version").read_text() == "1.6.0"
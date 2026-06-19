from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from expando.daemon import restart_daemon


def test_restart_daemon_stops_then_starts(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    calls: list[str] = []

    def fake_stop(_config_dir: Path) -> bool:
        calls.append("stop")
        return True

    def fake_start(_config_dir: Path) -> int:
        calls.append("start")
        return 4242

    with patch("expando.daemon.stop_daemon", side_effect=fake_stop):
        with patch("expando.daemon.start_daemon", side_effect=fake_start):
            pid = restart_daemon(config_dir)

    assert calls == ["stop", "start"]
    assert pid == 4242
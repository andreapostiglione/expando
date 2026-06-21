from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from expando.daemon import (
    register_foreground_cleanup,
    release_foreground_instance,
    restart_foreground_daemon,
)


def test_release_foreground_instance_invokes_registered_cleanup(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cleanup = MagicMock()
    register_foreground_cleanup(cleanup)

    release_foreground_instance(config_dir)

    cleanup.assert_called_once()
    register_foreground_cleanup(None)


def test_restart_foreground_daemon_releases_lock_before_spawn(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    events: list[str] = []
    cleanup = MagicMock(side_effect=lambda: events.append("release"))
    register_foreground_cleanup(cleanup)
    argv = ["/usr/bin/python3", "-m", "expando.daemon", "foreground", str(config_dir)]

    def _popen(*args, **kwargs):
        events.append("spawn")
        return MagicMock()

    with patch("expando.daemon._daemon_command", return_value=argv):
        with patch("expando.daemon.subprocess.Popen", side_effect=_popen) as popen_ctor:
            restart_foreground_daemon(config_dir)

    assert events == ["release", "spawn"]
    popen_ctor.assert_called_once()
    assert popen_ctor.call_args.args[0] == argv
    register_foreground_cleanup(None)
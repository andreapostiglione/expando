from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from expando.cli import main
from expando.daemon import is_running, stop_daemon


def test_cli_start_stop_status(tmp_path: Path, fake_daemon_command: None, monkeypatch):
    config_dir = tmp_path / "expando"
    runner = CliRunner()

    status = runner.invoke(main, ["--config-dir", str(config_dir), "status"])
    assert status.exit_code == 0
    assert "not running" in status.output

    start = runner.invoke(main, ["--config-dir", str(config_dir), "start"])
    assert start.exit_code == 0
    assert "started" in start.output
    assert is_running(config_dir)[0] is True

    status_running = runner.invoke(main, ["--config-dir", str(config_dir), "status"])
    assert status_running.exit_code == 0
    assert "running" in status_running.output

    stop = runner.invoke(main, ["--config-dir", str(config_dir), "stop"])
    assert stop.exit_code == 0
    assert "stopped" in stop.output
    assert is_running(config_dir)[0] is False


def test_cli_restart(tmp_path: Path, fake_daemon_command: None):
    config_dir = tmp_path / "expando"
    runner = CliRunner()

    runner.invoke(main, ["--config-dir", str(config_dir), "start"])
    first_pid = is_running(config_dir)[1]

    restart = runner.invoke(main, ["--config-dir", str(config_dir), "restart"])
    assert restart.exit_code == 0
    assert "restarted" in restart.output

    second_pid = is_running(config_dir)[1]
    assert second_pid is not None
    stop_daemon(config_dir)
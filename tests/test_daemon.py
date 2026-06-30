from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from expando.daemon import (
    _daemon_command,
    foreground,
    is_running,
    restart_foreground_daemon,
    start_daemon,
    stop_daemon,
)
from expando.lock import SingleInstanceLock
from expando.paths import lock_file, pid_file


def test_is_running_false_when_pid_missing(tmp_path: Path):
    running, pid = is_running(tmp_path)
    assert running is False
    assert pid is None


def test_is_running_cleans_stale_pid(tmp_path: Path):
    pid_path = pid_file(tmp_path)
    pid_path.write_text("999999999", encoding="utf-8")
    running, pid = is_running(tmp_path)
    assert running is False
    assert pid is None
    assert not pid_path.exists()


def test_start_and_stop_daemon(tmp_path: Path, fake_daemon_command: None):
    config_dir = tmp_path / "expando"
    pid = start_daemon(config_dir)
    assert pid > 0
    running, live_pid = is_running(config_dir)
    assert running is True
    assert live_pid == pid

    assert stop_daemon(config_dir) is True
    assert is_running(config_dir)[0] is False


def test_start_daemon_returns_existing_pid(tmp_path: Path, fake_daemon_command: None):
    config_dir = tmp_path / "expando"
    first = start_daemon(config_dir)
    second = start_daemon(config_dir)
    assert second == first
    stop_daemon(config_dir)


def test_daemon_command_uses_installed_app_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_executable = tmp_path / "Expando.app" / "Contents" / "MacOS" / "expando"
    resources = tmp_path / "Expando.app" / "Contents" / "Resources"
    app_executable.parent.mkdir(parents=True)
    resources.mkdir(parents=True)
    app_executable.write_text("#!/bin/sh\n", encoding="utf-8")
    app_executable.chmod(0o755)
    config_dir = tmp_path / "config"

    monkeypatch.setenv("EXPANDO_RESOURCES", str(resources))
    monkeypatch.setattr(sys, "executable", str(app_executable))

    assert _daemon_command(config_dir) == [
        str(app_executable.resolve()),
        "--config-dir",
        str(config_dir),
        "run",
    ]


def test_foreground_writes_pid_and_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: OFF\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':x'\n    replace: 'X'\n",
        encoding="utf-8",
    )

    seen_pid: list[int] = []

    def fake_run_service(_config_dir: Path) -> None:
        seen_pid.append(os.getpid())
        assert pid_file(_config_dir).read_text(encoding="utf-8") == str(os.getpid())

    monkeypatch.setattr("expando.listener.run_service", fake_run_service)
    foreground(config_dir)

    assert seen_pid
    assert not pid_file(config_dir).exists()
    assert not lock_file(config_dir).exists()


def test_foreground_signal_handler_exits_after_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: OFF\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':x'\n    replace: 'X'\n",
        encoding="utf-8",
    )
    handlers = {}

    def capture_signal(signum, handler):
        handlers[signum] = handler

    def fake_run_service(_config_dir: Path) -> None:
        handlers[signal.SIGTERM](signal.SIGTERM, None)

    import signal

    monkeypatch.setattr("expando.daemon.signal.signal", capture_signal)
    monkeypatch.setattr("expando.listener.run_service", fake_run_service)

    with pytest.raises(SystemExit) as exc:
        foreground(config_dir)

    assert exc.value.code == 0
    assert not pid_file(config_dir).exists()
    assert not lock_file(config_dir).exists()


def test_foreground_exits_when_already_running(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "expando"
    config_dir.mkdir(parents=True)

    monkeypatch.setattr("expando.daemon.is_running", lambda _d: (True, os.getpid()))

    def cannot_acquire(self, *, blocking: bool = True) -> bool:
        return False

    monkeypatch.setattr(SingleInstanceLock, "acquire", cannot_acquire)
    monkeypatch.setattr("expando.listener.run_service", lambda _d: None)

    with pytest.raises(SystemExit) as exc:
        foreground(config_dir)
    assert exc.value.code == 0


def test_start_daemon_raises_when_pid_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    hang_script = tmp_path / "hang.py"
    hang_script.write_text(
        "import time\nfor _ in range(200):\n    time.sleep(0.01)\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "expando.daemon._daemon_command",
        lambda _d: [sys.executable, str(hang_script)],
    )
    monkeypatch.setattr("expando.daemon._START_WAIT_ATTEMPTS", 2)
    monkeypatch.setattr("expando.daemon._START_WAIT_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr("expando.daemon.time.sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="pid file not written"):
        start_daemon(config_dir)


def test_restart_foreground_daemon_waits_for_old_pid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    popen_calls: list[tuple] = []

    def fake_popen(args, **kwargs):
        popen_calls.append((args, kwargs))
        return object()

    monkeypatch.setattr("expando.daemon._daemon_command", lambda _d: ["python", "-m", "expando"])
    monkeypatch.setattr("expando.daemon.release_foreground_instance", lambda _d: None)
    monkeypatch.setattr("expando.daemon.subprocess.Popen", fake_popen)

    restart_foreground_daemon(config_dir, wait_for_pid=12345)

    assert len(popen_calls) == 1
    args, kwargs = popen_calls[0]
    assert args[0] == "/bin/bash"
    assert "kill -0 12345" in args[2]
    assert "python -m expando" in args[2]
    assert kwargs["start_new_session"] is True

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from expando.doctor_repair import _is_stale_lock, diagnose_daemon_state, repair_daemon_state
from expando.lock import SingleInstanceLock
from expando.paths import lock_file, pid_file


def _setup_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )
    return config_dir


def test_diagnose_detects_stale_pid_file(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    pid_file(config_dir).write_text("999999999", encoding="utf-8")

    with patch("expando.doctor_repair.is_running", return_value=(False, None)):
        with patch("expando.doctor_repair._find_expando_processes", return_value=[]):
            diagnosis = diagnose_daemon_state(config_dir)

    assert diagnosis["stale_pid_file"] is True
    assert diagnosis["needs_repair"] is True


def test_repair_removes_stale_pid_file(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    pid_file(config_dir).write_text("999999999", encoding="utf-8")

    with patch("expando.doctor_repair.is_running", return_value=(False, None)):
        with patch("expando.doctor_repair._find_expando_processes", return_value=[]):
            result = repair_daemon_state(config_dir)

    assert "removed_stale_pid_file" in result["actions"]
    assert not pid_file(config_dir).exists()
    assert result["ok"] is True


def test_repair_kills_orphan_processes(tmp_path: Path, monkeypatch):
    config_dir = _setup_config_dir(tmp_path)
    killed: list[tuple[int, int]] = []

    def fake_kill(pid: int, sig: int) -> None:
        killed.append((pid, sig))

    monkeypatch.setattr("expando.doctor_repair.os.kill", fake_kill)
    with patch("expando.doctor_repair._find_expando_processes", return_value=[4242, 5252]):
        with patch("expando.doctor_repair.is_running", return_value=(False, None)):
            result = repair_daemon_state(config_dir)

    killed_pids = {pid for pid, _sig in killed}
    assert killed_pids == {4242, 5252}
    assert any(action.startswith("killed_orphan_processes:") for action in result["actions"])


def test_repair_releases_stale_lock(tmp_path: Path, monkeypatch):
    config_dir = _setup_config_dir(tmp_path)
    lock_path = lock_file(config_dir)
    lock_path.write_text(str(os.getpid()), encoding="utf-8")

    monkeypatch.setattr("expando.doctor_repair._is_stale_lock", lambda _path: True)
    with patch("expando.doctor_repair._find_expando_processes", return_value=[]):
        with patch("expando.doctor_repair.is_running", return_value=(False, None)):
            result = repair_daemon_state(config_dir)

    assert not lock_path.exists()
    assert any(action.startswith("released_stale_lock:") for action in result["actions"])


def test_held_lock_with_empty_pid_is_not_stale(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    lock_path = lock_file(config_dir)
    lock = SingleInstanceLock(lock_path)
    assert lock.acquire()
    lock_path.write_text("", encoding="utf-8")
    try:
        assert _is_stale_lock(lock_path) is False
    finally:
        lock.release()


def test_repair_clears_safe_mode(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    from expando.crash_loop import activate_safe_mode, safe_mode_file

    activate_safe_mode(config_dir, reason="test")
    assert safe_mode_file(config_dir).exists()

    with patch("expando.doctor_repair.is_running", return_value=(False, None)):
        with patch("expando.doctor_repair._find_expando_processes", return_value=[]):
            result = repair_daemon_state(config_dir)

    assert "cleared_safe_mode" in result["actions"]
    assert not safe_mode_file(config_dir).exists()

from pathlib import Path

from expando.crash_loop import (
    activate_safe_mode,
    apply_startup_crash_policy,
    crash_count_in_window,
    record_daemon_crash,
    safe_mode_status,
    should_enter_safe_mode,
)


def test_crash_loop_enters_safe_mode(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    for _ in range(5):
        record_daemon_crash(config_dir)
    assert should_enter_safe_mode(config_dir, max_crashes=5)
    result = apply_startup_crash_policy(config_dir)
    assert result["safe_mode"] is True
    assert safe_mode_status(config_dir) is not None


def test_crash_count_in_window(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    record_daemon_crash(config_dir)
    assert crash_count_in_window(config_dir) == 1
    activate_safe_mode(config_dir, reason="test")
    assert safe_mode_status(config_dir)["reason"] == "test"
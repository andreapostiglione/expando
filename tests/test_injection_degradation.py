from __future__ import annotations

from pathlib import Path

from expando.injection_degradation import (
    degradation_status,
    record_injection_failure,
    record_injection_success,
)


def test_record_injection_failure_increments_counter(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()

    record_injection_failure(config_dir)
    record_injection_failure(config_dir)

    status = degradation_status(config_dir)
    assert status["consecutive_failures"] == 2
    assert status["should_warn"] is False


def test_degradation_warn_threshold(tmp_path: Path, monkeypatch):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    monkeypatch.setenv("EXPANDO_INJECTION_WARN_THRESHOLD", "2")

    record_injection_failure(config_dir)
    record_injection_failure(config_dir)

    status = degradation_status(config_dir)
    assert status["should_warn"] is True
    assert status["should_disable"] is False


def test_degradation_disable_requires_env_flag(tmp_path: Path, monkeypatch):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    monkeypatch.setenv("EXPANDO_INJECTION_DISABLE_THRESHOLD", "2")

    record_injection_failure(config_dir)
    record_injection_failure(config_dir)
    assert degradation_status(config_dir)["should_disable"] is False

    monkeypatch.setenv("EXPANDO_AUTO_DISABLE_INJECTION", "1")
    assert degradation_status(config_dir)["should_disable"] is True


def test_record_injection_success_resets_counter(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()

    record_injection_failure(config_dir)
    record_injection_failure(config_dir)
    record_injection_success(config_dir)

    status = degradation_status(config_dir)
    assert status["consecutive_failures"] == 0
    assert status["should_warn"] is False
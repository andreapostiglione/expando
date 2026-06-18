from pathlib import Path

import pytest

from expando.benchmark import SparkleBenchmarkResult
from expando.sparkle_benchmark_history import (
    HISTORY_VERSION,
    build_sparkle_benchmark_entry,
    format_sparkle_benchmark_history_report,
    load_sparkle_benchmark_history,
    record_sparkle_benchmark,
    sparkle_benchmark_history_to_dict,
)


def _sample_result(helper_ms: float | None = 1200.5) -> SparkleBenchmarkResult:
    return SparkleBenchmarkResult(
        sparkle_available=True,
        app_bundle="/Applications/Expando.app",
        helper_path="/Applications/Expando.app/Contents/Frameworks/Sparkle.framework/...",
        framework_present=True,
        appcast_fetch_ms=42.0,
        helper_check_ms=helper_ms,
        appcast_entries=3,
        latest_version="3.8.0",
        current_version="3.8.0",
        update_available=False,
    )


def test_build_sparkle_benchmark_entry_marks_slow():
    entry = build_sparkle_benchmark_entry(
        _sample_result(helper_ms=16000.0),
        version="3.8.0",
        warn_ms=15000,
        tag="v3.8.0",
    )
    assert entry["version"] == "3.8.0"
    assert entry["slow"] is True
    assert entry["benchmark"]["helper_slow"] is True


def test_record_and_load_sparkle_benchmark_history(tmp_path: Path):
    history_path = tmp_path / "sparkle-benchmark-history.json"
    record_sparkle_benchmark(
        _sample_result(),
        history_path,
        version="3.8.0",
        warn_ms=15000,
        tag="v3.8.0",
    )
    entries = load_sparkle_benchmark_history(history_path)
    assert len(entries) == 1
    assert entries[0]["version"] == "3.8.0"
    assert entries[0]["benchmark"]["helper_check_ms"] == 1200.5


def test_sparkle_benchmark_history_caps_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    history_path = tmp_path / "sparkle-benchmark-history.json"
    monkeypatch.setattr("expando.sparkle_benchmark_history.MAX_HISTORY_ENTRIES", 2)
    for index in range(3):
        record_sparkle_benchmark(
            _sample_result(helper_ms=float(index)),
            history_path,
            version=f"3.{index}.0",
            warn_ms=15000,
        )
    entries = load_sparkle_benchmark_history(history_path)
    assert len(entries) == 2
    assert entries[0]["version"] == "3.1.0"
    assert entries[1]["version"] == "3.2.0"


def test_sparkle_benchmark_history_report_and_to_dict(tmp_path: Path):
    history_path = tmp_path / "sparkle-benchmark-history.json"
    record_sparkle_benchmark(
        _sample_result(),
        history_path,
        version="3.8.0",
        warn_ms=15000,
    )
    report = format_sparkle_benchmark_history_report(history_path, limit=5)
    assert "3.8.0" in report
    payload = sparkle_benchmark_history_to_dict(history_path, limit=1)
    assert payload["version"] == HISTORY_VERSION
    assert payload["stats"]["total"] == 1
    assert len(payload["entries"]) == 1
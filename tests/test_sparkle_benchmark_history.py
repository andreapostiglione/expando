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
    sparkle_benchmark_sparkline,
    sparkle_benchmark_trend_svg,
    write_sparkle_benchmark_trend_svg,
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


def test_build_sparkle_benchmark_entry_marks_slow_and_fail():
    entry = build_sparkle_benchmark_entry(
        _sample_result(helper_ms=31000.0),
        version="3.8.0",
        warn_ms=15000,
        fail_ms=30000,
        tag="v3.8.0",
    )
    assert entry["version"] == "3.8.0"
    assert entry["slow"] is True
    assert entry["failed"] is True
    assert entry["benchmark"]["helper_slow"] is True
    assert entry["benchmark"]["helper_fail"] is True


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


def test_sparkle_benchmark_sparkline_and_report_trend(tmp_path: Path):
    history_path = tmp_path / "sparkle-benchmark-history.json"
    for helper_ms in (1000.0, 2000.0, 4000.0):
        record_sparkle_benchmark(
            _sample_result(helper_ms=helper_ms),
            history_path,
            version="3.8.0",
            warn_ms=15000,
        )
    entries = load_sparkle_benchmark_history(history_path)
    sparkline = sparkle_benchmark_sparkline(entries)
    assert len(sparkline) == 3
    report = format_sparkle_benchmark_history_report(history_path, limit=5)
    assert sparkline in report
    assert "min=" in report


def test_sparkle_benchmark_trend_svg_includes_points_and_labels():
    entries = [
        {
            "version": "3.9.0",
            "warn_ms": 15000,
            "fail_ms": 30000,
            "benchmark": {"helper_check_ms": 1200.0},
        },
        {
            "version": "3.10.0",
            "warn_ms": 15000,
            "fail_ms": 30000,
            "benchmark": {"helper_check_ms": 2400.0},
        },
    ]
    svg = sparkle_benchmark_trend_svg(entries)
    assert "<svg" in svg
    assert "polyline" in svg
    assert "3.9.0" in svg
    assert "3.10.0" in svg


def test_write_sparkle_benchmark_trend_svg(tmp_path: Path):
    history_path = tmp_path / "sparkle-benchmark-history.json"
    record_sparkle_benchmark(
        _sample_result(helper_ms=1500.0),
        history_path,
        version="3.11.0",
        warn_ms=15000,
    )
    svg_path = tmp_path / "trend.svg"
    written = write_sparkle_benchmark_trend_svg(svg_path, history_path=history_path)
    assert written == svg_path
    content = svg_path.read_text(encoding="utf-8")
    assert "3.11.0" in content
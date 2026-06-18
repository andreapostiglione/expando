import json
from pathlib import Path

import pytest

from expando.notarization_audit import NotarizationAuditReport
from expando.notarization_history import (
    format_notarization_history_report,
    history_file,
    load_notarization_history,
    notarization_history_stats,
    notarization_history_to_dict,
    notarization_history_trend_svg,
    record_notarization_audit,
    write_notarization_history_trend_svg,
)


def test_record_notarization_audit_appends_entry(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    report = NotarizationAuditReport(ok=True)
    report.add("codesign.verify", "pass", "ok")
    report.add("gatekeeper.assess", "warn", "skipped")

    entry = record_notarization_audit(
        config_dir,
        report,
        app_bundle=Path("/Applications/Expando.app"),
        dmg=Path("/tmp/Expando.dmg"),
    )

    assert entry["ok"] is True
    assert entry["summary"] == {"pass": 1, "warn": 1, "fail": 0}
    assert entry["targets"]["app"] == "/Applications/Expando.app"

    data = json.loads(history_file(config_dir).read_text(encoding="utf-8"))
    assert len(data["entries"]) == 1
    assert data["entries"][0]["report"]["ok"] is True


def test_notarization_history_stats_and_report(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()

    for ok in (True, False, True):
        report = NotarizationAuditReport(ok=ok)
        report.add("codesign.verify", "pass" if ok else "fail", "check")
        record_notarization_audit(config_dir, report)

    entries = load_notarization_history(config_dir)
    stats = notarization_history_stats(entries)
    assert stats["total"] == 3
    assert stats["ok"] == 2
    assert stats["failed"] == 1
    assert stats["recent_ok_rate"] == 0.67

    report_text = format_notarization_history_report(config_dir, limit=2)
    assert "Runs: 3" in report_text or "Esecuzioni: 3" in report_text
    assert "codesign.verify" not in report_text


def test_notarization_history_to_dict_limits_entries(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    for index in range(3):
        report = NotarizationAuditReport(ok=index % 2 == 0)
        report.add("codesign.verify", "pass", f"run-{index}")
        record_notarization_audit(config_dir, report)

    payload = notarization_history_to_dict(config_dir, limit=2)
    assert payload["stats"]["total"] == 3
    assert len(payload["entries"]) == 2
    assert payload["entries"][0]["report"]["findings"][0]["message"] == "run-1"


def test_notarization_history_caps_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    monkeypatch.setattr("expando.notarization_history.MAX_HISTORY_ENTRIES", 2)

    for index in range(3):
        report = NotarizationAuditReport(ok=True)
        report.add("codesign.verify", "pass", f"run-{index}")
        record_notarization_audit(config_dir, report)

    entries = load_notarization_history(config_dir)
    assert len(entries) == 2
    assert entries[0]["report"]["findings"][0]["message"] == "run-1"


def test_notarization_history_trend_svg_marks_pass_and_fail():
    entries = [
        {"ok": True, "recorded_at": "2026-06-18T10:00:00+00:00"},
        {"ok": False, "recorded_at": "2026-06-18T11:00:00+00:00"},
    ]
    svg = notarization_history_trend_svg(entries)
    assert "<svg" in svg
    assert "#3ecf8e" in svg
    assert "#ff6b6b" in svg
    assert "1/2 ok" in svg


def test_write_notarization_history_trend_svg(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    report = NotarizationAuditReport(ok=True)
    report.add("codesign.verify", "pass", "ok")
    record_notarization_audit(config_dir, report)

    svg_path = tmp_path / "trend.svg"
    written = write_notarization_history_trend_svg(config_dir, svg_path)
    assert written == svg_path
    assert "<svg" in svg_path.read_text(encoding="utf-8")
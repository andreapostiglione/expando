from pathlib import Path

import pytest

from expando.notarization_audit import (
    _entitlements_match,
    _normalize_entitlements,
    format_notarization_audit_report,
    load_expected_entitlements,
    run_notarization_audit,
)


def test_entitlements_match_detects_missing_key():
    expected = {"com.apple.security.automation.apple-events": True}
    actual = {}
    ok, message = _entitlements_match(actual, expected)
    assert not ok
    assert "missing keys" in message


def test_entitlements_match_passes_identical_dicts():
    data = {"com.apple.security.automation.apple-events": True}
    ok, message = _entitlements_match(data, data)
    assert ok
    assert "match" in message


def test_normalize_entitlements_sorts_lists():
    normalized = _normalize_entitlements({"tags": ["b", "a"]})
    assert normalized["tags"] == ["a", "b"]


def test_load_expected_entitlements_reads_repo_baseline():
    data = load_expected_entitlements()
    assert "com.apple.security.automation.apple-events" in data


def test_notarization_audit_warns_without_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.notarization_audit.resolve_audit_targets",
        lambda **_: (None, None),
    )
    report = run_notarization_audit()
    assert report.ok
    assert any(item.check_id == "targets" and item.status == "warn" for item in report.findings)


def test_notarization_audit_strict_fails_without_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "expando.notarization_audit.resolve_audit_targets",
        lambda **_: (None, None),
    )
    report = run_notarization_audit(strict=True)
    assert not report.ok


def test_format_notarization_audit_report(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.notarization_audit.resolve_audit_targets",
        lambda **_: (None, None),
    )
    report = run_notarization_audit()
    text = format_notarization_audit_report(report)
    assert "codesign" in text.lower() or "targets" in text.lower() or "[" in text
from pathlib import Path

import pytest

from expando.notarization_audit import (
    audit_dmg,
    _entitlements_match,
    _normalize_entitlements,
    format_notarization_audit_report,
    expected_team_id,
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


def test_expected_team_id_can_be_overridden(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("EXPANDO_EXPECTED_TEAM_ID", "TEAM123456")

    assert expected_team_id() == "TEAM123456"


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


def test_audit_dmg_fails_unsigned_gatekeeper_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    dmg = tmp_path / "Expando.dmg"
    dmg.write_bytes(b"not a real dmg")

    def fake_run(args: list[str], *, timeout: int = 60):
        class Result:
            stdout = ""
            stderr = ""

            def __init__(self, returncode: int, stderr: str = "") -> None:
                self.returncode = returncode
                self.stderr = stderr

        if args[:3] == ["codesign", "--verify", "--verbose=2"]:
            return Result(0)
        if args[:3] == ["spctl", "-a", "-t"]:
            return Result(3, f"{dmg}: rejected\nsource=no usable signature")
        if args[:3] == ["xcrun", "stapler", "validate"]:
            return Result(0, "The validate action worked!")
        return Result(1, "unexpected command")

    monkeypatch.setattr("expando.notarization_audit._run_command", fake_run)

    findings = audit_dmg(dmg)

    by_id = {finding.check_id: finding for finding in findings}
    assert by_id["dmg.codesign.verify"].status == "pass"
    assert by_id["dmg.gatekeeper.open"].status == "fail"
    assert "no usable signature" in by_id["dmg.gatekeeper.open"].message
    assert by_id["notary.staple"].status == "pass"

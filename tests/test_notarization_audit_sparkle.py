from pathlib import Path
from unittest.mock import MagicMock

import pytest

from expando.notarization_audit import audit_sparkle_helper_signing


@pytest.fixture
def sparkle_helper(tmp_path: Path) -> Path:
    path = tmp_path / "expando-sparkle"
    path.write_bytes(b"\xcf\xfa\xed\xfe")
    return path


def test_audit_sparkle_helper_signing_passes_when_signed(
    sparkle_helper: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    expected = {"com.apple.security.automation.apple-events": True}

    def fake_run(args, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        return result

    monkeypatch.setattr("expando.notarization_audit._run_command", fake_run)
    monkeypatch.setattr(
        "expando.notarization_audit._codesign_details",
        lambda target: "flags=runtime TeamIdentifier=68Q8CQBQQV",
    )
    monkeypatch.setattr(
        "expando.notarization_audit._read_codesign_entitlements",
        lambda target: expected,
    )

    findings = audit_sparkle_helper_signing(sparkle_helper, expected=expected)
    by_id = {item.check_id: item.status for item in findings}
    assert by_id["sparkle.helper.verify"] == "pass"
    assert by_id["sparkle.helper.hardened_runtime"] == "pass"
    assert by_id["sparkle.helper.team_id"] == "pass"
    assert by_id["sparkle.helper.entitlements"] == "pass"


def test_audit_sparkle_helper_signing_fails_without_hardened_runtime(
    sparkle_helper: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "expando.notarization_audit._run_command",
        lambda args, **kwargs: MagicMock(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        "expando.notarization_audit._codesign_details",
        lambda target: "TeamIdentifier=68Q8CQBQQV",
    )
    monkeypatch.setattr(
        "expando.notarization_audit._read_codesign_entitlements",
        lambda target: {},
    )

    findings = audit_sparkle_helper_signing(sparkle_helper, expected={})
    by_id = {item.check_id: item.status for item in findings}
    assert by_id["sparkle.helper.hardened_runtime"] == "fail"
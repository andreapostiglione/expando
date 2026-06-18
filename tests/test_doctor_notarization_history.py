from pathlib import Path
from unittest.mock import patch

from expando.doctor_checks import format_doctor_report, run_doctor
from expando.notarization_audit import NotarizationAuditReport
from expando.notarization_history import record_notarization_audit
from expando.permissions import PermissionStatus
from expando.runtime_info import RuntimeInfo


def _runtime() -> RuntimeInfo:
    return RuntimeInfo(
        mode="venv",
        executable="/tmp/.venv/bin/python3.14",
        grant_label="python3.14",
        grant_hint="/tmp/.venv/bin/python3.14",
    )


def test_doctor_includes_notarization_history_summary(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )

    report = NotarizationAuditReport(ok=True)
    report.add("codesign.verify", "pass", "ok")
    record_notarization_audit(config_dir, report)

    status = PermissionStatus(
        accessibility=True,
        input_monitoring=None,
        notes=[],
        runtime=_runtime(),
        injection_ready=True,
    )
    with patch("expando.doctor_checks.check_permissions", return_value=status):
        text = format_doctor_report(run_doctor(config_dir))

    assert "Audit notarizzazione" in text or "Notarization audit" in text
    assert "Esecuzioni: 1" in text or "Runs: 1" in text


def test_doctor_hints_notarize_history_after_failed_audit(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )

    report = NotarizationAuditReport(ok=False)
    report.add("notary.staple", "fail", "missing staple")
    record_notarization_audit(config_dir, report)

    status = PermissionStatus(
        accessibility=True,
        input_monitoring=None,
        notes=[],
        runtime=_runtime(),
        injection_ready=True,
    )
    with patch("expando.doctor_checks.check_permissions", return_value=status):
        text = format_doctor_report(run_doctor(config_dir))

    assert "notarize-history" in text
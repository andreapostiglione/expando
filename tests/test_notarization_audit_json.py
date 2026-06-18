import json
from pathlib import Path

import pytest

from expando.notarization_audit import (
    NotarizationAuditReport,
    notarization_audit_report_to_dict,
    write_notarization_audit_json,
)


def test_notarization_audit_report_to_dict():
    report = NotarizationAuditReport(ok=True)
    report.add("codesign.verify", "pass", "ok")
    payload = notarization_audit_report_to_dict(report)
    assert payload["ok"] is True
    assert payload["findings"][0]["check_id"] == "codesign.verify"


def test_write_notarization_audit_json(tmp_path: Path):
    report = NotarizationAuditReport(ok=False)
    report.add("notary.staple", "fail", "missing staple")
    destination = tmp_path / "audit.json"
    write_notarization_audit_json(report, destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["ok"] is False
    assert len(payload["findings"]) == 1
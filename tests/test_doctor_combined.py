import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from expando.cli import main
from expando.doctor_checks import (
    DoctorReport,
    doctor_combined_document,
    doctor_document,
    doctor_report_to_dict,
)


def test_doctor_report_to_dict():
    report = DoctorReport(
        ok=True,
        config_dir=Path("/tmp/expando"),
        running=True,
        pid=42,
        process_count=1,
        match_count=10,
    )
    payload = doctor_report_to_dict(report)
    assert payload["ok"] is True
    assert payload["pid"] == 42
    assert payload["match_count"] == 10


def test_doctor_combined_document_merges_marketplace(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    with patch(
        "expando.doctor_checks.run_doctor",
        return_value=DoctorReport(
            ok=True,
            config_dir=tmp_path,
            running=False,
            pid=None,
            process_count=0,
            match_count=5,
        ),
    ):
        payload = doctor_combined_document(tmp_path)
    assert payload["version"] == 1
    assert payload["doctor"]["match_count"] == 5
    assert "marketplace" in payload
    json.dumps(payload)


def test_doctor_document_exports_structured_report(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    with patch(
        "expando.doctor_checks.run_doctor",
        return_value=DoctorReport(
            ok=True,
            config_dir=tmp_path,
            running=False,
            pid=None,
            process_count=0,
            match_count=7,
        ),
    ):
        payload = doctor_document(tmp_path)
    assert payload["version"] == 1
    assert payload["doctor"]["match_count"] == 7
    assert "marketplace" not in payload


def test_doctor_cli_doctor_json_includes_text_and_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config-dir", str(tmp_path), "doctor", "--doctor-json"],
    )
    assert result.exit_code == 0, result.output
    assert "Doctor JSON" in result.output
    assert '"doctor"' in result.output
    assert '"marketplace"' not in result.output


def test_doctor_cli_marketplace_json_includes_text_and_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config-dir", str(tmp_path), "doctor", "--marketplace-json"],
    )
    assert result.exit_code == 0, result.output
    assert "Marketplace JSON" in result.output
    assert '"doctor"' in result.output
    assert '"marketplace"' in result.output
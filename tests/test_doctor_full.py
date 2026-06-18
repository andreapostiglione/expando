import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from expando.cli import main
from expando.doctor_checks import DoctorReport, doctor_full_document


def test_doctor_full_document_includes_histories(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    with patch(
        "expando.doctor_checks.run_doctor",
        return_value=DoctorReport(
            ok=True,
            config_dir=tmp_path,
            running=False,
            pid=None,
            process_count=0,
            match_count=3,
        ),
    ):
        payload = doctor_full_document(tmp_path, history_limit=2)
    assert payload["doctor"]["match_count"] == 3
    assert "marketplace" in payload
    assert "notarization_history" in payload
    assert "sparkle_benchmark_history" in payload
    assert "community_validation" in payload
    json.dumps(payload)


def test_doctor_cli_full_json(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config-dir", str(tmp_path), "doctor", "--full-json"],
    )
    assert result.exit_code == 0, result.output
    assert "Full health JSON" in result.output
    assert '"notarization_history"' in result.output
    assert '"sparkle_benchmark_history"' in result.output
    assert '"community_validation"' in result.output
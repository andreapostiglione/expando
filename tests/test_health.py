from __future__ import annotations

import json
from pathlib import Path

from expando.health import (
    build_health_document,
    format_health_report,
    load_runtime_health,
    record_config_reload,
    record_daemon_started,
    record_expansion,
    runtime_health_file,
)


def test_runtime_health_records_metrics(tmp_path: Path):
    record_daemon_started(tmp_path)
    record_expansion(tmp_path, ":hello")
    record_config_reload(tmp_path)

    data = load_runtime_health(tmp_path)
    assert data["daemon_started_at"]
    assert data["last_expansion_trigger"] == ":hello"
    assert data["config_reload_count"] == 1
    assert runtime_health_file(tmp_path).exists()


def test_build_health_document(tmp_path: Path):
    record_daemon_started(tmp_path)
    document = build_health_document(tmp_path)
    assert document["config_dir"] == str(tmp_path)
    assert "daemon" in document
    assert "listener" in document
    report = format_health_report(document)
    assert "Expando runtime health" in report


def test_health_cli_json(tmp_path: Path, monkeypatch):
    from click.testing import CliRunner

    from expando.cli import main

    record_daemon_started(tmp_path)
    runner = CliRunner()
    result = runner.invoke(main, ["--config-dir", str(tmp_path), "health", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["config_dir"] == str(tmp_path)
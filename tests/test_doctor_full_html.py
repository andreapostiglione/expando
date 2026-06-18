from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from expando.cli import main
from expando.doctor_checks import (
    DoctorReport,
    build_doctor_full_html,
    write_doctor_full_html,
)


def test_build_doctor_full_html_includes_sections():
    document = {
        "generated_at": "2026-06-18T10:00:00+00:00",
        "doctor": {
            "ok": True,
            "config_dir": "/tmp/expando",
            "running": True,
            "pid": 42,
            "match_count": 12,
            "warnings": [],
            "config_errors": [],
            "permissions": {
                "accessibility": True,
                "input_monitoring": True,
                "injection_ready": True,
            },
            "runtime": {"mode": "app"},
        },
        "marketplace": {
            "remote_url": "https://example.com/marketplace.json",
            "community_count": 1,
            "approved_count": 4,
            "community_packages": [{"id": "typing-it", "name": "Typing IT"}],
            "pending_diffs": [],
        },
        "notarization_history": {
            "stats": {"total": 1, "ok": 1, "failed": 0},
            "entries": [
                {
                    "recorded_at": "2026-06-18T09:00:00+00:00",
                    "ok": True,
                    "summary": {"pass": 5, "warn": 0, "fail": 0},
                }
            ],
        },
        "sparkle_benchmark_history": {
            "stats": {"total": 1, "trend_sparkline": "▁"},
            "entries": [
                {
                    "recorded_at": "2026-06-18T08:00:00+00:00",
                    "version": "3.12.0",
                    "slow": False,
                    "failed": False,
                    "benchmark": {"helper_check_ms": 1200.0},
                }
            ],
        },
        "community_validation": {
            "ok": True,
            "packages": [{"package_id": "typing-it", "ok": True}],
            "trigger_suggestions": [],
        },
    }
    html_text = build_doctor_full_html(document)
    assert "Expando Health Dashboard" in html_text
    assert "Notarization history" in html_text
    assert "Sparkle benchmark history" in html_text
    assert "typing-it" in html_text
    assert "3.12.0" in html_text
    assert "<svg" in html_text
    assert "polyline" in html_text


def test_write_doctor_full_html(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    with patch(
        "expando.doctor_checks.run_doctor",
        return_value=DoctorReport(
            ok=True,
            config_dir=tmp_path,
            running=False,
            pid=None,
            process_count=0,
            match_count=4,
        ),
    ):
        destination = tmp_path / "health.html"
        written = write_doctor_full_html(tmp_path, destination)
    assert written == destination
    assert "Expando Health Dashboard" in destination.read_text(encoding="utf-8")


def test_doctor_cli_full_html(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    monkeypatch.setattr("expando.i18n._LOCALE", "en")
    runner = CliRunner()
    html_path = tmp_path / "doctor-health.html"
    result = runner.invoke(
        main,
        [
            "--config-dir",
            str(tmp_path),
            "doctor",
            "--full-html",
            "--full-html-output",
            str(html_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Health HTML dashboard written" in result.output
    assert html_path.exists()
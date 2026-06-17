from pathlib import Path
from unittest.mock import patch

from expando.doctor_checks import format_doctor_report, run_doctor
from expando.permissions import PermissionStatus
from expando.runtime_info import RuntimeInfo


def _runtime() -> RuntimeInfo:
    return RuntimeInfo(
        mode="venv",
        executable="/tmp/.venv/bin/python3.14",
        grant_label="python3.14",
        grant_hint="/tmp/.venv/bin/python3.14",
    )


def test_doctor_report_includes_runtime(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )
    status = PermissionStatus(
        accessibility=True,
        input_monitoring=None,
        notes=[],
        runtime=_runtime(),
        injection_ready=True,
    )
    with patch("expando.doctor_checks.check_permissions", return_value=status):
        report = run_doctor(config_dir)
    text = format_doctor_report(report)
    assert "python3.14" in text
    assert report.ok is True


def test_doctor_fails_without_accessibility(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )
    status = PermissionStatus(
        accessibility=False,
        input_monitoring=False,
        notes=["test"],
        runtime=_runtime(),
        injection_ready=False,
    )
    with patch("expando.doctor_checks.check_permissions", return_value=status):
        report = run_doctor(config_dir)
    assert report.ok is False
    assert "Accessibilità" in format_doctor_report(report)
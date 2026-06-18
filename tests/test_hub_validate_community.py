from pathlib import Path

from click.testing import CliRunner

from expando.cli import main
from expando.hub_marketplace import (
    format_community_validation_report,
    validate_community_hub_packages,
)


def test_validate_community_hub_packages_passes_repo_packages():
    reports = validate_community_hub_packages()
    ids = {report.package_id for _, report in reports}
    assert "typing-it" in ids
    assert "meeting-it" in ids
    assert "writing-it" in ids
    assert all(report.ok for _, report in reports)


def test_validate_community_hub_packages_detects_invalid_package(tmp_path: Path):
    bad = tmp_path / "packages" / "community" / "broken-pack"
    bad.mkdir(parents=True)
    (bad / "hub.json").write_text('{"id": "other-id", "name": "x", "description": "y"}\n', encoding="utf-8")

    reports = validate_community_hub_packages(root=tmp_path)
    assert len(reports) == 1
    assert reports[0][1].ok is False
    text, ok = format_community_validation_report(reports)
    assert ok is False
    assert "broken-pack" in text or "other-id" in text


def test_hub_validate_community_cli():
    runner = CliRunner()
    result = runner.invoke(main, ["hub", "validate-community"])
    assert result.exit_code == 0, result.output
    assert "typing-it" in result.output
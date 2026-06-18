import json
from pathlib import Path

from click.testing import CliRunner

from expando.cli import main
from expando.hub_marketplace import (
    find_cross_package_trigger_duplicates,
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


def test_find_cross_package_trigger_duplicates_detects_conflict(tmp_path: Path):
    community = tmp_path / "packages" / "community"
    for package_id in ("pack-a", "pack-b"):
        package_dir = community / package_id
        package_dir.mkdir(parents=True)
        (package_dir / "hub.json").write_text(
            json.dumps({"id": package_id, "name": package_id, "description": "d"}),
            encoding="utf-8",
        )
        (package_dir / "snippets.yml").write_text(
            "matches:\n  - trigger: ':shared'\n    replace: 'x'\n",
            encoding="utf-8",
        )

    duplicates = find_cross_package_trigger_duplicates(root=tmp_path)
    assert duplicates == {":shared": ["pack-a", "pack-b"]}
    text, ok = format_community_validation_report([], trigger_duplicates=duplicates)
    assert ok is False
    assert ":shared" in text


def test_find_cross_package_trigger_duplicates_ignores_regex(tmp_path: Path):
    community = tmp_path / "packages" / "community"
    for package_id in ("pack-a", "pack-b"):
        package_dir = community / package_id
        package_dir.mkdir(parents=True)
        (package_dir / "hub.json").write_text(
            json.dumps({"id": package_id, "name": package_id, "description": "d"}),
            encoding="utf-8",
        )
        (package_dir / "snippets.yml").write_text(
            "matches:\n  - trigger: ':shared'\n    regex: true\n    replace: 'x'\n",
            encoding="utf-8",
        )

    assert find_cross_package_trigger_duplicates(root=tmp_path) == {}
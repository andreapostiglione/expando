import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from expando.cli import main
from expando.hub_marketplace import init_contributor_package


def test_init_contributor_package_creates_template(tmp_path: Path):
    package_dir = init_contributor_package(
        tmp_path,
        "my-pack",
        name="My Pack",
        description="Test community package",
        author="Tester",
        tags=["community", "demo"],
    )
    assert package_dir == tmp_path / "my-pack"
    manifest = json.loads((package_dir / "hub.json").read_text(encoding="utf-8"))
    assert manifest["id"] == "my-pack"
    assert manifest["name"] == "My Pack"
    assert manifest["description"] == "Test community package"
    assert manifest["author"] == "Tester"
    assert manifest["tags"] == ["community", "demo"]
    snippets = (package_dir / "snippets.yml").read_text(encoding="utf-8")
    assert "matches:" in snippets
    assert ":mypack" in snippets


def test_init_contributor_package_refuses_existing_without_force(tmp_path: Path):
    package_dir = tmp_path / "existing"
    package_dir.mkdir()
    (package_dir / "hub.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="already exists"):
        init_contributor_package(tmp_path, "existing", name="Existing", description="x")


def test_init_contributor_package_force_overwrites(tmp_path: Path):
    package_dir = tmp_path / "existing"
    package_dir.mkdir()
    (package_dir / "old.txt").write_text("stale", encoding="utf-8")
    init_contributor_package(
        tmp_path,
        "existing",
        name="Fresh",
        description="Updated",
        force=True,
    )
    manifest = json.loads((package_dir / "hub.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "Fresh"
    assert (package_dir / "snippets.yml").exists()


def test_hub_submit_init_cli(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "hub",
            "submit",
            "init",
            "cli-pack",
            "--name",
            "CLI Pack",
            "--description",
            "From CLI",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "cli-pack" / "hub.json").exists()
    assert "cli-pack" in result.output
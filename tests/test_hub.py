from pathlib import Path

import pytest

from expando.hub import (
    HubPackage,
    fetch_registry,
    install_hub_package,
    publish_hub_package,
    search_hub_packages,
    uninstall_hub_package,
    validate_hub_package_dir,
)
from expando.paths import package_root


def test_fetch_registry_uses_local_index():
    packages = fetch_registry()
    ids = {package.id for package in packages}
    assert "core" in ids
    assert "dev" in ids
    assert "email-it" in ids
    assert "legal-it" in ids
    assert "social" in ids
    assert "medical-it" in ids
    assert "sales-it" in ids
    assert "support-it" in ids
    assert len(packages) >= 8


def test_search_hub_packages():
    results = search_hub_packages("firma")
    assert results
    assert results[0].id == "core"


def test_install_and_uninstall_local_package(tmp_path: Path):
    config_dir = tmp_path / "expando"
    path = install_hub_package(config_dir, "core", force=True)
    assert path.exists()
    assert any(path.glob("*.yml"))

    assert uninstall_hub_package(config_dir, "core") is True
    assert not path.exists()


def test_install_rejects_unknown_package(tmp_path: Path):
    with pytest.raises(ValueError, match="Unknown hub package"):
        install_hub_package(tmp_path, "does-not-exist")


def test_validate_and_publish_local_package(tmp_path: Path):
    source = package_root() / "default_config" / "match" / "packages" / "social"
    report = validate_hub_package_dir(source)
    assert report.ok
    assert report.match_count >= 4

    config_dir = tmp_path / "expando"
    published = publish_hub_package(source, config_dir=config_dir, install=True)
    assert published.ok
    assert published.installed_to is not None
    assert any(published.installed_to.glob("snippets.yml"))


def test_publish_rejects_invalid_package(tmp_path: Path):
    bad_dir = tmp_path / "broken"
    bad_dir.mkdir()
    report = validate_hub_package_dir(bad_dir)
    assert not report.ok
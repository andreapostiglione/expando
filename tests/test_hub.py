from pathlib import Path

import pytest

from expando.hub import (
    HubPackage,
    fetch_registry,
    install_hub_package,
    search_hub_packages,
    uninstall_hub_package,
)


def test_fetch_registry_uses_local_index():
    packages = fetch_registry()
    ids = {package.id for package in packages}
    assert "core" in ids
    assert "dev" in ids
    assert "email-it" in ids
    assert "legal-it" in ids


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
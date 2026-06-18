from pathlib import Path

from expando.hub import fetch_registry, install_hub_package


def test_fetch_registry_includes_approved_community_packages(monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    packages = fetch_registry()
    ids = {item.id for item in packages}
    assert "typing-it" in ids
    assert "meeting-it" in ids
    assert "writing-it" in ids


def test_install_community_package_from_local_source(tmp_path: Path):
    config_dir = tmp_path / "expando"
    path = install_hub_package(config_dir, "typing-it", force=True)
    snippets = path / "snippets.yml"
    assert snippets.exists()
    content = snippets.read_text(encoding="utf-8")
    assert ":addr" in content
    assert ":tel" in content
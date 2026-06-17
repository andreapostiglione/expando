from expando.registry_catalog import build_registry_catalog, format_registry_json


def test_build_registry_catalog(tmp_path):
    config_dir = tmp_path / "expando"
    (config_dir / "match" / "packages" / "core").mkdir(parents=True)
    (config_dir / "match" / "packages" / "core" / "snippets.yml").write_text(
        "matches:\n  - trigger: ':pkg'\n    replace: ok\n",
        encoding="utf-8",
    )
    catalog = build_registry_catalog(config_dir)
    assert len(catalog.hub_packages) >= 8
    assert "core" in catalog.installed_packages
    payload = format_registry_json(catalog)
    assert '"hub_packages"' in payload
import json
from pathlib import Path
from unittest.mock import patch

from expando.config import compile_matches, load_config
from expando.hub import HubPackage
from expando.hub_marketplace import (
    find_community_official_trigger_collisions,
    marketplace_pending_metadata_diffs,
)
from expando.paths import package_root


def _official_package(package_id: str) -> HubPackage:
    return HubPackage(
        id=package_id,
        name=package_id,
        description="official",
        author="Expando",
    )


def test_find_community_official_trigger_collisions(tmp_path: Path):
    official = tmp_path / "default_config" / "match" / "packages" / "core"
    official.mkdir(parents=True)
    (official / "snippets.yml").write_text(
        "matches:\n  - trigger: ':email'\n    replace: 'official@example.com'\n",
        encoding="utf-8",
    )

    community = tmp_path / "packages" / "community" / "typing-it"
    community.mkdir(parents=True)
    (community / "hub.json").write_text(
        json.dumps({"id": "typing-it", "name": "Typing", "description": "d"}),
        encoding="utf-8",
    )
    (community / "snippets.yml").write_text(
        "matches:\n  - trigger: ':email'\n    replace: 'community@example.com'\n",
        encoding="utf-8",
    )

    with patch("expando.hub.fetch_registry", return_value=[_official_package("core")]):
        collisions = find_community_official_trigger_collisions(root=tmp_path)

    assert collisions == {":email": [("typing-it", "core")]}


def test_official_packages_compile_without_literal_trigger_conflicts():
    config = load_config(package_root() / "default_config")

    compile_matches(config.matches)


def test_marketplace_pending_metadata_diffs_detects_missing_and_changed(tmp_path, monkeypatch):
    marketplace = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(marketplace))
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_URL", "https://example.com/marketplace.json")
    marketplace.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {
                        "id": "local-pending",
                        "name": "Local Name",
                        "description": "d",
                        "status": "pending",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    remote = {
        "version": 1,
        "packages": [
            {
                "id": "fresh-submit",
                "name": "Fresh",
                "description": "d",
                "author": "Alice",
                "status": "pending",
            },
            {
                "id": "local-pending",
                "name": "Remote Name",
                "description": "d",
                "status": "pending",
            },
        ],
    }

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        diffs = marketplace_pending_metadata_diffs()

    by_id = {item.package_id: item for item in diffs}
    assert by_id["fresh-submit"].missing_local is True
    assert by_id["fresh-submit"].remote_name == "Fresh"
    assert by_id["local-pending"].changed_fields
    assert by_id["local-pending"].changed_fields[0][0] == "name"

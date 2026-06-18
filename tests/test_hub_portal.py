import json
from pathlib import Path

import pytest

from expando.hub_marketplace import (
    build_publishable_portal_index,
    export_portal_index,
    marketplace_portal_stats,
    sync_remote_marketplace_index,
)


@pytest.fixture
def marketplace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(path))
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_URL", raising=False)
    return path


def test_export_portal_index_only_includes_approved(marketplace_file: Path):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {"id": "a", "name": "A", "description": "one", "status": "approved"},
                    {"id": "b", "name": "B", "description": "two", "status": "pending"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = build_publishable_portal_index()
    assert len(payload["packages"]) == 1
    assert payload["packages"][0]["id"] == "a"
    assert "updated_at" in payload

    destination = marketplace_file.parent / "published.json"
    export_portal_index(destination)
    exported = json.loads(destination.read_text(encoding="utf-8"))
    assert exported["packages"][0]["id"] == "a"


def test_sync_remote_marketplace_index_merges_entries(
    marketplace_file: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {"id": "local", "name": "Local", "description": "x", "status": "pending"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    remote_payload = json.dumps(
        {
            "version": 1,
            "packages": [
                {
                    "id": "remote",
                    "name": "Remote",
                    "description": "y",
                    "status": "approved",
                },
                {
                    "id": "local",
                    "name": "Local updated",
                    "description": "z",
                    "status": "approved",
                },
            ],
        }
    ).encode("utf-8")

    class FakeResponse:
        def read(self) -> bytes:
            return remote_payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_URL", "https://example.com/marketplace.json")
    monkeypatch.setattr("expando.hub_marketplace.urlopen", lambda *args, **kwargs: FakeResponse())

    stats = sync_remote_marketplace_index()
    assert stats == {"added": 1, "updated": 1, "unchanged": 0}

    data = json.loads(marketplace_file.read_text(encoding="utf-8"))
    ids = {item["id"]: item for item in data["packages"]}
    assert ids["remote"]["status"] == "approved"
    assert ids["local"]["name"] == "Local updated"


def test_marketplace_portal_stats_counts(marketplace_file: Path):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {"id": "a", "name": "A", "description": "", "status": "pending"},
                    {"id": "b", "name": "B", "description": "", "status": "approved"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    stats = marketplace_portal_stats()
    assert stats["counts"]["pending"] == 1
    assert stats["counts"]["approved"] == 1
    assert stats["total"] == 2
import json
from unittest.mock import patch

import pytest

from expando.hub_marketplace import marketplace_sync_preview, sync_remote_marketplace_index


@pytest.fixture
def marketplace_file(tmp_path, monkeypatch):
    path = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(path))
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {
                        "id": "typing-it",
                        "name": "Typing IT",
                        "description": "d",
                        "status": "approved",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_marketplace_sync_preview_counts_diff(marketplace_file, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_URL", "https://example.com/marketplace.json")
    remote = {
        "version": 1,
        "packages": [
            {
                "id": "typing-it",
                "name": "Typing IT",
                "description": "d",
                "status": "approved",
            },
            {
                "id": "meeting-it",
                "name": "Meeting IT",
                "description": "d",
                "status": "approved",
            },
        ],
    }

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        preview = marketplace_sync_preview()

    assert preview is not None
    assert preview["sync"]["added"] == 1
    assert preview["sync"]["unchanged"] == 1
    assert preview["local_approved"] == 1
    assert preview["remote_approved"] == 2


def test_sync_remote_marketplace_index_dry_run_does_not_write(marketplace_file, monkeypatch):
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_URL", "https://example.com/marketplace.json")
    remote = {
        "version": 1,
        "packages": [
            {
                "id": "new-pack",
                "name": "New",
                "description": "d",
                "status": "approved",
            }
        ],
    }
    before = marketplace_file.read_text(encoding="utf-8")

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        stats = sync_remote_marketplace_index(dry_run=True)

    assert stats["added"] == 1
    assert marketplace_file.read_text(encoding="utf-8") == before
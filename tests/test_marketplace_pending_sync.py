import json
from unittest.mock import patch

import pytest

from expando.hub_marketplace import marketplace_pending_sync_gaps


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


def test_marketplace_pending_sync_gaps_lists_remote_pending_missing_locally(marketplace_file, monkeypatch):
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
                "id": "fresh-submit",
                "name": "Fresh",
                "description": "d",
                "status": "pending",
            },
        ],
    }

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        gaps = marketplace_pending_sync_gaps()

    assert gaps == ["fresh-submit"]


def test_marketplace_pending_sync_gaps_ignores_local_pending(marketplace_file, monkeypatch):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {
                        "id": "local-pending",
                        "name": "Local",
                        "description": "d",
                        "status": "pending",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_URL", "https://example.com/marketplace.json")
    remote = {
        "version": 1,
        "packages": [
            {
                "id": "local-pending",
                "name": "Local",
                "description": "d",
                "status": "pending",
            }
        ],
    }

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        assert marketplace_pending_sync_gaps() == []
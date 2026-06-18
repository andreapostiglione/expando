import json
from pathlib import Path
from unittest.mock import patch

from expando.hub_marketplace import (
    PendingMetadataDiff,
    marketplace_pending_metadata_diff_document,
    pending_metadata_diff_to_dict,
    write_marketplace_pending_diff_json,
)


def test_pending_metadata_diff_to_dict():
    diff = PendingMetadataDiff(
        package_id="fresh-submit",
        missing_local=True,
        remote_name="Fresh",
        remote_author="Alice",
        changed_fields=[],
    )
    assert pending_metadata_diff_to_dict(diff) == {
        "package_id": "fresh-submit",
        "missing_local": True,
        "remote_name": "Fresh",
        "remote_author": "Alice",
        "changed_fields": [],
    }


def test_marketplace_pending_metadata_diff_document_and_write(tmp_path: Path, monkeypatch):
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
            }
        ],
    }

    with patch(
        "expando.hub_marketplace.fetch_remote_marketplace_document",
        return_value=remote,
    ):
        document = marketplace_pending_metadata_diff_document()
        destination = tmp_path / "pending-diff.json"
        write_marketplace_pending_diff_json(destination)

    assert document["version"] == 1
    assert len(document["diffs"]) == 1
    assert document["diffs"][0]["package_id"] == "fresh-submit"
    assert destination.exists()
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written["diffs"][0]["missing_local"] is True
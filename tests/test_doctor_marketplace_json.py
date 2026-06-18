import json
from unittest.mock import patch

from expando.hub import HubPackage
from expando.hub_marketplace import (
    PendingMetadataDiff,
    doctor_marketplace_document,
)


def _community_package(package_id: str) -> HubPackage:
    return HubPackage(
        id=package_id,
        name=package_id,
        description="community",
        author="Contributor",
        status="approved",
    )


def test_doctor_marketplace_document_includes_community_and_pending_diff(monkeypatch):
    monkeypatch.setenv(
        "EXPANDO_HUB_MARKETPLACE_URL",
        "https://example.com/marketplace.json",
    )
    with patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        return_value=[_community_package("typing-it")],
    ), patch(
        "expando.hub.fetch_registry",
        return_value=[HubPackage(id="core", name="Core", description="d", author="Expando")],
    ), patch(
        "expando.hub_marketplace.marketplace_sync_preview",
        return_value={
            "sync": {"added": 1, "updated": 0, "unchanged": 2},
            "local_total": 3,
            "local_approved": 2,
            "remote_approved": 3,
        },
    ), patch(
        "expando.hub_marketplace.marketplace_pending_metadata_diffs",
        return_value=[
            PendingMetadataDiff(
                package_id="fresh-submit",
                missing_local=True,
                remote_name="Fresh",
                remote_author="Alice",
                changed_fields=[],
            )
        ],
    ), patch(
        "expando.hub_marketplace.marketplace_pending_sync_gaps",
        return_value=["fresh-submit"],
    ):
        payload = doctor_marketplace_document(limit=5)

    assert payload["available"] is True
    assert payload["community_count"] == 1
    assert payload["community_packages"][0]["id"] == "typing-it"
    assert payload["sync_preview"]["sync"]["added"] == 1
    assert payload["pending_diffs"][0]["package_id"] == "fresh-submit"
    assert payload["pending_sync_gaps"] == ["fresh-submit"]
    json.dumps(payload)
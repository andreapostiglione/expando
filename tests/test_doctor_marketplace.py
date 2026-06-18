from unittest.mock import patch

from expando.hub import HubPackage
from expando.hub_marketplace import PendingMetadataDiff, doctor_marketplace_lines


def _package(package_id: str, name: str) -> HubPackage:
    return HubPackage(
        id=package_id,
        name=name,
        description=f"{name} description",
        author="Community",
        tags=["community"],
    )


def test_doctor_marketplace_lists_community_packages():
    official = [_package("dev", "Dev")]
    community = [
        _package("typing-it", "Typing IT"),
        _package("meeting-it", "Meeting IT"),
    ]

    with patch("expando.hub_marketplace.marketplace_index_url", return_value="https://example.com/hub.json"), patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        return_value=official + community,
    ), patch("expando.hub.fetch_registry", return_value=official):
        lines = doctor_marketplace_lines(limit=5)

    text = "\n".join(lines)
    assert "marketplace" in text.lower()
    assert "typing-it" in text
    assert "meeting-it" in text
    assert "hub install" in text


def test_doctor_marketplace_unavailable_remote():
    with patch("expando.hub_marketplace.marketplace_index_url", return_value="https://example.com/hub.json"), patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        side_effect=RuntimeError("offline"),
    ):
        lines = doctor_marketplace_lines()

    text = "\n".join(lines)
    assert "unavailable" in text.lower() or "non disponibile" in text.lower()


def test_doctor_marketplace_empty_community():
    official = [_package("dev", "Dev")]

    with patch("expando.hub_marketplace.marketplace_index_url", return_value=None), patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        return_value=official,
    ), patch("expando.hub.fetch_registry", return_value=official):
        lines = doctor_marketplace_lines()

    text = "\n".join(lines)
    assert "community" in text.lower() or "nessun package" in text.lower()


def test_doctor_marketplace_includes_sync_preview():
    official = [_package("dev", "Dev")]
    community = [_package("typing-it", "Typing IT")]

    with patch("expando.hub_marketplace.marketplace_index_url", return_value="https://example.com/hub.json"), patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        return_value=official + community,
    ), patch("expando.hub.fetch_registry", return_value=official), patch(
        "expando.hub_marketplace.marketplace_sync_preview",
        return_value={
            "sync": {"added": 1, "updated": 0, "unchanged": 2},
            "local_total": 3,
            "local_approved": 2,
            "remote_approved": 3,
        },
    ):
        lines = doctor_marketplace_lines(limit=5)

    text = "\n".join(lines)
    assert "sync" in text.lower() or "merge" in text.lower()
    assert "aggiunti=1" in text or "added=1" in text
    assert "hub portal sync" in text


def test_doctor_marketplace_shows_pending_metadata_diff():
    official = [_package("dev", "Dev")]

    with patch("expando.hub_marketplace.marketplace_index_url", return_value="https://example.com/hub.json"), patch(
        "expando.hub_marketplace.fetch_marketplace_packages",
        return_value=official,
    ), patch("expando.hub.fetch_registry", return_value=official), patch(
        "expando.hub_marketplace.marketplace_sync_preview",
        return_value=None,
    ), patch(
        "expando.hub_marketplace.marketplace_pending_metadata_diffs",
        return_value=[
            PendingMetadataDiff(
                package_id="new-submit",
                missing_local=True,
                remote_name="New Submit",
                remote_author="Contributor",
                changed_fields=[],
            ),
            PendingMetadataDiff(
                package_id="changed-pack",
                missing_local=False,
                remote_name="Changed",
                remote_author="Contributor",
                changed_fields=[("name", "Old", "New")],
            ),
        ],
    ):
        lines = doctor_marketplace_lines(limit=5)

    text = "\n".join(lines)
    assert "new-submit" in text
    assert "changed-pack" in text
    assert "name" in text
    assert "pending" in text.lower() or "Pending" in text
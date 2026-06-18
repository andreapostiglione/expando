import json
from pathlib import Path

import pytest

from expando.hub_marketplace import (
    fetch_marketplace_packages,
    list_marketplace_queue,
    marketplace_index_path,
    queue_marketplace_submission,
    review_marketplace_package,
)
from expando.paths import package_root


@pytest.fixture
def marketplace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(path))
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_URL", raising=False)
    return path


def test_queue_and_approve_submission(marketplace_file: Path):
    source = package_root() / "default_config" / "match" / "packages" / "social"
    package = queue_marketplace_submission(source)
    assert package.status == "pending"
    assert package.id == "social"

    pending = list_marketplace_queue(status="pending")
    assert len(pending) == 1
    assert fetch_marketplace_packages() == []

    approved = review_marketplace_package("social", "approve", reviewer="maintainer")
    assert approved.status == "approved"
    assert approved.reviewer == "maintainer"

    visible = fetch_marketplace_packages()
    assert len(visible) == 1
    assert visible[0].id == "social"


def test_reject_submission_hides_package(marketplace_file: Path):
    source = package_root() / "default_config" / "match" / "packages" / "social"
    queue_marketplace_submission(source)
    rejected = review_marketplace_package("social", "reject", note="duplicate")
    assert rejected.status == "rejected"
    assert rejected.review_note == "duplicate"
    assert fetch_marketplace_packages() == []


def test_marketplace_index_persists_status_fields(marketplace_file: Path):
    source = package_root() / "default_config" / "match" / "packages" / "social"
    queue_marketplace_submission(source)
    data = json.loads(marketplace_index_path().read_text(encoding="utf-8"))
    entry = data["packages"][0]
    assert entry["status"] == "pending"
    assert "submitted_at" in entry
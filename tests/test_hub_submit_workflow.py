import json
from pathlib import Path

import pytest

from expando.hub_marketplace import (
    contributor_submission_status,
    format_submission_status_report,
    marketplace_index_path,
    run_contributor_submission_workflow,
)


@pytest.fixture
def marketplace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(path))
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    path.write_text(
        json.dumps({"version": 1, "packages": []}) + "\n",
        encoding="utf-8",
    )
    return path


def test_run_contributor_submission_workflow_queues_package(
    marketplace_file: Path,
    tmp_path: Path,
):
    source = Path(__file__).resolve().parents[1] / "packages" / "community" / "typing-it"
    bundle_path = tmp_path / "typing-it.zip"
    result = run_contributor_submission_workflow(
        source,
        bundle_path=bundle_path,
        queue=True,
    )
    assert result.package_id == "typing-it"
    assert result.queued is True
    assert bundle_path.exists()

    status = contributor_submission_status("typing-it")
    assert status.found is True
    assert status.status == "pending"
    text = format_submission_status_report(status)
    assert "typing-it" in text
    assert "pending" in text

    data = json.loads(marketplace_index_path().read_text(encoding="utf-8"))
    assert any(item["id"] == "typing-it" for item in data["packages"])


def test_contributor_submission_status_official_package():
    status = contributor_submission_status("dev")
    assert status.in_official_index is True
    text = format_submission_status_report(status)
    assert "dev" in text
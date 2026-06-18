import json
from pathlib import Path

import pytest

from expando.hub_marketplace import (
    DEFAULT_MARKETPLACE_URL,
    build_maintainer_hub_html,
    build_portal_site_html,
    build_publishable_portal_index,
    export_portal_index,
    marketplace_index_url,
    marketplace_portal_stats,
    publish_portal_site,
    sync_remote_marketplace_index,
)


@pytest.fixture
def marketplace_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "marketplace.json"
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_PATH", str(path))
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_URL", raising=False)
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
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


def test_publish_portal_site_writes_html_and_json(marketplace_file: Path, tmp_path: Path):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {
                        "id": "social",
                        "name": "Social",
                        "description": "Social snippets",
                        "author": "Andrea",
                        "tags": ["social"],
                        "status": "approved",
                    },
                    {
                        "id": "pending",
                        "name": "Pending",
                        "description": "hidden",
                        "status": "pending",
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    html_path = tmp_path / "hub-marketplace.html"
    json_path = tmp_path / "hub" / "marketplace.json"
    paths = publish_portal_site(html_path=html_path, json_path=json_path)

    assert paths["html"] == html_path
    assert paths["json"] == json_path
    assert "suggestions_html" in paths
    assert "maintainer_html" in paths
    html = html_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    suggestions = paths["suggestions_html"].read_text(encoding="utf-8")
    assert "Social" in html
    assert "hub-maintainer.html" in html
    assert "hub-trigger-suggestions.html" in html
    assert "Pending" not in html
    assert len(payload["packages"]) == 1
    assert payload["packages"][0]["id"] == "social"
    assert "Community Trigger Dashboard" in suggestions
    maintainer = paths["maintainer_html"].read_text(encoding="utf-8")
    assert "Maintainer Portal" in maintainer
    assert "hub-marketplace.html" in maintainer


def test_build_maintainer_hub_html_links_portal_pages():
    html = build_maintainer_hub_html(updated_at="2026-06-18T10:00:00+00:00")
    assert "Maintainer Portal" in html
    assert "hub-marketplace.html" in html
    assert "hub-trigger-suggestions.html" in html
    assert "publish-site" in html


def test_build_portal_site_html_escapes_markup():
    payload = {
        "updated_at": "2026-06-18T00:00:00+00:00",
        "packages": [
            {
                "id": "x",
                "name": "<script>",
                "description": "A & B",
                "author": "Me",
                "tags": ["<tag>"],
            }
        ],
    }
    html = build_portal_site_html(payload)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "A &amp; B" in html


def test_marketplace_index_url_defaults_to_github_pages(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_URL", raising=False)
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_DISABLE", raising=False)
    assert marketplace_index_url() == DEFAULT_MARKETPLACE_URL


def test_marketplace_index_url_can_be_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("EXPANDO_HUB_MARKETPLACE_URL", raising=False)
    monkeypatch.setenv("EXPANDO_HUB_MARKETPLACE_DISABLE", "1")
    assert marketplace_index_url() is None


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
import json
from pathlib import Path

import pytest

from expando.hub_marketplace import (
    DEFAULT_MARKETPLACE_URL,
    build_hub_index_document,
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
    health_html_path = tmp_path / "doctor-health.html"
    health_json_path = tmp_path / "hub" / "doctor-full.json"
    hub_index_path = tmp_path / "hub" / "index.json"
    paths = publish_portal_site(
        html_path=html_path,
        json_path=json_path,
        health_html_path=health_html_path,
        health_json_path=health_json_path,
        hub_index_json_path=hub_index_path,
    )

    assert paths["html"] == html_path
    assert paths["json"] == json_path
    assert "suggestions_html" in paths
    assert "maintainer_html" in paths
    assert "validation_json" in paths
    assert "health_html" in paths
    assert "health_json" in paths
    assert "hub_index_json" in paths
    html = html_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    suggestions = paths["suggestions_html"].read_text(encoding="utf-8")
    assert "Social" in html
    assert "hub-maintainer.html" in html
    assert "hub-trigger-suggestions.html" in html
    assert "doctor-health.html" in html
    assert "hub/index.json" in html
    assert "Pending" not in html
    assert len(payload["packages"]) == 1
    assert payload["packages"][0]["id"] == "social"
    assert "Community Trigger Dashboard" in suggestions
    maintainer = paths["maintainer_html"].read_text(encoding="utf-8")
    assert "Maintainer Portal" in maintainer
    assert "hub-marketplace.html" in maintainer
    assert "doctor-health.html" in maintainer
    health_html = paths["health_html"].read_text(encoding="utf-8")
    assert "Expando Health Dashboard" in health_html
    assert "Publish-site snapshot" in health_html
    health_json = json.loads(paths["health_json"].read_text(encoding="utf-8"))
    assert health_json.get("publish_context") == "github-pages"
    assert "doctor" in health_json
    hub_index = json.loads(paths["hub_index_json"].read_text(encoding="utf-8"))
    assert len(hub_index["artifacts"]) == 3
    assert hub_index["artifacts"][2]["id"] == "doctor-full"
    validation = json.loads(paths["validation_json"].read_text(encoding="utf-8"))
    assert "packages" in validation
    assert "trigger_suggestions" in validation


def test_build_maintainer_hub_html_links_portal_pages():
    html = build_maintainer_hub_html(
        updated_at="2026-06-18T10:00:00+00:00",
        validation={
            "ok": True,
            "packages": [{"package_id": "typing-it", "ok": True}],
            "trigger_suggestions": [{"community_trigger": ":x", "official_trigger": ":y"}],
            "trigger_duplicates": {},
            "official_collisions": {},
        },
    )
    assert "Maintainer Portal" in html
    assert "hub-marketplace.html" in html
    assert "hub-trigger-suggestions.html" in html
    assert "community-validation.json" in html
    assert "doctor-health.html" in html
    assert "similarity warnings=1" in html
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


def test_publish_portal_site_skips_health_when_env_set(
    marketplace_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    marketplace_file.write_text(
        json.dumps(
            {
                "version": 1,
                "packages": [
                    {
                        "id": "social",
                        "name": "Social",
                        "description": "Social snippets",
                        "status": "approved",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    health_html_path = tmp_path / "doctor-health.html"
    health_json_path = tmp_path / "hub" / "doctor-full.json"
    health_html_path.write_text("<html>release snapshot</html>", encoding="utf-8")
    health_json_path.parent.mkdir(parents=True, exist_ok=True)
    health_json_path.write_text(
        json.dumps(
            {
                "publish_context": "release-ci",
                "release_context": "v3.18.0",
                "generated_at": "2026-06-19T00:00:00+00:00",
                "doctor": {"ok": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("EXPANDO_PUBLISH_SITE_SKIP_HEALTH", "1")
    paths = publish_portal_site(
        html_path=tmp_path / "hub-marketplace.html",
        json_path=tmp_path / "hub" / "marketplace.json",
        health_html_path=health_html_path,
        health_json_path=health_json_path,
        hub_index_json_path=tmp_path / "hub" / "index.json",
    )
    assert paths["health_html"].read_text(encoding="utf-8") == "<html>release snapshot</html>"
    hub_index = json.loads(paths["hub_index_json"].read_text(encoding="utf-8"))
    assert hub_index["artifacts"][2]["release_context"] == "v3.18.0"


def test_build_hub_index_document_includes_health_metadata(tmp_path: Path):
    health_json_path = tmp_path / "doctor-full.json"
    health_json_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-19T08:00:00+00:00",
                "publish_context": "release-ci",
                "release_context": "v3.18.0",
                "doctor": {"ok": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    document = build_hub_index_document(
        marketplace_payload={"updated_at": "2026-06-19T07:00:00+00:00", "packages": [{"id": "a"}]},
        validation_document={"generated_at": "2026-06-19T07:30:00+00:00", "ok": True},
        health_json_path=health_json_path,
    )
    assert document["artifacts"][0]["package_count"] == 1
    assert document["artifacts"][2]["release_context"] == "v3.18.0"


def test_build_portal_site_html_includes_validation_badge():
    payload = {
        "updated_at": "2026-06-18T00:00:00+00:00",
        "packages": [],
    }
    html = build_portal_site_html(
        payload,
        validation={
            "ok": False,
            "trigger_duplicates": {":dup": ["a", "b"]},
            "trigger_suggestions": [{"community_trigger": ":x", "official_trigger": ":y"}],
        },
    )
    assert "community-validation.json" in html
    assert "similarity warnings=1" in html
    assert "duplicates=1" in html
    assert 'badge fail">Issues</span>' in html


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
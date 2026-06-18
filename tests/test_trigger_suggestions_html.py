import json
from pathlib import Path

from expando.hub_marketplace import (
    build_trigger_suggestions_html,
    community_validation_document,
    write_trigger_suggestions_html,
)


def test_community_validation_document_shape():
    document = community_validation_document()
    assert document["version"] == 1
    assert "packages" in document
    assert "trigger_suggestions" in document
    assert "ok" in document
    json.dumps(document)


def test_build_trigger_suggestions_html_includes_tables():
    document = {
        "generated_at": "2026-06-18T10:00:00+00:00",
        "ok": True,
        "packages": [{"package_id": "typing-it", "ok": True, "match_count": 3}],
        "trigger_duplicates": {},
        "official_collisions": {},
        "trigger_suggestions": [
            {
                "community_trigger": ":emails",
                "official_trigger": ":email",
                "score": 0.95,
                "reason": "prefix",
                "community_package": "typing-it",
                "official_package": "email-it",
            }
        ],
    }
    html_text = build_trigger_suggestions_html(document)
    assert "Community Trigger Dashboard" in html_text
    assert ":emails" in html_text
    assert "prefix" in html_text
    assert "typing-it" in html_text


def test_write_trigger_suggestions_html(tmp_path: Path):
    destination = tmp_path / "trigger-dashboard.html"
    path = write_trigger_suggestions_html(destination, root=tmp_path / "empty-root")
    assert path == destination
    assert destination.exists()
    assert "Community Trigger Dashboard" in destination.read_text(encoding="utf-8")
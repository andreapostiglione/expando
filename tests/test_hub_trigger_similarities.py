import json
from pathlib import Path
from unittest.mock import patch

from expando.hub import HubPackage
from expando.hub_marketplace import (
    TriggerSimilaritySuggestion,
    find_community_official_trigger_similarities,
    format_community_validation_report,
    trigger_similarity_suggestion_to_dict,
)


def _official_package(package_id: str) -> HubPackage:
    return HubPackage(
        id=package_id,
        name=package_id,
        description="official",
        author="Expando",
    )


def test_find_community_official_trigger_similarities_prefix_and_levenshtein(tmp_path: Path):
    official = tmp_path / "default_config" / "match" / "packages" / "core"
    official.mkdir(parents=True)
    (official / "snippets.yml").write_text(
        "matches:\n"
        "  - trigger: ':email'\n"
        "    replace: 'official@example.com'\n"
        "  - trigger: ':grazie'\n"
        "    replace: 'Grazie'\n",
        encoding="utf-8",
    )

    community = tmp_path / "packages" / "community" / "typing-it"
    community.mkdir(parents=True)
    (community / "hub.json").write_text(
        json.dumps({"id": "typing-it", "name": "Typing", "description": "d"}),
        encoding="utf-8",
    )
    (community / "snippets.yml").write_text(
        "matches:\n"
        "  - trigger: ':emails'\n"
        "    replace: 'community@example.com'\n"
        "  - trigger: ':grazie-it'\n"
        "    replace: 'Grazie mille'\n",
        encoding="utf-8",
    )

    with patch("expando.hub.fetch_registry", return_value=[_official_package("core")]):
        suggestions = find_community_official_trigger_similarities(root=tmp_path)

    pairs = {
        (item.community_trigger, item.official_trigger, item.community_package, item.official_package)
        for item in suggestions
    }
    assert (":emails", ":email", "typing-it", "core") in pairs
    assert (":grazie-it", ":grazie", "typing-it", "core") in pairs
    by_trigger = {(item.community_trigger, item.official_trigger): item for item in suggestions}
    assert by_trigger[(":emails", ":email")].reason == "prefix"
    assert by_trigger[(":emails", ":email")].score >= 0.9
    assert suggestions[0].score >= suggestions[-1].score


def test_format_community_validation_report_keeps_ok_with_similarities_only():
    suggestion = TriggerSimilaritySuggestion(
        community_trigger=":emails",
        official_trigger=":email",
        community_package="typing-it",
        official_package="core",
        score=0.95,
        reason="prefix",
    )
    text, ok = format_community_validation_report(
        [],
        trigger_suggestions=[suggestion],
    )
    assert ok is True
    assert ":emails" in text
    assert ":email" in text


def test_trigger_similarity_suggestion_to_dict():
    item = TriggerSimilaritySuggestion(
        community_trigger=":foo",
        official_trigger=":food",
        community_package="a",
        official_package="b",
        score=0.88,
        reason="prefix",
    )
    assert trigger_similarity_suggestion_to_dict(item) == {
        "community_trigger": ":foo",
        "official_trigger": ":food",
        "community_package": "a",
        "official_package": "b",
        "score": 0.88,
        "reason": "prefix",
    }
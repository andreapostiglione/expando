from __future__ import annotations

import json
import plistlib
from pathlib import Path

import yaml

from expando.external_import import (
    import_raycast_snippets,
    import_textexpander_snippets,
    migrate_raycast_snippets,
    migrate_textexpander_snippets,
)
from expando.raycast_compat import convert_raycast_snippet, load_raycast_snippets
from expando.textexpander_compat import (
    convert_textexpander_snippet,
    parse_textexpander_csv,
    parse_textexpander_plist,
    TextExpanderSnippet,
)


def test_parse_textexpander_csv_with_header(tmp_path: Path):
    csv_path = tmp_path / "email.csv"
    csv_path.write_text(
        "abbreviation,snippet,label\n"
        ";sig,\"Cheers,\\nAndrea\",Email signature\n"
        ",empty,skip me\n",
        encoding="utf-8",
    )
    snippets = parse_textexpander_csv(csv_path)
    assert len(snippets) == 1
    assert snippets[0].abbreviation == ";sig"
    assert "Cheers" in snippets[0].text
    assert snippets[0].label == "Email signature"


def test_parse_textexpander_csv_headerless(tmp_path: Path):
    csv_path = tmp_path / "snippets.csv"
    csv_path.write_text(":hi,Hello there\n", encoding="utf-8")
    snippets = parse_textexpander_csv(csv_path)
    assert len(snippets) == 1
    assert snippets[0].abbreviation == ":hi"
    assert snippets[0].text == "Hello there"


def test_convert_textexpander_snippet_adds_group_label():
    converted = convert_textexpander_snippet(
        TextExpanderSnippet(
            abbreviation=";sig",
            text="Best",
            label="Signature",
            group="Email",
        )
    )
    assert converted is not None
    assert converted["trigger"] == ";sig"
    assert converted["replace"] == "Best"
    assert converted["label"] == "[Email] Signature"


def test_convert_textexpander_snippet_skips_without_trigger():
    assert convert_textexpander_snippet(TextExpanderSnippet(abbreviation="", text="x")) is None


def test_parse_textexpander_plist_excludes_suggested(tmp_path: Path):
    plist_path = tmp_path / "Settings.textexpander"
    data = {
        "snippetsTE2": [
            {
                "uuidString": "a1",
                "abbreviation": ";ok",
                "plainText": "Good",
                "label": "OK",
                "snippetType": 0,
            },
            {
                "uuidString": "b2",
                "abbreviation": "",
                "plainText": "noise",
                "label": "Suggested",
                "snippetType": 0,
            },
        ],
        "groupsTE2": [
            {
                "name": "Work",
                "snippetUUIDs": ["a1"],
            },
            {
                "name": "Suggested Snippets",
                "snippetUUIDs": ["b2"],
            },
        ],
    }
    with plist_path.open("wb") as handle:
        plistlib.dump(data, handle)

    snippets = parse_textexpander_plist(plist_path)
    assert len(snippets) == 1
    assert snippets[0].abbreviation == ";ok"
    assert snippets[0].group == "Work"


def test_import_textexpander_from_csv(tmp_path: Path):
    source = tmp_path / "group.csv"
    source.write_text("abbreviation,snippet\n:te,From TextExpander\n", encoding="utf-8")
    destination = tmp_path / "expando"
    (destination / "match").mkdir(parents=True)

    report = import_textexpander_snippets(destination, source=source, force=True)
    assert report.matches_imported == 1
    imported = yaml.safe_load(
        (destination / "match" / "textexpander-group.yml").read_text(encoding="utf-8")
    )
    assert imported["matches"][0]["trigger"] == ":te"


def test_load_and_convert_raycast_snippets(tmp_path: Path):
    export = tmp_path / "snippets.json"
    export.write_text(
        json.dumps(
            [
                {"name": "Greeting", "text": "Hello", "keyword": ":hi"},
                {"name": "Search only", "text": "No trigger"},
            ]
        ),
        encoding="utf-8",
    )
    snippets = load_raycast_snippets(export)
    assert len(snippets) == 2
    converted = convert_raycast_snippet(snippets[0])
    assert converted is not None
    assert converted["trigger"] == ":hi"
    assert convert_raycast_snippet(snippets[1]) is None


def test_import_raycast_snippets(tmp_path: Path):
    source = tmp_path / "raycast.json"
    source.write_text(
        json.dumps([{"name": "Deploy", "text": "npm run build", "keyword": ";deploy"}]),
        encoding="utf-8",
    )
    destination = tmp_path / "expando"
    (destination / "match").mkdir(parents=True)

    report = import_raycast_snippets(destination, source=source, force=True)
    assert report.matches_imported == 1
    imported = yaml.safe_load(
        (destination / "match" / "raycast-raycast.yml").read_text(encoding="utf-8")
    )
    assert imported["matches"][0]["replace"] == "npm run build"


def test_migrate_textexpander_creates_backup(tmp_path: Path):
    source = tmp_path / "snippets.csv"
    source.write_text("abbreviation,snippet\n:one,One\n", encoding="utf-8")
    destination = tmp_path / "expando"
    (destination / "config").mkdir(parents=True)
    (destination / "match").mkdir(parents=True)
    (destination / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")

    report = migrate_textexpander_snippets(destination, source=source, force=True)
    assert report.backup_path.exists()
    assert report.import_report.matches_imported == 1


def test_migrate_raycast_creates_backup(tmp_path: Path):
    source = tmp_path / "snippets.json"
    source.write_text(
        json.dumps([{"name": "Two", "text": "2", "keyword": ":two"}]),
        encoding="utf-8",
    )
    destination = tmp_path / "expando"
    (destination / "config").mkdir(parents=True)
    (destination / "match").mkdir(parents=True)
    (destination / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")

    report = migrate_raycast_snippets(destination, source=source, force=True)
    assert report.backup_path.exists()
    assert report.import_report.matches_imported == 1
from pathlib import Path

import yaml

from expando.match_store import append_match_entry
from expando.snippet_templates import build_match_from_template, get_template, list_templates


def test_list_templates_includes_email():
    ids = {item.id for item in list_templates()}
    assert "email" in ids
    assert "meeting" in ids


def test_build_match_from_template_sets_trigger():
    entry = build_match_from_template("email", ":reply")
    assert entry["trigger"] == ":reply"
    assert "Grazie" in entry["replace"]


def test_get_template_unknown_raises():
    try:
        get_template("missing")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "missing" in str(exc)


def test_append_template_match(tmp_path: Path):
    config_dir = tmp_path / "expando"
    entry = build_match_from_template("dev", ":commit")
    path = append_match_entry(config_dir, entry, target_file="dev.yml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["matches"][0]["trigger"] == ":commit"
from __future__ import annotations

from pathlib import Path

import yaml

from expando.snippet_editor_data import (
    create_snippet_entry,
    list_match_files,
    preview_snippet_text,
)
from expando.config import Match


def test_create_snippet_with_advanced_rules(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config").mkdir()
    (config_dir / "config" / "default.yml").write_text("app:\n  enabled: true\n")

    entry = create_snippet_entry(
        config_dir,
        ":rx",
        "replacement",
        target_file="dev.yml",
        regex=True,
        if_bundle=["com.apple.mail"],
        when={"app": "Mail"},
        priority=5,
        force_clipboard=True,
    )
    assert entry.match.regex is True
    path = config_dir / "match" / "dev.yml"
    data = yaml.safe_load(path.read_text())
    raw = data["matches"][0]
    assert raw["regex"] is True
    assert raw["if_bundle"] == ["com.apple.mail"]
    assert raw["when"] == {"app": "Mail"}
    assert raw["priority"] == 5
    assert raw["force_clipboard"] is True


def test_list_match_files(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    match_dir = config_dir / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "a.yml").write_text("matches: []\n")
    (match_dir / "b.yml").write_text("matches: []\n")
    assert list_match_files(config_dir) == ["a.yml", "b.yml"]


def test_preview_snippet_text_date_var(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "app:\n  enabled: true\n  shell_allowlist: []\n"
    )
    (config_dir / "match").mkdir()
    match = Match(
        triggers=[":d"],
        replace="Hello world",
        vars=[],
    )
    preview = preview_snippet_text(match, config_dir, replace_text="Hello world")
    assert preview == "Hello world"
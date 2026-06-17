from pathlib import Path

import yaml

from expando.espanso_compat import convert_espanso_match
from expando.espanso_import import import_espanso_config


def test_convert_espanso_match_maps_word_and_force_mode():
    converted = convert_espanso_match(
        {
            "trigger": ":date",
            "replace": "today",
            "word": True,
            "force_mode": "clipboard",
            "propagate_case": True,
        }
    )
    assert converted is not None
    assert converted["word_break"] is True
    assert converted["force_clipboard"] is True
    assert converted["propagate_case"] is True


def test_convert_espanso_match_maps_image_path():
    converted = convert_espanso_match({"trigger": ":img", "image_path": "icons/logo.png"})
    assert converted is not None
    assert converted["image"] == "icons/logo.png"
    assert converted["replace"] == "icons/logo.png"
    assert converted["force_clipboard"] is True


def test_convert_espanso_match_converts_markdown():
    converted = convert_espanso_match({"trigger": ":md", "markdown": "**Hello**"})
    assert converted is not None
    assert converted["replace"] == "Hello"


def test_import_espanso_config(tmp_path: Path):
    source = tmp_path / "espanso"
    (source / "config").mkdir(parents=True)
    (source / "match").mkdir(parents=True)
    (source / "config" / "default.yml").write_text(
        "toggle_key: OFF\nclipboard_threshold: 42\n",
        encoding="utf-8",
    )
    match_data = {
        "global_vars": [{"name": "greet", "type": "plain", "params": {"value": "Hi"}}],
        "matches": [
            {"trigger": ":hello", "replace": "{{greet}} there"},
            {"trigger": ":img", "image_path": "x.png"},
        ],
    }
    (source / "match" / "base.yml").write_text(
        yaml.safe_dump(match_data, allow_unicode=True),
        encoding="utf-8",
    )

    destination = tmp_path / "expando"
    report = import_espanso_config(destination, source=source, force=True)

    assert report.matches_imported >= 1
    assert report.config_merged is True

    imported = yaml.safe_load((destination / "match" / "espanso-base.yml").read_text(encoding="utf-8"))
    assert imported["global_vars"][0]["name"] == "greet"
    assert imported["matches"][0]["trigger"] == ":hello"

    default = yaml.safe_load((destination / "config" / "default.yml").read_text(encoding="utf-8"))
    assert default["toggle_key"] == "OFF"
    assert default["clipboard_threshold"] == 42
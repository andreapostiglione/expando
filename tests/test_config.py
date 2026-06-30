from pathlib import Path

import pytest

from expando.config import ConfigCompileError, Match, compile_matches, load_config, normalize_match
from expando.paths import ensure_default_config


def test_load_default_config():
    root = Path(__file__).resolve().parents[1]
    bundle = load_config(root / "default_config")
    assert len(bundle.matches) >= 3
    assert bundle.app.toggle_key == "ALT"
    triggers = {trigger for match in bundle.matches for trigger in match.triggers}
    assert ":claude" not in triggers
    assert ":ultraclaude" not in triggers


def test_fresh_user_config_does_not_copy_dev_shortcuts(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    config_dir = tmp_path / "config"
    ensure_default_config(config_dir, root)
    assert (config_dir / "match" / "base.yml").exists()
    assert not (config_dir / "match" / "dev.yml").exists()


def test_compile_literal_and_regex():
    matches = [
        Match(triggers=[":hello"], replace="Hello"),
        Match(triggers=[r"\d{4}"], replace="year", regex=True),
    ]
    literal, regex = compile_matches(matches)
    assert ":hello" in literal
    assert literal[":hello"][0].replace == "Hello"
    assert len(regex) == 1


def test_compile_allows_duplicate_triggers_with_when():
    matches = [
        Match(triggers=[":hi"], replace="am", when={"hour": "0-12"}),
        Match(triggers=[":hi"], replace="pm", when={"hour": "12-24"}),
    ]
    literal, _ = compile_matches(matches)
    assert len(literal[":hi"]) == 2


def test_normalize_match_advanced_filters():
    match = normalize_match(
        {
            "trigger": ":x",
            "replace": "X",
            "if_bundle": ["com.apple.Terminal"],
            "unless_title": ["Private"],
        }
    )
    assert match.if_bundle == ["com.apple.Terminal"]
    assert match.unless_title == ["Private"]


def test_compile_matches_rejects_duplicates():
    matches = [
        Match(triggers=[":dup"], replace="one"),
        Match(triggers=[":dup"], replace="two"),
    ]
    with pytest.raises(ConfigCompileError, match="Conflicting"):
        compile_matches(matches)


def test_compile_matches_rejects_invalid_regex():
    matches = [
        Match(triggers=["[invalid"], replace="x", regex=True),
    ]
    with pytest.raises(ConfigCompileError, match="Invalid regex"):
        compile_matches(matches)

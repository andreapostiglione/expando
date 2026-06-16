from pathlib import Path

import pytest

from expando.config import ConfigCompileError, Match, compile_matches, load_config, normalize_match


def test_load_default_config():
    root = Path(__file__).resolve().parents[1]
    bundle = load_config(root / "default_config")
    assert len(bundle.matches) >= 3
    assert bundle.app.toggle_key == "ALT"


def test_compile_literal_and_regex():
    matches = [
        Match(triggers=[":hello"], replace="Hello"),
        Match(triggers=[r"\d{4}"], replace="year", regex=True),
    ]
    literal, regex = compile_matches(matches)
    assert ":hello" in literal
    assert len(regex) == 1


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
    with pytest.raises(ConfigCompileError, match="Duplicate"):
        compile_matches(matches)


def test_compile_matches_rejects_invalid_regex():
    matches = [
        Match(triggers=["[invalid"], replace="x", regex=True),
    ]
    with pytest.raises(ConfigCompileError, match="Invalid regex"):
        compile_matches(matches)
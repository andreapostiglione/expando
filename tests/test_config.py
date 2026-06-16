from pathlib import Path

from expando.config import Match, compile_matches, load_config, normalize_match


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
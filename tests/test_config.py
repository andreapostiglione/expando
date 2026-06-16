from pathlib import Path

from expando.config import compile_matches, load_config


def test_load_default_config():
    root = Path(__file__).resolve().parents[1]
    bundle = load_config(root / "default_config")
    assert len(bundle.matches) >= 3
    assert bundle.app.toggle_key == "ALT"


def test_compile_literal_and_regex():
    from expando.config import Match

    matches = [
        Match(triggers=[":hello"], replace="Hello"),
        Match(triggers=[r"\d{4}"], replace="year", regex=True),
    ]
    literal, regex = compile_matches(matches)
    assert ":hello" in literal
    assert len(regex) == 1
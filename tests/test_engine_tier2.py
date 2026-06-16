from unittest.mock import patch

from expando.app_context import AppContext
from expando.config import AppConfig, ConfigBundle, Match, Variable, load_matches, normalize_match
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def _engine(
    matches: list[Match],
    *,
    respect_secure_input: bool = False,
) -> ExpansionEngine:
    config = ConfigBundle(
        app=AppConfig(respect_secure_input=respect_secure_input),
        matches=matches,
    )
    injector = TextInjector(InjectorSettings())
    return ExpansionEngine(config=config, injector=injector)


def test_engine_higher_priority_wins():
    engine = _engine(
        [
            Match(triggers=[":hel"], replace="short", priority=10),
            Match(triggers=[":hello"], replace="long", priority=1),
        ]
    )
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        for char in ":hello":
            engine.handle_char(char)
        assert injected == ["short"]


def test_engine_propagate_case():
    engine = _engine(
        [Match(triggers=[":HI"], replace="hello", propagate_case=True)]
    )
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        for char in ":HI":
            engine.handle_char(char)
        assert injected == ["HELLO"]


def test_engine_blocks_secure_input():
    engine = _engine(
        [Match(triggers=[":hi"], replace="Hello")],
        respect_secure_input=True,
    )
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ), patch("expando.engine.is_secure_input_active", return_value=True):
        for char in ":hi":
            assert engine.handle_char(char) is False


def test_engine_undo_last():
    engine = _engine([Match(triggers=[":hi"], replace="Hello")])
    deleted: list[int] = []
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: deleted.append(count)  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        for char in ":hi":
            engine.handle_char(char)
        assert injected == ["Hello"]
        assert engine.undo_last() is True
        assert deleted[-1] == len("Hello")
        assert injected[-1] == ":hi"


def test_load_matches_merges_global_vars(tmp_path):
    match_dir = tmp_path / "match"
    match_dir.mkdir()
    (match_dir / "base.yml").write_text(
        """
global_vars:
  - name: greet
    type: plain
    params:
      value: Hi
matches:
  - trigger: ":hello"
    replace: "{{greet}} there"
""".strip(),
        encoding="utf-8",
    )
    matches = load_matches(match_dir)
    assert len(matches) == 1
    assert matches[0].vars[0].name == "greet"


def test_normalize_match_extended_fields():
    match = normalize_match(
        {
            "trigger": ":x",
            "replace": "X",
            "priority": 5,
            "postpone": True,
            "left_word": True,
            "label": "Example",
            "search_terms": ["demo"],
        }
    )
    assert match.priority == 5
    assert match.postpone is True
    assert match.left_word is True
    assert match.label == "Example"
    assert match.search_terms == ["demo"]
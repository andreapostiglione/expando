from unittest.mock import patch

from expando.app_context import AppContext
from expando.config import AppConfig, ConfigBundle, Match
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def _engine(matches: list[Match], blacklist: list[str] | None = None) -> ExpansionEngine:
    config = ConfigBundle(
        app=AppConfig(app_blacklist=blacklist or []),
        matches=matches,
    )
    injector = TextInjector(InjectorSettings())
    return ExpansionEngine(config=config, injector=injector)


def test_engine_skips_match_outside_if_app():
    engine = _engine(
        [Match(triggers=[":hi"], replace="Hello", if_app=["Terminal"])]
    )
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Safari"),
    ):
        assert engine.handle_char("i") is False
        assert engine.handle_char("h") is False


def test_engine_expands_inside_if_app():
    engine = _engine(
        [Match(triggers=[":hi"], replace="Hello", if_app=["Terminal"])]
    )
    engine.injector.inject = lambda *args, **kwargs: None  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        for char in ":hi":
            expanded = engine.handle_char(char)
        assert expanded is True


def test_engine_respects_bundle_filter():
    engine = _engine(
        [Match(triggers=[":hi"], replace="Hello", if_bundle=["com.apple.Terminal"])]
    )
    engine.injector.inject = lambda *args, **kwargs: None  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal", bundle_id="com.apple.Safari"),
    ):
        for char in ":hi":
            assert engine.handle_char(char) is False


def test_engine_force_break_expands_without_word_break():
    engine = _engine(
        [Match(triggers=[":hi"], replace="Hello", word_break=True, force_break=True)]
    )
    engine.injector.inject = lambda *args, **kwargs: None  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        assert engine.handle_char(":") is False
        assert engine.handle_char("h") is False
        assert engine.handle_char("i") is True
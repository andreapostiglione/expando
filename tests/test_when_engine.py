from __future__ import annotations

from unittest.mock import MagicMock, patch

from expando.app_context import AppContext
from expando.config import AppConfig, ConfigBundle, Match
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def test_engine_picks_match_by_when_priority():
    morning = Match(triggers=[":hi"], replace="morning", when={"hour": "0-12"}, priority=5)
    evening = Match(triggers=[":hi"], replace="evening", when={"hour": "12-24"}, priority=5)
    config = ConfigBundle(app=AppConfig(), matches=[evening, morning])
    engine = ExpansionEngine(
        config=config,
        injector=TextInjector(InjectorSettings()),
    )
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ), patch("expando.when_conditions.datetime") as dt:
        dt.now.return_value = MagicMock(hour=9)
        for char in ":hi":
            engine.handle_char(char)
        assert injected == ["morning"]
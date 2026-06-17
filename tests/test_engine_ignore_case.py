from unittest.mock import patch

from expando.app_context import AppContext
from expando.config import AppConfig, ConfigBundle, Match
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def test_engine_ignore_case_trigger():
    engine = ExpansionEngine(
        config=ConfigBundle(
            app=AppConfig(),
            matches=[
                Match(
                    triggers=[":grok"],
                    replace="grok --permission-mode bypassPermissions",
                    ignore_case=True,
                )
            ],
        ),
        injector=TextInjector(InjectorSettings()),
    )
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]
    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="iTerm2"),
    ):
        for char in ":Grok":
            engine.handle_char(char)
    assert injected == ["grok --permission-mode bypassPermissions"]
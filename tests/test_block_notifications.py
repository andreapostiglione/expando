from __future__ import annotations

from unittest.mock import patch

from expando.app_context import AppContext
from expando.block_notifications import BlockNotifier
from expando.config import AppConfig, ConfigBundle, Match, Variable
from expando.engine import ExpansionEngine
from expando.injector import InjectorSettings, TextInjector


def test_block_notifier_respects_cooldown():
    notifier = BlockNotifier(enabled=True, cooldown_seconds=60.0)
    with patch("expando.block_notifications.notify") as notify:
        notifier.notify_secure_input()
        notifier.notify_secure_input()
        notify.assert_called_once()


def test_block_notifier_secure_input_message():
    notifier = BlockNotifier(enabled=True, cooldown_seconds=0.0)
    with patch("expando.block_notifications.notify") as notify:
        notifier.notify_secure_input(trigger=":pwd")
        title, message = notify.call_args.args
        assert title == "Expando"
        assert ":pwd" in message


def test_engine_notifies_when_if_app_blocks():
    config = ConfigBundle(
        app=AppConfig(notify_on_block=True, notify_cooldown_seconds=0),
        matches=[
            Match(
                triggers=[":term"],
                replace="terminal only",
                if_app=["Terminal"],
            )
        ],
    )
    notifier = BlockNotifier(enabled=True, cooldown_seconds=0.0)
    engine = ExpansionEngine(
        config=config,
        injector=TextInjector(InjectorSettings()),
        block_notifier=notifier,
    )
    injected: list[str] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="TextEdit"),
    ), patch("expando.block_notifications.notify") as notify:
        for char in ":term":
            engine.handle_char(char)
        assert injected == []
        notify.assert_called_once()
        assert "TextEdit" in notify.call_args.args[1] or "questa app" in notify.call_args.args[1]


def test_engine_notifies_shell_denied():
    config = ConfigBundle(
        app=AppConfig(
            notify_on_block=True,
            notify_cooldown_seconds=0,
            shell_allowlist=[],
        ),
        matches=[
            Match(
                triggers=[":bad"],
                replace="{{out}}",
                vars=[
                    Variable(
                        name="out",
                        type="shell",
                        params={"cmd": "echo nope"},
                    )
                ],
            )
        ],
    )
    notifier = BlockNotifier(enabled=True, cooldown_seconds=0.0)
    engine = ExpansionEngine(
        config=config,
        injector=TextInjector(InjectorSettings()),
        block_notifier=notifier,
    )
    engine.injector.inject = lambda text, **kwargs: None  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ), patch("expando.block_notifications.notify") as notify:
        for char in ":bad":
            engine.handle_char(char)
        notify.assert_called_once()
        assert ":bad" in notify.call_args.args[1]
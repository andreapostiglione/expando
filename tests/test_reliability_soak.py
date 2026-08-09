"""Reliability soak: layout-safe triggers and press-path expansion."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from expando.app_context import AppContext
from expando.engine import ExpansionEngine, build_engine
from expando.listener import KeyboardService, build_service


class _KeyChar:
    def __init__(self, char: str) -> None:
        self.char = char


def _type(service: KeyboardService, text: str) -> None:
    for char in text:
        service._on_press(_KeyChar(char))


@pytest.fixture
def soak_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "\n".join(
            [
                "toggle_key: ALT",
                "auto_restart: false",
                "respect_secure_input: false",
                "backend: clipboard",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "match" / "base.yml").write_text(
        """
matches:
  - triggers:
      - ":hello"
      - "//hello"
    replace: "Hi there!"
  - triggers:
      - ":grok"
      - ";grok"
      - "//grok"
    replace: "grok --permission-mode bypassPermissions"
    ignore_case: true
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return config_dir


def _expand_text(engine: ExpansionEngine, text: str) -> None:
    engine.clear_buffer()
    for char in text:
        engine.handle_char(char)


def test_soak_colon_and_slash_triggers(soak_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="TextEdit"),
    )
    engine = build_engine(soak_config)
    engine.injector.inject = MagicMock()
    engine.injector.delete_chars = MagicMock()

    for _ in range(20):
        engine.injector.inject.reset_mock()
        _expand_text(engine, ":hello")
        assert engine.injector.inject.called
        assert "Hi there!" in str(engine.injector.inject.call_args)

    for _ in range(20):
        engine.injector.inject.reset_mock()
        _expand_text(engine, "//hello")
        assert engine.injector.inject.called


def test_soak_grok_aliases(soak_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="Terminal", bundle_id="com.apple.Terminal"),
    )
    engine = build_engine(soak_config)
    engine.injector.inject = MagicMock()
    engine.injector.delete_chars = MagicMock()

    for trigger in (":grok", ";grok", "//grok", ":GROK"):
        engine.injector.inject.reset_mock()
        _expand_text(engine, trigger)
        assert engine.injector.inject.called
        assert "bypassPermissions" in str(engine.injector.inject.call_args)


def test_listener_press_path_layout_safe(soak_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="TextEdit"),
    )
    service = build_service(soak_config)
    service.engine.injector.inject = MagicMock()
    service.engine.injector.delete_chars = MagicMock()
    # Sync path (worker not started) must expand layout-safe aliases.
    for trigger in (":hello", "//hello", "//grok"):
        service.engine.clear_buffer()
        service.engine.injector.inject.reset_mock()
        _type(service, trigger)
        assert service.engine.injector.inject.called, (trigger, service.engine._buffer)


def test_engine_terminal_profile_forces_clipboard(soak_config: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="Warp", bundle_id="dev.warp.Warp-Stable"),
    )
    engine = build_engine(soak_config)
    engine.injector.inject = MagicMock()
    engine.injector.delete_chars = MagicMock()
    for char in ":hello":
        engine.handle_char(char)
    kwargs = engine.injector.inject.call_args.kwargs
    assert kwargs.get("force_clipboard") is True

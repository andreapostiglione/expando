from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from expando.app_context import AppContext
from expando.listener import KeyboardService, build_service


@pytest.fixture
def isolated_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "\n".join(
            [
                "toggle_key: ALT",
                "undo_shortcut: CMD+SHIFT+Z",
                "search_shortcut: CMD+SHIFT+E",
                "auto_restart: false",
                "respect_secure_input: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':hi'\n    replace: 'Hello'\n",
        encoding="utf-8",
    )
    return config_dir


@pytest.fixture
def keyboard_service(isolated_config_dir: Path, monkeypatch: pytest.MonkeyPatch) -> KeyboardService:
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="Terminal"),
    )
    service = build_service(isolated_config_dir)
    service.engine.injector.inject = MagicMock()
    service.engine.injector.delete_chars = MagicMock()
    service.engine.injector.move_cursor_left = MagicMock()
    return service


@pytest.fixture
def fake_daemon_command(monkeypatch: pytest.MonkeyPatch) -> None:
    script = Path(__file__).resolve().parent / "fixtures" / "fake_daemon.py"

    def _command(config_dir: Path) -> list[str]:
        return [sys.executable, str(script), str(config_dir)]

    monkeypatch.setattr("expando.daemon._daemon_command", _command)
from __future__ import annotations

import json
import sys
from unittest.mock import patch

from expando import ui_bridge
from expando.ui_cli import main as ui_cli_main


def test_ui_cli_search_does_not_import_snippet_editor(monkeypatch) -> None:
    if "expando.snippet_editor" in sys.modules:
        del sys.modules["expando.snippet_editor"]

    captured: dict[str, object] = {}

    def fake_run_search_picker(items):
        captured["items"] = items
        return {"id": "0", "trigger": ":x"}

    monkeypatch.setattr("expando.ui_native.run_search_picker", fake_run_search_picker)
    monkeypatch.setattr(
        sys,
        "argv",
        ["expando.ui_cli", "search"],
    )
    monkeypatch.setattr(
        sys,
        "stdin",
        type(
            "R",
            (),
            {"read": staticmethod(lambda *_args, **_kwargs: json.dumps({"items": []}))},
        )(),
    )

    ui_cli_main()
    assert "expando.snippet_editor" not in sys.modules
    assert captured["items"] == []


def test_prefer_inprocess_on_darwin(monkeypatch) -> None:
    monkeypatch.delenv("EXPANDO_UI_SUBPROCESS", raising=False)
    monkeypatch.delenv("EXPANDO_HEADLESS", raising=False)
    with patch.object(sys, "platform", "darwin"):
        assert ui_bridge._prefer_inprocess() is True


def test_ui_subprocess_uses_app_launcher_when_in_app_mode(tmp_path, monkeypatch) -> None:
    app_root = tmp_path / "Expando.app"
    launcher = app_root / "Contents" / "MacOS" / "expando"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n", encoding="utf-8")

    from expando.runtime_info import RuntimeInfo

    runtime = RuntimeInfo(
        mode="app",
        executable=str(launcher),
        grant_label="Expando.app",
        grant_hint=str(app_root),
    )
    monkeypatch.setattr("expando.runtime_info.detect_runtime", lambda: runtime)
    argv = ui_bridge._ui_subprocess_argv("search")
    assert argv[:3] == [str(launcher), "-m", "expando.ui_cli"]


def test_show_snippet_editor_passes_initial_new(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_ui_command(command, payload):
        captured["command"] = command
        captured["payload"] = payload
        return {"saved": "1"}

    monkeypatch.setattr(ui_bridge, "run_ui_command", fake_run_ui_command)

    result = ui_bridge.show_snippet_editor("/tmp/expando", initial_new=True)

    assert result == {"saved": "1"}
    assert captured == {
        "command": "editor",
        "payload": {"config_dir": "/tmp/expando", "initial_new": True},
    }

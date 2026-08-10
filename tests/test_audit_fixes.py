"""Regression tests for the 3.29.27 audit fix batch (data integrity + expansion)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml
from pynput.keyboard import Key

from expando.engine import ExpansionEngine
from expando.inject_profiles import app_name_matches_terminal_candidate, is_terminal_app
from expando.snippet_editor_data import (
    empty_snippet_form_state,
    merge_match_update,
    update_snippet_entry,
)


def test_merge_match_update_preserves_aliases_and_unknown_flags():
    existing = {
        "triggers": [":hello", "//hello"],
        "replace": "Hi there!",
        "word_break": True,
        "label": "Greeting",
        "search_terms": ["ciao"],
    }
    merged = merge_match_update(
        existing,
        trigger=":hello",
        replace="Hello world!\n\n",
    )
    assert merged["triggers"] == [":hello", "//hello"]
    assert merged["replace"] == "Hello world!\n\n"
    assert merged["word_break"] is True
    assert merged["label"] == "Greeting"
    assert merged["search_terms"] == ["ciao"]
    assert "trigger" not in merged


def test_update_snippet_entry_preserves_multi_trigger_on_disk(tmp_path: Path):
    config_dir = tmp_path / "expando"
    match_dir = config_dir / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "base.yml").write_text(
        "matches:\n"
        "  - triggers:\n"
        "      - :hello\n"
        "      - //hello\n"
        "    replace: Hi there!\n"
        "    word_break: true\n"
        "    label: Greeting\n",
        encoding="utf-8",
    )
    updated = update_snippet_entry(
        config_dir,
        "base.yml:0",
        trigger=":hello",
        replace="Updated greeting\n",
    )
    assert updated.match.triggers == [":hello", "//hello"]
    assert updated.match.replace == "Updated greeting\n"

    on_disk = yaml.safe_load((match_dir / "base.yml").read_text(encoding="utf-8"))
    entry = on_disk["matches"][0]
    assert entry["triggers"] == [":hello", "//hello"]
    assert entry["replace"] == "Updated greeting\n"
    assert entry["word_break"] is True
    assert entry["label"] == "Greeting"


def test_match_write_is_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_dir = tmp_path / "expando"
    (config_dir / "match").mkdir(parents=True)
    path = config_dir / "match" / "base.yml"
    path.write_text("matches:\n  - trigger: :a\n    replace: A\n", encoding="utf-8")

    calls: list[tuple[str, str]] = []

    def fake_atomic(p: Path, text: str) -> None:
        calls.append((str(p), text))
        Path(p).write_text(text, encoding="utf-8")

    # _write_match_file imports atomic_write_text inside the function body.
    monkeypatch.setattr("expando.atomic_io.atomic_write_text", fake_atomic)

    update_snippet_entry(config_dir, "base.yml:0", trigger=":a", replace="B")
    assert calls, "expected atomic_write_text to be used"
    assert any("B" in body for _, body in calls)
    assert path.read_text(encoding="utf-8")


def test_empty_snippet_form_state_has_no_advanced_inheritance():
    state = empty_snippet_form_state(target_file="dev.yml", trigger=":nuovo")
    assert state["trigger"] == ":nuovo"
    assert state["target_file"] == "dev.yml"
    assert state["replace"] == ""
    assert state["unless_app"] == ""
    assert state["if_bundle"] == ""
    assert state["regex"] == ""
    assert state["image"] == ""
    assert state["priority"] == ""
    assert state["force_clipboard"] == ""
    assert state["form"] == ""
    assert state["vars"] == ""
    assert state["when"] == ""


def test_payload_replace_keeps_trailing_whitespace_via_merge():
    # Body is not stripped by merge/update path.
    merged = merge_match_update(
        {"trigger": ":sig", "replace": "old"},
        trigger=":sig",
        replace="Best regards,\n\n",
    )
    assert merged["replace"] == "Best regards,\n\n"
    assert merged["replace"].endswith("\n\n")


def _engine_with_matches(matches: list) -> ExpansionEngine:
    from expando.config import ConfigBundle, AppConfig, Match, normalize_match

    app = AppConfig()
    bundle = ConfigBundle(app=app, matches=[normalize_match(m) for m in matches])
    injector = MagicMock()
    return ExpansionEngine(bundle, injector)


def test_regex_left_word_is_honored():
    engine = _engine_with_matches(
        [
            {
                "trigger": r"cat",
                "replace": "meow",
                "regex": True,
                "left_word": True,
            }
        ]
    )
    # Mid-word: no left boundary
    for ch in "xcat":
        assert engine.handle_char(ch) is False
    engine.clear_buffer()
    # Word boundary via space
    engine.handle_char(" ")
    for ch in "cat":
        expanded = engine.handle_char(ch)
    assert expanded is True


def test_buffer_clears_on_frontmost_app_change(monkeypatch: pytest.MonkeyPatch):
    from expando.app_context import AppContext

    engine = _engine_with_matches([{"trigger": ":ab", "replace": "OK"}])
    contexts = [
        AppContext(name="Safari", bundle_id="com.apple.Safari"),
        AppContext(name="Notes", bundle_id="com.apple.Notes"),
    ]
    idx = {"i": 0}

    def fake_frontmost():
        return contexts[idx["i"]]

    monkeypatch.setattr("expando.engine.get_frontmost_context", fake_frontmost)
    engine.handle_char(":")
    engine.handle_char("a")
    assert ":" in engine._buffer or engine._buffer.endswith("a")
    idx["i"] = 1
    engine.handle_char("b")
    # After app switch, buffer should not still hold ":a" + "b" as ":ab"
    # Partial trigger from Safari must have been cleared.
    assert engine.injector.inject.call_count == 0


def test_buffer_clears_when_app_blacklisted(monkeypatch: pytest.MonkeyPatch):
    from expando.app_context import AppContext
    from expando.config import AppConfig, ConfigBundle, normalize_match

    app = AppConfig()
    app.app_blacklist = ["1Password"]
    bundle = ConfigBundle(
        app=app,
        matches=[normalize_match({"trigger": ":x", "replace": "Y"})],
    )
    engine = ExpansionEngine(bundle, MagicMock())
    monkeypatch.setattr(
        "expando.engine.get_frontmost_context",
        lambda: AppContext(name="1Password", bundle_id="com.1password"),
    )
    engine._buffer = ":partial"
    assert engine.handle_char("x") is False
    assert engine._buffer == ""


def test_inject_mute_depth_uses_refcount_not_force_assign(monkeypatch: pytest.MonkeyPatch):
    import inspect

    from expando.listener import KeyboardService
    import expando.listener as listener_mod

    # Guard against reintroducing `self._injecting_depth = 1` force-reset.
    source = inspect.getsource(KeyboardService._run_expansion)
    assert "_injecting_depth = 1" not in source
    assert "_injecting_depth =" not in source.replace("self._injecting_depth = max", "")

    engine = MagicMock()
    engine.enabled = True
    engine.config.app.clipboard_threshold = 9999
    engine._base_bundle.app.toggle_key = "OFF"
    engine._base_bundle.app.auto_restart = False
    engine._base_bundle.matches = []
    service = KeyboardService(config_dir=MagicMock(), engine=engine)

    timers: list = []

    class FakeTimer:
        def __init__(self, delay, fn):
            self.delay = delay
            self.fn = fn
            self.daemon = False

        def start(self):
            timers.append(self)

        def is_alive(self):
            return True

    monkeypatch.setattr(listener_mod.threading, "Timer", FakeTimer)

    service._run_expansion(lambda: True)
    assert service._injecting_depth == 1
    assert len(timers) == 1
    service._finish_injecting()
    assert service._injecting_depth == 0


def test_xcode_not_terminal_via_code_token():
    assert not app_name_matches_terminal_candidate("Xcode", "Code")
    assert app_name_matches_terminal_candidate("Code", "Code")
    assert not is_terminal_app("Xcode")

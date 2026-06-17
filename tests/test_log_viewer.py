from __future__ import annotations

import logging

from expando.log_viewer import print_log_tail, resolve_log_level


def test_resolve_log_level_defaults_to_info():
    assert resolve_log_level(None) == logging.INFO


def test_resolve_log_level_accepts_debug(monkeypatch):
    monkeypatch.delenv("EXPANDO_LOG_LEVEL", raising=False)
    assert resolve_log_level("debug") == logging.DEBUG


def test_print_log_tail_shows_last_lines(tmp_path, capsys):
    log_path = tmp_path / "expando.log"
    log_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
    print_log_tail(log_path, lines=2, follow=False)
    output = capsys.readouterr().out
    assert "line2" in output
    assert "line3" in output
    assert "line1" not in output
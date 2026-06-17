from __future__ import annotations

import json
from pathlib import Path

from expando.crash_reporting import (
    format_crash_report,
    install_crash_handlers,
    list_crash_reports,
    recent_crash_count,
    write_crash_report,
)


def test_write_and_list_crash_report(tmp_path: Path):
    try:
        raise ValueError("boom")
    except ValueError as exc:
        path = write_crash_report(
            tmp_path,
            type(exc),
            exc,
            exc.__traceback__,
            source="test",
        )

    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["exception_type"] == "ValueError"
    assert payload["source"] == "test"
    assert "boom" in payload["message"]

    reports = list_crash_reports(tmp_path)
    assert len(reports) == 1
    assert reports[0].exception_type == "ValueError"
    assert "boom" in format_crash_report(path)


def test_recent_crash_count(tmp_path: Path):
    write_crash_report(tmp_path, RuntimeError, RuntimeError("x"), None, source="test")
    assert recent_crash_count(tmp_path) == 1


def test_install_crash_handlers_idempotent(tmp_path: Path):
    install_crash_handlers(tmp_path)
    install_crash_handlers(tmp_path)
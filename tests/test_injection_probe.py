from __future__ import annotations

import subprocess
from pathlib import Path

from expando.injection_probe import run_injection_probe


def test_injection_probe_skips_non_darwin(tmp_path: Path):
    result = run_injection_probe(tmp_path / "expando", system="Linux")

    assert result["skipped"] is True
    assert result["method"] == "skip"
    assert result["ok"] is None


def test_injection_probe_skips_without_accessibility(tmp_path: Path):
    result = run_injection_probe(
        tmp_path / "expando",
        system="Darwin",
        accessibility=False,
    )

    assert result["skipped"] is True
    assert result["ok"] is False
    assert "accessibility" in result["detail"]


def test_injection_probe_uses_clipboard_path(tmp_path: Path):
    result = run_injection_probe(
        tmp_path / "expando",
        system="Darwin",
        accessibility=True,
        clipboard_ready=True,
    )

    assert result["skipped"] is False
    assert result["method"] == "clipboard"
    assert result["ok"] is True


def test_injection_probe_falls_back_to_system_events(tmp_path: Path, monkeypatch):
    def fake_runner(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="true\n", stderr="")

    monkeypatch.setattr(
        "expando.injection_probe.clipboard_injection_ready",
        lambda: None,
    )
    result = run_injection_probe(
        tmp_path / "expando",
        system="Darwin",
        accessibility=True,
        clipboard_ready=None,
        runner=fake_runner,
    )

    assert result["skipped"] is False
    assert result["method"] == "system_events"
    assert result["ok"] is True
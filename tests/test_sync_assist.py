from pathlib import Path

import pytest

from expando.sync_assist import format_sync_report, init_git_sync, inspect_sync_status


def test_inspect_local_sync_status(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir()
    status = inspect_sync_status(config_dir)
    assert status.mode == "local"
    assert not status.git_repo
    report = format_sync_report(status)
    assert "config/" in report or "config" in report


def test_init_git_sync(tmp_path: Path):
    config_dir = tmp_path / "expando"
    messages = init_git_sync(config_dir, commit=True)
    assert (config_dir / ".git").exists()
    assert (config_dir / ".gitignore").exists()
    assert any("git" in line.lower() for line in messages)


def test_init_git_requires_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("expando.sync_assist.shutil.which", lambda _name: None)
    with pytest.raises(RuntimeError, match="git"):
        init_git_sync(tmp_path / "expando")
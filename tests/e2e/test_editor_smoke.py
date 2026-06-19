from __future__ import annotations

import platform

import pytest

from expando.snippet_editor_data import create_snippet_entry, entries_for_editor

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only"),
]


def test_editor_data_roundtrip(e2e_config_dir):
    entry = create_snippet_entry(
        e2e_config_dir,
        ":editor-smoke",
        "editor smoke text",
    )
    entries = entries_for_editor(e2e_config_dir)
    ids = {item["id"] for item in entries}
    assert entry.entry_id in ids
    match = next(item for item in entries if item["id"] == entry.entry_id)
    assert match["trigger"] == ":editor-smoke"
    assert match["replace"] == "editor smoke text"


@pytest.mark.integration
def test_editor_cli_opens_without_error(require_full_e2e, e2e_config_dir, monkeypatch):
    from click.testing import CliRunner

    from expando.cli import main

    monkeypatch.setattr(
        "expando.snippet_editor.open_snippet_editor",
        lambda _config_dir: None,
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--config-dir", str(e2e_config_dir), "editor"],
    )
    assert result.exit_code == 0, result.output
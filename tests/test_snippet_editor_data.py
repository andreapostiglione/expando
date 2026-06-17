from pathlib import Path

import pytest

from expando.snippet_editor_data import (
    create_snippet_entry,
    delete_snippet_entry,
    entries_for_editor,
    list_snippet_entries,
    update_snippet_entry,
)


def _setup_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "match" / "dev.yml").write_text(
        "matches:\n  - trigger: ':old'\n    replace: 'Old text'\n",
        encoding="utf-8",
    )
    return config_dir


def test_list_and_update_snippet_entry(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    entries = list_snippet_entries(config_dir)
    assert len(entries) == 1
    entry = entries[0]

    updated = update_snippet_entry(
        config_dir,
        entry.entry_id,
        trigger=":new",
        replace="New text",
        if_app=["Terminal"],
    )
    assert updated.match.triggers == [":new"]
    assert updated.match.replace == "New text"
    assert updated.match.if_app == ["Terminal"]


def test_create_and_delete_snippet_entry(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    created = create_snippet_entry(
        config_dir,
        ":extra",
        "Extra text",
        target_file="dev.yml",
    )
    assert created.match.triggers == [":extra"]
    assert len(list_snippet_entries(config_dir)) == 2

    delete_snippet_entry(config_dir, created.entry_id)
    assert len(list_snippet_entries(config_dir)) == 1


def test_create_rejects_duplicate_trigger(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        create_snippet_entry(config_dir, ":old", "Duplicate")


def test_entries_for_editor_marks_packages_readonly(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    package_dir = config_dir / "match" / "packages" / "core"
    package_dir.mkdir(parents=True)
    (package_dir / "snippets.yml").write_text(
        "matches:\n  - trigger: ':pkg'\n    replace: 'from package'\n",
        encoding="utf-8",
    )
    rows = entries_for_editor(config_dir)
    package_rows = [row for row in rows if row["source_file"] == "packages"]
    assert package_rows
    assert package_rows[0]["editable"] == "0"
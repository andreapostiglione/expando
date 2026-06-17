from pathlib import Path

import pytest

from expando.snippet_editor_data import (
    create_snippet_entry,
    delete_snippet_entry,
    entries_for_editor,
    format_form_for_editor,
    format_vars_for_editor,
    list_snippet_entries,
    parse_form_from_editor,
    parse_vars_from_editor,
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


def test_form_and_vars_round_trip(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    created = create_snippet_entry(
        config_dir,
        ":email",
        "Ciao {{name}},\n{{body}}",
        form=parse_form_from_editor("name|Nome|\nbody|Messaggio|"),
        variables=parse_vars_from_editor(
            "- name: ts\n  type: date\n  params:\n    format: '%H:%M'\n"
        ),
    )
    assert created.match.form
    assert created.match.vars
    rows = entries_for_editor(config_dir)
    row = next(item for item in rows if item["trigger"] == ":email")
    assert "name|Nome|" in row["form"]
    assert "type: date" in row["vars"]

    entry = list_snippet_entries(config_dir)[-1]
    updated = update_snippet_entry(
        config_dir,
        entry.entry_id,
        trigger=":email",
        replace="Buongiorno {{name}}",
        form=parse_form_from_editor("name|Nome destinatario|"),
        variables=[],
    )
    assert len(updated.match.form) == 1
    assert not updated.match.vars


def test_parse_form_rejects_invalid_line():
    with pytest.raises(ValueError, match="nome\\|etichetta"):
        parse_form_from_editor("solo-un-campo")


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
from pathlib import Path

from expando.espanso_migrate import migrate_espanso_config


def test_migrate_espanso_creates_backup(tmp_path: Path):
    source = tmp_path / "espanso"
    (source / "config").mkdir(parents=True)
    (source / "match").mkdir(parents=True)
    (source / "config" / "default.yml").write_text(
        "toggle_key: ALT\nsearch_shortcut: CMD+SPACE\n",
        encoding="utf-8",
    )
    (source / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':hi'\n    replace: 'Hello'\n",
        encoding="utf-8",
    )

    destination = tmp_path / "expando"
    (destination / "config").mkdir(parents=True)
    (destination / "match").mkdir(parents=True)
    (destination / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")

    report = migrate_espanso_config(destination, source=source, force=True)
    assert report.backup_path.exists()
    assert report.import_report.matches_imported >= 1
    assert any(path.endswith(".yml") for path in report.import_report.match_files)
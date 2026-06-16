from pathlib import Path

from expando.backup import backup_config, restore_config


def test_backup_and_restore(tmp_path: Path):
    config_dir = tmp_path / "expando"
    match_dir = config_dir / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "base.yml").write_text("matches: []\n", encoding="utf-8")

    archive = backup_config(config_dir)
    assert archive.exists()

    (match_dir / "base.yml").write_text("matches:\n  - trigger: ':x'\n    replace: 'y'\n", encoding="utf-8")
    restore_config(config_dir, archive)
    assert "matches" in (match_dir / "base.yml").read_text(encoding="utf-8")
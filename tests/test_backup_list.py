from __future__ import annotations

from expando.backup import backups_for_picker, list_backup_archives, list_restore_candidates


def test_list_backup_archives_finds_parent_and_backups_dir(tmp_path) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    parent_backup = tmp_path / "expando-backup-20260101-120000.tar.gz"
    parent_backup.write_bytes(b"parent")
    auto_dir = config_dir / "backups"
    auto_dir.mkdir()
    auto_backup = auto_dir / "auto-backup-20260102-120000.tar.gz"
    auto_backup.write_bytes(b"auto")

    found = list_backup_archives(config_dir)
    assert found == [auto_backup, parent_backup]


def test_list_restore_candidates_excludes_pre_restore_snapshot(tmp_path) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    manual = tmp_path / "expando-backup-20260101-120000.tar.gz"
    manual.write_bytes(b"manual")
    pre_restore = tmp_path / "expando-pre-restore-backup.tar.gz"
    pre_restore.write_bytes(b"safety")

    assert list_restore_candidates(config_dir) == [manual]


def test_backups_for_picker_labels_manual_backups(tmp_path) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    manual = tmp_path / "expando-backup-20260619-151658.tar.gz"
    manual.write_bytes(b"manual")

    items = backups_for_picker(config_dir)
    assert len(items) == 1
    assert items[0]["label"] == "19/06/2026 15:16"
    assert items[0]["archive_path"] == str(manual.resolve())
from __future__ import annotations

from pathlib import Path

from expando.backup import backup_label


def test_backup_label_formats_timestamp() -> None:
    path = Path("/tmp/expando-backup-20260619-151658.tar.gz")
    assert backup_label(path) == "19/06/2026 15:16"


def test_backup_label_falls_back_to_filename() -> None:
    path = Path("/tmp/custom-backup.tar.gz")
    assert backup_label(path) == "custom-backup.tar.gz"
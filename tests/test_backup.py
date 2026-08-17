import tarfile
from pathlib import Path

import pytest

from expando.backup import _safe_extract, backup_config, restore_config


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


def test_safe_extract_rejects_tar_slip(tmp_path: Path):
    archive_path = tmp_path / "evil.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        info = tarfile.TarInfo(name="../escape.txt")
        data = b"pwned"
        info.size = len(data)
        import io

        archive.addfile(info, io.BytesIO(data))

    dest = tmp_path / "out"
    dest.mkdir()
    with tarfile.open(archive_path, "r:gz") as archive:
        with pytest.raises(ValueError, match="Unsafe path"):
            _safe_extract(archive, dest)
    assert not (tmp_path / "escape.txt").exists()
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from expando.backup import backup_config, restore_config


def test_restore_rolls_back_on_copy_failure(tmp_path: Path) -> None:
    config_dir = tmp_path / "expando"
    match_dir = config_dir / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "base.yml").write_text("matches: []\n", encoding="utf-8")

    archive = backup_config(config_dir)
    original = (match_dir / "base.yml").read_text(encoding="utf-8")

    with patch("expando.backup.shutil.move", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            restore_config(config_dir, archive)

    assert config_dir.exists()
    assert (match_dir / "base.yml").read_text(encoding="utf-8") == original
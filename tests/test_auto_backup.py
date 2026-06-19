from __future__ import annotations

from pathlib import Path

from expando.auto_backup import (
    backup_before_mutation,
    backup_stale_warning,
    create_auto_backup,
    latest_backup_age_days,
)


def _write_config(config_dir: Path, *, auto_backup: str = "daily") -> None:
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir()
    (config_dir / "config" / "default.yml").write_text(
        "\n".join(
            [
                f"auto_backup: {auto_backup}",
                "auto_backup_retention: 7",
                "auto_backup_stale_days: 3",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (config_dir / "match" / "base.yml").write_text("matches: []\n", encoding="utf-8")


def test_create_auto_backup_daily(tmp_path: Path):
    config_dir = tmp_path / "expando"
    _write_config(config_dir)
    archive = create_auto_backup(config_dir)
    assert archive is not None
    assert archive.exists()
    second = create_auto_backup(config_dir)
    assert second is None


def test_backup_before_mutation(tmp_path: Path):
    config_dir = tmp_path / "expando"
    _write_config(config_dir, auto_backup="off")
    archive = backup_before_mutation(config_dir, "restore")
    assert archive.exists()
    assert "pre-restore-" in archive.name


def test_backup_stale_warning_when_missing(tmp_path: Path):
    config_dir = tmp_path / "expando"
    _write_config(config_dir)
    warning = backup_stale_warning(config_dir)
    assert warning is not None
    assert "backup" in warning.lower()


def test_latest_backup_age_days_after_backup(tmp_path: Path):
    config_dir = tmp_path / "expando"
    _write_config(config_dir)
    create_auto_backup(config_dir)
    age = latest_backup_age_days(config_dir)
    assert age is not None
    assert age < 1.0
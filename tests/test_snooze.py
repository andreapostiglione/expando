from __future__ import annotations

from pathlib import Path

from expando.snooze import (
    clear_snooze,
    format_snooze_remaining,
    set_snooze,
    snooze_active,
    snooze_until,
)


def test_snooze_lifecycle(tmp_path: Path) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    assert snooze_active(config_dir) is False
    set_snooze(config_dir, minutes=30)
    assert snooze_active(config_dir) is True
    assert snooze_until(config_dir) is not None
    assert format_snooze_remaining(config_dir)
    clear_snooze(config_dir)
    assert snooze_active(config_dir) is False


def test_snooze_expires(tmp_path: Path) -> None:
    from expando.snooze import snooze_file

    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    snooze_file(config_dir).write_text(
        '{"version": 1, "until": "2000-01-01T00:00:00+00:00"}',
        encoding="utf-8",
    )
    assert snooze_active(config_dir) is False
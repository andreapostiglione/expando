from pathlib import Path

from expando.expansion_stats import (
    is_tracking_enabled,
    load_stats,
    record_expansion,
    set_tracking_enabled,
)
from expando.paths import config_file


def _setup_config(tmp_path: Path, *, track: bool = True) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        f"track_expansions: {'true' if track else 'false'}\n",
        encoding="utf-8",
    )
    return config_dir


def test_record_expansion_when_enabled(tmp_path: Path):
    config_dir = _setup_config(tmp_path)
    set_tracking_enabled(config_dir, True)
    assert is_tracking_enabled(config_dir)
    record_expansion(config_dir, ":hi")
    record_expansion(config_dir, ":hi")
    stats = load_stats(config_dir)
    assert stats.total == 2
    assert stats.by_trigger[":hi"] == 2


def test_record_expansion_skipped_when_disabled(tmp_path: Path):
    config_dir = _setup_config(tmp_path, track=False)
    set_tracking_enabled(config_dir, True)
    record_expansion(config_dir, ":hi")
    stats = load_stats(config_dir)
    assert stats.total == 0
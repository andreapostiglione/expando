from pathlib import Path
from unittest.mock import MagicMock

from expando.config import AppConfig, ConfigBundle
from expando.engine import ExpansionEngine
from expando.snooze import set_snooze


def _bundle() -> ConfigBundle:
    return ConfigBundle(app=AppConfig(), matches=[])


def test_engine_respects_snooze(tmp_path: Path) -> None:
    config_dir = tmp_path / "expando"
    config_dir.mkdir()
    injector = MagicMock()
    engine = ExpansionEngine(_bundle(), injector, config_dir=config_dir)
    set_snooze(config_dir, minutes=30)
    assert engine._expansion_active() is False
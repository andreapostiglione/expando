from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from expando.config import load_config
from expando.config_reload_gate import (
    ConfigReloadError,
    last_good_dir,
    rollback_to_last_good,
    safe_reload_config,
    save_last_good_config,
    validate_config_for_reload,
    wait_for_stable_config,
)


def _setup_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text("toggle_key: ALT\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':ok'\n    replace: 'yes'\n",
        encoding="utf-8",
    )
    return config_dir


def test_validate_config_for_reload_ok(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    bundle = validate_config_for_reload(config_dir)
    assert len(bundle.matches) == 1


def test_save_and_rollback_last_good_config(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    bundle = load_config(config_dir)
    save_last_good_config(config_dir, bundle)

    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':new'\n    replace: 'changed'\n",
        encoding="utf-8",
    )
    assert load_config(config_dir).matches[0].triggers == [":new"]

    assert rollback_to_last_good(config_dir) is True
    assert load_config(config_dir).matches[0].triggers == [":ok"]
    assert last_good_dir(config_dir).exists()


def test_safe_reload_config_rolls_back_on_invalid_yaml(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    engine = MagicMock()
    bundle = load_config(config_dir)
    save_last_good_config(config_dir, bundle)

    (config_dir / "match" / "base.yml").write_text(
        "matches:\n"
        "  - trigger: ':dup'\n    replace: 'one'\n"
        "  - trigger: ':dup'\n    replace: 'two'\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigReloadError) as exc_info:
        safe_reload_config(config_dir, engine)

    assert exc_info.value.rolled_back is True
    engine.reload.assert_called()
    assert load_config(config_dir).matches[0].triggers == [":ok"]


def test_wait_for_stable_config_waits_for_changing_file(tmp_path: Path, monkeypatch):
    config_dir = _setup_config_dir(tmp_path)
    target = config_dir / "match" / "base.yml"
    calls = {"sleeps": 0}

    def fake_sleep(seconds: float) -> None:
        calls["sleeps"] += 1
        if calls["sleeps"] == 1:
            target.write_text(
                "matches:\n  - trigger: ':mid'\n    replace: 'partial'\n",
                encoding="utf-8",
            )

    monkeypatch.setattr("expando.config_reload_gate.time.sleep", fake_sleep)
    wait_for_stable_config(
        config_dir,
        settle_seconds=0.01,
        poll_interval=0.01,
        timeout_seconds=0.2,
    )
    assert calls["sleeps"] >= 2


def test_safe_reload_config_applies_valid_changes(tmp_path: Path):
    config_dir = _setup_config_dir(tmp_path)
    engine = MagicMock()
    bundle = load_config(config_dir)
    save_last_good_config(config_dir, bundle)

    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':new'\n    replace: 'changed'\n",
        encoding="utf-8",
    )

    result = safe_reload_config(config_dir, engine)

    engine.reload.assert_called_once()
    assert result.matches[0].triggers == [":new"]
    assert load_config(config_dir).matches[0].triggers == [":new"]

    (config_dir / "match" / "base.yml").write_text(
        "matches:\n  - trigger: ':broken'\n    replace: 'bad'\n",
        encoding="utf-8",
    )
    assert rollback_to_last_good(config_dir) is True
    assert load_config(config_dir).matches[0].triggers == [":new"]
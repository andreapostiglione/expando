from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from expando.hub import (
    hub_outdated_packages,
    hub_update_count,
    install_hub_package,
    record_hub_install,
    upgrade_hub_package,
)


def test_hub_outdated_detects_version_mismatch(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    record_hub_install(config_dir, "typing-it", version="0.9.0")

    with patch("expando.hub._remote_package_version", return_value="1.0.0"):
        outdated = hub_outdated_packages(config_dir)

    assert len(outdated) == 1
    assert outdated[0]["package_id"] == "typing-it"
    assert outdated[0]["local_version"] == "0.9.0"
    assert outdated[0]["remote_version"] == "1.0.0"
    assert hub_update_count(config_dir) == 1


def test_upgrade_hub_package_reinstalls(tmp_path: Path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    pkg_dir = config_dir / "match" / "packages" / "typing-it"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "snippets.yml").write_text("matches:\n  - trigger: ':old'\n    replace: old\n")

    record_hub_install(config_dir, "typing-it", version="0.9.0")

    def fake_install(config_dir: Path, package_id: str, *, force: bool = False) -> Path:
        destination = config_dir / "match" / "packages" / package_id
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "snippets.yml").write_text(
            "matches:\n  - trigger: ':new'\n    replace: new\n",
            encoding="utf-8",
        )
        record_hub_install(config_dir, package_id, version="1.0.0")
        return destination

    monkeypatch.setattr("expando.hub.install_hub_package", fake_install)
    monkeypatch.setattr("expando.hub.uninstall_hub_package", lambda *_args, **_kwargs: True)

    destination = upgrade_hub_package(config_dir, "typing-it")
    assert "new" in destination.joinpath("snippets.yml").read_text()
    manifest = json.loads((config_dir / "hub-installed.json").read_text())
    assert manifest["packages"]["typing-it"]["version"] == "1.0.0"
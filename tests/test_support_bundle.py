from __future__ import annotations

import json
import tarfile
from pathlib import Path

from expando.support_bundle import create_support_bundle, redact_config_tree


def test_redact_config_tree_masks_secrets(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "api_key: super-secret-token\nenabled: true\n",
        encoding="utf-8",
    )
    destination = tmp_path / "redacted"
    redact_config_tree(config_dir, destination)
    text = (destination / "config" / "default.yml").read_text(encoding="utf-8")
    assert "super-secret-token" not in text
    assert "***REDACTED***" in text
    assert "enabled: true" in text


def test_create_support_bundle(tmp_path: Path):
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir()
    (config_dir / "config" / "default.yml").write_text("enabled: true\n", encoding="utf-8")
    (config_dir / "match" / "base.yml").write_text("matches: []\n", encoding="utf-8")
    (config_dir / "expando.log").write_text(
        "2026-06-19 10:00:00 [INFO] expando.listener: started\n",
        encoding="utf-8",
    )

    archive = tmp_path / "bundle.tar.gz"
    create_support_bundle(config_dir, archive)
    assert archive.exists()

    with tarfile.open(archive, "r:gz") as bundle:
        names = bundle.getnames()
        assert any(name.endswith("doctor.json") for name in names)
        assert any(name.endswith("health.json") for name in names)
        assert any(name.endswith("manifest.json") for name in names)

        doctor_member = next(name for name in names if name.endswith("doctor.json"))
        extracted = bundle.extractfile(doctor_member)
        assert extracted is not None
        payload = json.loads(extracted.read().decode("utf-8"))
        assert "doctor" in payload
from pathlib import Path

import pytest
import yaml

from expando.match_store import duplicate_snippet, export_snippet_yaml


def _setup(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    match_dir = config_dir / "match"
    match_dir.mkdir(parents=True)
    (match_dir / "dev.yml").write_text(
        "matches:\n"
        "  - trigger: ':sig'\n"
        "    form:\n"
        "      - name: name\n"
        "        label: Nome\n"
        "    replace: 'Ciao {{name}}'\n",
        encoding="utf-8",
    )
    return config_dir


def test_export_snippet_yaml(tmp_path: Path):
    config_dir = _setup(tmp_path)
    exported = export_snippet_yaml(config_dir, ":sig")
    data = yaml.safe_load(exported)
    assert data["matches"][0]["trigger"] == ":sig"
    assert data["matches"][0]["form"]


def test_duplicate_snippet(tmp_path: Path):
    config_dir = _setup(tmp_path)
    path = duplicate_snippet(config_dir, ":sig", ":sig2")
    assert path.name == "dev.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    triggers = [item["trigger"] for item in data["matches"]]
    assert ":sig" in triggers
    assert ":sig2" in triggers


def test_export_missing_trigger(tmp_path: Path):
    config_dir = _setup(tmp_path)
    with pytest.raises(ValueError, match="not found"):
        export_snippet_yaml(config_dir, ":missing")
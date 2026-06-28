from __future__ import annotations

from pathlib import Path

from expando import snippet_editor


def _setup_config(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "match" / "dev.yml").write_text(
        "matches:\n  - trigger: ':old'\n    replace: 'Old text'\n",
        encoding="utf-8",
    )
    return config_dir


def test_open_snippet_editor_forwards_initial_new(tmp_path: Path, monkeypatch) -> None:
    config_dir = _setup_config(tmp_path)
    captured: dict[str, object] = {}

    def fake_run_snippet_editor(items, **kwargs):
        captured["items"] = items
        captured.update(kwargs)
        return {"saved": "1"}

    monkeypatch.setattr(snippet_editor, "run_snippet_editor", fake_run_snippet_editor)

    result = snippet_editor.open_snippet_editor(config_dir, initial_new=True)

    assert result == {"saved": "1"}
    assert captured["initial_new"] is True
    assert captured["match_files"] == ["dev.yml"]

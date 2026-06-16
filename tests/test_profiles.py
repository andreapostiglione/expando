from pathlib import Path

from expando.config import AppConfig
from expando.profiles import resolve_app_config


def test_resolve_terminal_profile(tmp_path: Path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "default.yml").write_text("search_shortcut: CMD+SHIFT+E\n", encoding="utf-8")
    (config_dir / "terminal.yml").write_text(
        "filter:\n  app_names:\n    - Terminal\nsearch_shortcut: CMD+SHIFT+T\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("expando.profiles.get_frontmost_app", lambda: "Terminal")
    app = resolve_app_config(tmp_path, AppConfig())
    assert app.search_shortcut == "CMD+SHIFT+T"
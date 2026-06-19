from __future__ import annotations

from pathlib import Path

from expando.plugins import PluginManager
from expando.render_context import RenderContext


def test_plugin_allowlist_blocks_unlisted(tmp_path: Path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "allowed.py").write_text(
        "def transform_replacement(text, context):\n    return text + 'A'\n",
        encoding="utf-8",
    )
    (plugins / "blocked.py").write_text(
        "def transform_replacement(text, context):\n    return text + 'B'\n",
        encoding="utf-8",
    )

    manager = PluginManager(tmp_path, allowlist=["allowed.py"])
    assert manager.list_plugins() == ["allowed.py"]
    assert manager.skipped_plugins() == ["blocked.py"]
    ctx = RenderContext(trigger=":x")
    assert manager.transform_replacement("hi", ctx) == "hiA"
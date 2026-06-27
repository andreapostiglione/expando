from __future__ import annotations

from pathlib import Path

import pytest

from expando.plugins import PluginManager, resolve_plugin_script, run_plugin_script
from expando.render_context import RenderContext


def test_plugin_manager_loads_example(tmp_path: Path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "demo.py").write_text(
        "def transform_replacement(text, context):\n"
        "    return text + '!'\n",
        encoding="utf-8",
    )
    manager = PluginManager(tmp_path)
    assert manager.list_plugins() == ["demo.py"]
    ctx = RenderContext(trigger=":x")
    assert manager.transform_replacement("hi", ctx) == "hi!"


def test_script_variable_run(tmp_path: Path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "tag.py").write_text(
        "def run(context):\n"
        "    return context.get('trigger', '')\n",
        encoding="utf-8",
    )
    path = resolve_plugin_script(tmp_path, "tag.py")
    result = run_plugin_script(path, RenderContext(trigger=":hello"))
    assert result == ":hello"


def test_script_path_traversal_blocked(tmp_path: Path):
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    with pytest.raises(RuntimeError, match="inside plugins"):
        resolve_plugin_script(tmp_path, "../outside.py")


def test_script_path_prefix_sibling_traversal_blocked(tmp_path: Path):
    config_dir = tmp_path / "expando"
    plugins = config_dir / "plugins"
    plugins.mkdir(parents=True)
    sibling = config_dir / "plugins_evil"
    sibling.mkdir()
    (sibling / "leak.py").write_text("def run(context):\n    return 'leak'\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="inside plugins"):
        resolve_plugin_script(config_dir, "../plugins_evil/leak.py")

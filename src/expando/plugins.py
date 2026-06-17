from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable

from .paths import plugins_dir
from .render_context import RenderContext

logger = logging.getLogger(__name__)

HookFn = Callable[..., Any]


class PluginManager:
    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self._before_expand: list[HookFn] = []
        self._after_expand: list[HookFn] = []
        self._transform_replacement: list[HookFn] = []
        self._loaded_files: list[str] = []
        self.reload()

    def reload(self) -> None:
        self._before_expand = []
        self._after_expand = []
        self._transform_replacement = []
        self._loaded_files = []

        directory = plugins_dir(self.config_dir)
        directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            try:
                module = _load_module(path)
            except Exception:
                logger.exception("Failed to load plugin %s", path.name)
                continue
            self._loaded_files.append(path.name)
            self._register_hook(module, "before_expand", self._before_expand)
            self._register_hook(module, "after_expand", self._after_expand)
            self._register_hook(module, "transform_replacement", self._transform_replacement)

    def list_plugins(self) -> list[str]:
        return list(self._loaded_files)

    def run_before_expand(self, context: RenderContext) -> None:
        payload = context.as_dict()
        for hook in self._before_expand:
            try:
                hook(payload)
            except Exception:
                logger.exception("before_expand hook failed")

    def run_after_expand(self, context: RenderContext, replacement: str) -> None:
        payload = dict(context.as_dict())
        payload["replacement"] = replacement
        for hook in self._after_expand:
            try:
                hook(payload)
            except Exception:
                logger.exception("after_expand hook failed")

    def transform_replacement(self, text: str, context: RenderContext) -> str:
        payload = context.as_dict()
        result = text
        for hook in self._transform_replacement:
            try:
                transformed = hook(result, payload)
                if transformed is not None:
                    result = str(transformed)
            except Exception:
                logger.exception("transform_replacement hook failed")
        return result

    @staticmethod
    def _register_hook(module: Any, name: str, bucket: list[HookFn]) -> None:
        fn = getattr(module, name, None)
        if callable(fn):
            bucket.append(fn)


def _load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(f"expando_plugin_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_plugin_script(config_dir: Path, script_path: str) -> Path:
    base = plugins_dir(config_dir).resolve()
    candidate = (base / script_path).resolve()
    if not str(candidate).startswith(str(base)):
        raise RuntimeError(f"Script path must stay inside plugins/: {script_path}")
    if candidate.suffix != ".py":
        raise RuntimeError(f"Script must be a .py file: {script_path}")
    if not candidate.exists():
        raise RuntimeError(f"Script not found: {script_path}")
    return candidate


def run_plugin_script(path: Path, context: RenderContext) -> str:
    module = _load_module(path)
    runner = getattr(module, "run", None)
    if not callable(runner):
        raise RuntimeError(f"Script {path.name} must define run(context) -> str")
    result = runner(context.as_dict())
    return "" if result is None else str(result)
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ui_main_thread import call_on_main_thread
from .ui_state import set_ui_active

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UiBridgeError(Exception):
    message: str
    detail: str = ""

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


def _headless() -> bool:
    return os.environ.get("EXPANDO_HEADLESS", "").lower() in {"1", "true", "yes"}


def _prefer_inprocess() -> bool:
    if _headless():
        return False
    if os.environ.get("EXPANDO_UI_SUBPROCESS", "").lower() in {"1", "true", "yes"}:
        return False
    if os.environ.get("EXPANDO_UI_INPROCESS", "").lower() in {"1", "true", "yes"}:
        return True
    return sys.platform == "darwin"


def _use_appkit() -> bool:
    """Return True if we should prefer native AppKit UI over Tk fallback.
    AC4 this-round: centralized here; ui_native.py and snippet_editor_ui.py now import this.
    Tk kept ONLY as minimal fallback (EXPANDO_UI=tk / non-Darwin / no AppKit).
    """
    if platform.system() != "Darwin":
        return False
    if os.environ.get("EXPANDO_UI", "").lower() == "tk":
        return False
    try:
        import AppKit  # noqa: F401
        return True
    except ImportError:
        return False


def _ui_subprocess_argv(command: str) -> list[str]:
    override = os.environ.get("EXPANDO_UI_PYTHON", "").strip()
    if override:
        return [override, "-m", "expando.ui_cli", command]

    from .runtime_info import detect_runtime
    from .paths import find_expando_app_bundle

    runtime = detect_runtime()
    if runtime.mode == "app":
        app_root = Path(runtime.grant_hint)
        launcher = app_root / "Contents" / "MacOS" / "expando"
        if launcher.is_file():
            return [str(launcher), "-m", "expando.ui_cli", command]

        # try embedded python in bundle
        emb = app_root / "Contents" / "Resources" / "python" / "bin" / "python3"
        if emb.is_file():
            return [str(emb), "-m", "expando.ui_cli", command]

    # robust fallback using find
    app = find_expando_app_bundle()
    if app:
        launcher = app / "Contents" / "MacOS" / "expando"
        if launcher.is_file():
            return [str(launcher), "-m", "expando.ui_cli", command]
        emb = app / "Contents" / "Resources" / "python" / "bin" / "python3"
        if emb.is_file():
            return [str(emb), "-m", "expando.ui_cli", command]

    return [sys.executable, "-m", "expando.ui_cli", command]


def _run_ui_inprocess_body(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    if command == "search":
        from .ui_native import run_search_picker

        return run_search_picker(payload.get("items", []))
    if command == "form":
        from .ui_native import run_form_dialog

        return run_form_dialog(payload.get("fields", []))
    if command == "editor":
        from .snippet_editor import open_snippet_editor

        config_dir = payload.get("config_dir")
        if not config_dir:
            raise UiBridgeError("Missing config_dir for editor UI")
        return open_snippet_editor(Path(config_dir))
    raise UiBridgeError(f"Unknown UI command: {command}")


def _run_ui_inprocess(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    set_ui_active(True)
    try:
        return call_on_main_thread(
            lambda: _run_ui_inprocess_body(command, payload),
            wait=True,
        )
    except UiBridgeError:
        raise
    except Exception as exc:
        raise UiBridgeError("In-process UI failed", str(exc)) from exc
    finally:
        set_ui_active(False)


def _run_ui_subprocess(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    argv = _ui_subprocess_argv(command)
    set_ui_active(True)
    try:
        result = subprocess.run(
            argv,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise UiBridgeError(
                f"UI subprocess {command} failed (code {result.returncode})",
                stderr[-2000:],
            )
        output = result.stdout.strip()
        if not output:
            return None
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise UiBridgeError(
                f"UI subprocess {command} returned invalid JSON",
                output[-500:],
            ) from exc
        return data or None
    except subprocess.TimeoutExpired as exc:
        raise UiBridgeError(f"UI subprocess {command} timed out") from exc
    finally:
        set_ui_active(False)


def run_ui_command(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    if _headless():
        return None
    if _prefer_inprocess():
        return _run_ui_inprocess(command, payload)
    return _run_ui_subprocess(command, payload)


def show_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    try:
        return run_ui_command("search", {"items": items})
    except UiBridgeError as exc:
        logger.warning("%s", exc)
        return None


def show_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    try:
        return run_ui_command("form", {"fields": fields})
    except UiBridgeError as exc:
        logger.warning("%s", exc)
        return None


def show_snippet_editor(config_dir: str) -> dict[str, str] | None:
    try:
        return run_ui_command("editor", {"config_dir": config_dir})
    except UiBridgeError as exc:
        logger.warning("%s", exc)
        return None
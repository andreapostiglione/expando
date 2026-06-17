from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from typing import Any

from .ui_state import set_ui_active

logger = logging.getLogger(__name__)


def _headless() -> bool:
    return os.environ.get("EXPANDO_HEADLESS", "").lower() in {"1", "true", "yes"}


def _run_ui_subprocess(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    if _headless():
        return None

    set_ui_active(True)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "expando.ui_cli", command],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            logger.warning("UI subprocess %s failed (code %s): %s", command, result.returncode, stderr)
            return None
        output = result.stdout.strip()
        if not output:
            return None
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            logger.warning("UI subprocess %s returned invalid JSON", command)
            return None
        return data or None
    finally:
        set_ui_active(False)


def show_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    return _run_ui_subprocess("search", {"items": items})


def show_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    return _run_ui_subprocess("form", {"fields": fields})


def show_snippet_editor(config_dir: str) -> dict[str, str] | None:
    return _run_ui_subprocess("editor", {"config_dir": config_dir})
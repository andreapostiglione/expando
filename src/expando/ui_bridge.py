from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any


def _headless() -> bool:
    return os.environ.get("EXPANDO_HEADLESS", "").lower() in {"1", "true", "yes"}


def _run_ui_subprocess(command: str, payload: dict[str, Any]) -> dict[str, str] | None:
    if _headless():
        return None

    result = subprocess.run(
        [sys.executable, "-m", "expando.ui_cli", command],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if not output:
        return None
    data = json.loads(output)
    return data or None


def show_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    return _run_ui_subprocess("search", {"items": items})


def show_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    return _run_ui_subprocess("form", {"fields": fields})
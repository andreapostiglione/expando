from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Any, Callable

from .permissions import _check_accessibility_macos, clipboard_injection_ready


def _probe_system_events(
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str]:
    run = runner or subprocess.run
    script = 'tell application "System Events" to return (count of processes) > 0'
    try:
        result = run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    if result.returncode == 0 and result.stdout.strip().lower() == "true":
        return True, "system_events_ok"
    detail = (result.stderr or result.stdout or "system_events_failed").strip()
    return False, detail


def run_injection_probe(
    config_dir: Path,
    *,
    accessibility: bool | None = None,
    clipboard_ready: bool | None = None,
    system: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    del config_dir  # reserved for future live-probe state
    platform_name = system or platform.system()
    if platform_name != "Darwin":
        return {
            "ok": None,
            "method": "skip",
            "detail": "injection probe available only on macOS",
            "skipped": True,
        }

    if accessibility is None:
        accessibility = _check_accessibility_macos()
    if accessibility is False:
        return {
            "ok": False,
            "method": "skip",
            "detail": "accessibility not granted",
            "skipped": True,
        }

    if clipboard_ready is None:
        clipboard_ready = clipboard_injection_ready()
    if clipboard_ready is True:
        return {
            "ok": True,
            "method": "clipboard",
            "detail": "clipboard round-trip OK",
            "skipped": False,
        }
    if clipboard_ready is False:
        return {
            "ok": False,
            "method": "clipboard",
            "detail": "clipboard injection path unavailable",
            "skipped": False,
        }

    ok, detail = _probe_system_events(runner=runner)
    return {
        "ok": ok,
        "method": "system_events",
        "detail": detail,
        "skipped": False,
    }
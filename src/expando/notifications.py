from __future__ import annotations

import platform
import subprocess


def notify(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return
    script = (
        f'display notification {_applescript_string(message)} '
        f"with title {_applescript_string(title)}"
    )
    subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )


def notify_toggle(enabled: bool) -> None:
    state = "enabled" if enabled else "disabled"
    notify("Expando", f"Text expansion {state}")


def _applescript_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'
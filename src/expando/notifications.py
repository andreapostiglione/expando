from __future__ import annotations

import platform
import subprocess


def notify(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        return
    script = f'display notification "{_escape(message)}" with title "{_escape(title)}"'
    subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )


def notify_toggle(enabled: bool) -> None:
    state = "attivo" if enabled else "disattivato"
    notify("Expando", f"Espansione testi {state}")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
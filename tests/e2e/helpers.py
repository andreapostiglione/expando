from __future__ import annotations

import platform
import subprocess
import sys
import time


def run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "AppleScript failed")
    return result.stdout.strip()


def frontmost_app_name() -> str:
    return run_applescript(
        'tell application "System Events" to return name of first application process whose frontmost is true'
    )


def reset_textedit() -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("TextEdit helpers require macOS")
    run_applescript(
        '''
        tell application "TextEdit"
            if it is running then
                repeat while (count of documents) > 0
                    close front document saving no
                end repeat
                quit saving no
            end if
        end tell
        delay 0.6
        tell application "TextEdit"
            activate
            make new document
        end tell
        delay 0.5
        tell application "System Events"
            set frontmost of first process whose name is "TextEdit" to true
        end tell
        '''
    )
    for _ in range(6):
        time.sleep(0.25)
        if frontmost_app_name() == "TextEdit":
            return
    raise RuntimeError(f"TextEdit is not frontmost (got {frontmost_app_name()!r})")


def open_textedit_blank() -> None:
    reset_textedit()


def get_textedit_content() -> str:
    return run_applescript('tell application "TextEdit" to return text of front document')


def wait_for_textedit_content(predicate, *, timeout: float = 3.0, interval: float = 0.2) -> str:
    deadline = time.monotonic() + timeout
    content = ""
    while time.monotonic() < deadline:
        content = get_textedit_content()
        if predicate(content):
            return content
        time.sleep(interval)
    return content


def type_text_via_subprocess(text: str, *, delay: float = 0.12) -> None:
    """Type with a separate process so pynput listeners capture real key events."""
    script = f"""
import time
from pynput.keyboard import Controller

keyboard = Controller()
time.sleep(0.4)
for char in {text!r}:
    keyboard.type(char)
    time.sleep({delay})
"""
    subprocess.run([sys.executable, "-c", script], check=True, timeout=30)


def close_textedit_documents() -> None:
    run_applescript(
        '''
        tell application "TextEdit"
            if it is running then
                repeat while (count of documents) > 0
                    close front document saving no
                end repeat
                quit saving no
            end if
        end tell
        '''
    )

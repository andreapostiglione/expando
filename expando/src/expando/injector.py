from __future__ import annotations

import os
import platform
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from pynput.keyboard import Controller, Key

from .image_paths import macos_clipboard_type_for


@dataclass
class InjectorSettings:
    backend: str = "auto"
    clipboard_threshold: int = 100


class TextInjector:
    def __init__(self, settings: InjectorSettings) -> None:
        self.settings = settings
        self.keyboard = Controller()
        self._system = platform.system()
        self._lock = threading.Lock()

    def delete_chars(self, count: int) -> None:
        with self._lock:
            for _ in range(count):
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                time.sleep(0.005)

    def inject_image(self, image_path: Path) -> bool:
        if self._system != "Darwin":
            return False
        return self._mac_clipboard_paste_image(image_path)

    def inject(
        self,
        text: str,
        force_clipboard: bool = False,
        *,
        cursor_left: int | None = None,
    ) -> None:
        with self._lock:
            use_clipboard = force_clipboard or self._should_use_clipboard(text)
            if use_clipboard:
                self._inject_via_clipboard(text)
            else:
                self._inject_via_typing(text)
            if cursor_left:
                self.move_cursor_left(cursor_left)

    def move_cursor_left(self, count: int) -> None:
        with self._lock:
            for _ in range(count):
                self.keyboard.press(Key.left)
                self.keyboard.release(Key.left)
                time.sleep(0.003)

    def _should_use_clipboard(self, text: str) -> bool:
        backend = self.settings.backend
        if backend == "clipboard":
            return True
        if backend == "inject":
            return False
        return len(text) >= self.settings.clipboard_threshold or "\n" in text

    def _inject_via_typing(self, text: str) -> None:
        for char in text:
            if char == "\n":
                self.keyboard.press(Key.enter)
                self.keyboard.release(Key.enter)
            elif char == "\t":
                self.keyboard.press(Key.tab)
                self.keyboard.release(Key.tab)
            else:
                self.keyboard.type(char)
            time.sleep(0.003)

    def _inject_via_clipboard(self, text: str) -> None:
        if self._system == "Darwin":
            self._mac_clipboard_paste(text)
        elif self._system == "Windows":
            self._windows_clipboard_paste(text)
        else:
            self._linux_clipboard_paste(text)

    def _mac_clipboard_paste_image(self, image_path: Path) -> bool:
        type_code = macos_clipboard_type_for(image_path)
        script = (
            f'set imageFile to POSIX file "{image_path}"\n'
            f"set the clipboard to (read imageFile as «class {type_code}»)"
        )
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False
        with self._lock:
            with self.keyboard.pressed(Key.cmd):
                self.keyboard.press("v")
                self.keyboard.release("v")
            time.sleep(0.05)
        return True

    def _mac_clipboard_paste(self, text: str) -> None:
        previous = subprocess.run(["pbpaste"], capture_output=True, text=True)
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        with self.keyboard.pressed(Key.cmd):
            self.keyboard.press("v")
            self.keyboard.release("v")
        time.sleep(0.05)
        if previous.returncode == 0:
            subprocess.run(["pbcopy"], input=previous.stdout, text=True)

    def _linux_clipboard_paste(self, text: str) -> None:
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=False)
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("v")
            self.keyboard.release("v")

    def _windows_clipboard_paste(self, text: str) -> None:
        # Avoid shell=True for security; use cmd /c to invoke clip with stdin pipe
        subprocess.run(
            [os.environ.get("COMSPEC", "cmd.exe"), "/c", "clip"],
            input=text,
            text=True,
            check=False,
        )
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("v")
            self.keyboard.release("v")
from __future__ import annotations

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
        self._lock = threading.RLock()

    def delete_chars(self, count: int, *, delay: float | None = None) -> None:
        # Always individual backspaces. Selection shortcuts (Shift+Left) are
        # unreliable in terminals and leave trigger leftovers before paste.
        step = 0.012 if delay is None else max(0.0, float(delay))
        with self._lock:
            if count <= 0:
                return
            for _ in range(count):
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                if step:
                    time.sleep(step)

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
        post_delete_settle: float | None = None,
    ) -> None:
        with self._lock:
            if post_delete_settle and post_delete_settle > 0:
                time.sleep(post_delete_settle)
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
        if "\n" not in text and "\t" not in text:
            self.keyboard.type(text)
            return
        for char in text:
            if char == "\n":
                self.keyboard.press(Key.enter)
                self.keyboard.release(Key.enter)
                time.sleep(0.002)
            elif char == "\t":
                self.keyboard.press(Key.tab)
                self.keyboard.release(Key.tab)
                time.sleep(0.002)
            else:
                self.keyboard.type(char)

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
        # Let the target app finish processing backspaces before paste.
        time.sleep(0.03)
        with self.keyboard.pressed(Key.cmd):
            self.keyboard.press("v")
            self.keyboard.release("v")
        time.sleep(0.06)
        if previous.returncode == 0:
            subprocess.run(["pbcopy"], input=previous.stdout, text=True)

    def _linux_clipboard_paste(self, text: str) -> None:
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=False)
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("v")
            self.keyboard.release("v")

    def _windows_clipboard_paste(self, text: str) -> None:
        subprocess.run(["clip"], input=text, text=True, shell=True, check=False)
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("v")
            self.keyboard.release("v")

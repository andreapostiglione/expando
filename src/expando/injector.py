from __future__ import annotations

import platform
import subprocess
import threading
import time
from dataclasses import dataclass

from pynput.keyboard import Controller, Key


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

    def inject(self, text: str, force_clipboard: bool = False) -> None:
        with self._lock:
            use_clipboard = force_clipboard or self._should_use_clipboard(text)
            if use_clipboard:
                self._inject_via_clipboard(text)
            else:
                self._inject_via_typing(text)

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
        subprocess.run(["clip"], input=text, text=True, shell=True, check=False)
        with self.keyboard.pressed(Key.ctrl):
            self.keyboard.press("v")
            self.keyboard.release("v")
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from pynput.keyboard import Key, Listener
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import load_config
from .engine import ExpansionEngine
from .injector import InjectorSettings, TextInjector

logger = logging.getLogger(__name__)

TOGGLE_KEY_MAP = {
    "ALT": Key.alt,
    "LEFT_ALT": Key.alt_l,
    "RIGHT_ALT": Key.alt_r,
    "CTRL": Key.ctrl,
    "LEFT_CTRL": Key.ctrl_l,
    "RIGHT_CTRL": Key.ctrl_r,
    "SHIFT": Key.shift,
    "LEFT_SHIFT": Key.shift_l,
    "RIGHT_SHIFT": Key.shift_r,
    "CMD": Key.cmd,
    "LEFT_CMD": Key.cmd,
    "RIGHT_CMD": Key.cmd,
}


class ConfigReloader(FileSystemEventHandler):
    def __init__(self, config_dir: Path, engine: ExpansionEngine) -> None:
        self.config_dir = config_dir
        self.engine = engine
        self._debounce = 0.3
        self._last_reload = 0.0

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        if not str(event.src_path).endswith((".yml", ".yaml")):
            return
        now = time.time()
        if now - self._last_reload < self._debounce:
            return
        self._last_reload = now
        try:
            config = load_config(self.config_dir)
            self.engine.reload(config)
            logger.info("Configuration reloaded")
        except Exception:
            logger.exception("Failed to reload configuration")


class KeyboardService:
    def __init__(self, config_dir: Path, engine: ExpansionEngine) -> None:
        self.config_dir = config_dir
        self.engine = engine
        self._listener: Listener | None = None
        self._observer: Observer | None = None
        self._toggle_key = self._resolve_toggle_key(engine.config.app.toggle_key)
        self._last_toggle_press = 0.0
        self._toggle_window = 0.45
        self._injecting = False

    def _resolve_toggle_key(self, toggle_key: str) -> Key | None:
        if toggle_key.upper() == "OFF":
            return None
        return TOGGLE_KEY_MAP.get(toggle_key.upper(), Key.alt)

    def start(self) -> None:
        if self.engine.config.app.auto_restart:
            handler = ConfigReloader(self.config_dir, self.engine)
            self._observer = Observer()
            self._observer.schedule(handler, str(self.config_dir), recursive=True)
            self._observer.start()

        self._listener = Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.start()
        logger.info("Expando keyboard listener started")

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None

    def join(self) -> None:
        if self._listener:
            self._listener.join()

    def _on_press(self, key) -> None:
        if self._toggle_key and key == self._toggle_key:
            now = time.time()
            if now - self._last_toggle_press <= self._toggle_window:
                enabled = self.engine.toggle_enabled()
                state = "enabled" if enabled else "disabled"
                logger.info("Expando %s", state)
                self._last_toggle_press = 0.0
            else:
                self._last_toggle_press = now

    def _on_release(self, key) -> None:
        if self._injecting:
            return

        try:
            if key == Key.backspace:
                self.engine.handle_backspace()
                return

            if hasattr(key, "char") and key.char is not None:
                self._maybe_expand(self.engine.handle_char(key.char))
                return

            if isinstance(key, Key):
                self._maybe_expand(self.engine.handle_key(key))
        except Exception:
            logger.exception("Expansion failed")

    def _maybe_expand(self, expanded: bool) -> None:
        if expanded:
            self._injecting = True
            threading.Timer(0.15, self._clear_injecting).start()

    def _clear_injecting(self) -> None:
        self._injecting = False


def run_service(config_dir: Path) -> None:
    config = load_config(config_dir)
    injector = TextInjector(
        InjectorSettings(
            backend=config.app.backend,
            clipboard_threshold=config.app.clipboard_threshold,
        )
    )
    engine = ExpansionEngine(
        config=config,
        injector=injector,
        on_expand=lambda result: logger.info("Expanded %r -> %r", result.trigger, result.replacement),
    )
    service = KeyboardService(config_dir=config_dir, engine=engine)
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
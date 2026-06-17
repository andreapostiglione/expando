from __future__ import annotations

import logging
import platform
import threading
import time
from pathlib import Path
from typing import Callable

from pynput.keyboard import Key, Listener
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import ConfigBundle, load_config
from .engine import ExpansionEngine, build_engine
from .hotkeys import shortcut_pressed
from .logging_setup import setup_logging
from .notifications import notify_toggle
from .search import build_search_items, pick_snippet, resolve_snippet_text
from .ui_state import is_ui_active

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
    def __init__(self, on_reload: Callable[[], None]) -> None:
        self._on_reload = on_reload
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
            self._on_reload()
        except Exception:
            logger.exception("Failed to reload configuration")


class KeyboardService:
    def __init__(self, config_dir: Path, engine: ExpansionEngine) -> None:
        self.config_dir = config_dir
        self.engine = engine
        self.on_toggle: Callable[[], None] | None = None
        self._listener: Listener | None = None
        self._observer: Observer | None = None
        self._toggle_key = self._resolve_toggle_key(engine._base_bundle.app.toggle_key)
        self._last_toggle_press = 0.0
        self._toggle_window = 0.45
        self._state_lock = threading.Lock()
        self._injecting = False
        self._pressed_modifiers: set = set()

    def open_search(self) -> None:
        if not self.engine.enabled:
            return
        config = self.engine.config
        items = build_search_items(config.matches, config.app)
        picked = pick_snippet(items, app_config=config.app)
        if not picked:
            return
        text = resolve_snippet_text(picked.match, app_config=config.app)
        if not text:
            return
        self._set_injecting(True)
        try:
            self.engine.injector.inject(
                text,
                force_clipboard=picked.match.force_clipboard
                or len(text) >= config.app.clipboard_threshold,
            )
            logger.info("Inserted snippet from search: %s", picked.trigger)
        finally:
            threading.Timer(0.15, lambda: self._set_injecting(False)).start()

    def apply_config_reload(self) -> None:
        config = load_config(self.config_dir)
        self.engine.reload(config)
        self._toggle_key = self._resolve_toggle_key(self.engine._base_bundle.app.toggle_key)
        self._sync_file_watcher()
        logger.info("Configuration reloaded")

    def _sync_file_watcher(self) -> None:
        wants_observer = self.engine._base_bundle.app.auto_restart
        if wants_observer and self._observer is None:
            handler = ConfigReloader(self.apply_config_reload)
            self._observer = Observer()
            self._observer.schedule(handler, str(self.config_dir), recursive=True)
            self._observer.start()
        elif not wants_observer and self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None

    def _resolve_toggle_key(self, toggle_key: str) -> Key | None:
        if toggle_key.upper() == "OFF":
            return None
        return TOGGLE_KEY_MAP.get(toggle_key.upper(), Key.alt)

    def notify_toggle(self) -> None:
        notify_toggle(self.engine.enabled)
        if self.on_toggle:
            self.on_toggle()

    def start(self) -> None:
        self._sync_file_watcher()
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

    def _set_injecting(self, value: bool) -> None:
        with self._state_lock:
            self._injecting = value

    def _is_injecting(self) -> bool:
        with self._state_lock:
            return self._injecting

    def _track_modifier_press(self, key) -> None:
        if key in {
            Key.cmd, Key.alt, Key.ctrl, Key.shift,
            Key.cmd_l, Key.cmd_r, Key.alt_l, Key.alt_r,
            Key.ctrl_l, Key.ctrl_r, Key.shift_l, Key.shift_r,
        }:
            if key in {Key.cmd, Key.cmd_l, Key.cmd_r}:
                self._pressed_modifiers.add(Key.cmd)
            elif key in {Key.shift, Key.shift_l, Key.shift_r}:
                self._pressed_modifiers.add(Key.shift)
            elif key in {Key.alt, Key.alt_l, Key.alt_r}:
                self._pressed_modifiers.add(Key.alt)
            elif key in {Key.ctrl, Key.ctrl_l, Key.ctrl_r}:
                self._pressed_modifiers.add(Key.ctrl)

    def _track_modifier_release(self, key) -> None:
        if key in {Key.cmd, Key.cmd_l, Key.cmd_r}:
            self._pressed_modifiers.discard(Key.cmd)
        elif key in {Key.shift, Key.shift_l, Key.shift_r}:
            self._pressed_modifiers.discard(Key.shift)
        elif key in {Key.alt, Key.alt_l, Key.alt_r}:
            self._pressed_modifiers.discard(Key.alt)
        elif key in {Key.ctrl, Key.ctrl_l, Key.ctrl_r}:
            self._pressed_modifiers.discard(Key.ctrl)

    def _on_press(self, key) -> None:
        if is_ui_active():
            return
        self._track_modifier_press(key)
        config = self.engine.config.app
        if config.undo_shortcut and shortcut_pressed(
            config.undo_shortcut, self._pressed_modifiers, key
        ):
            if self.engine.undo_last():
                logger.info("Undid last expansion")
            return

        if config.search_shortcut and shortcut_pressed(
            config.search_shortcut, self._pressed_modifiers, key
        ):
            threading.Thread(target=self.open_search, daemon=True).start()
            return

        if self._toggle_key and key == self._toggle_key:
            now = time.time()
            if now - self._last_toggle_press <= self._toggle_window:
                self.engine.toggle_enabled()
                self.notify_toggle()
                logger.info("Expando %s", "enabled" if self.engine.enabled else "disabled")
                self._last_toggle_press = 0.0
            else:
                self._last_toggle_press = now

    def _on_release(self, key) -> None:
        if is_ui_active() or self._is_injecting():
            return
        self._track_modifier_release(key)

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
            self._set_injecting(True)
            threading.Timer(0.15, lambda: self._set_injecting(False)).start()


def build_service(config_dir: Path) -> KeyboardService:
    def _on_expand(result) -> None:
        logger.info("Expanded %r -> %r", result.trigger, result.replacement)
        try:
            from .expansion_stats import record_expansion

            record_expansion(config_dir, result.trigger)
        except Exception:
            logger.exception("Failed to record expansion stats")

    engine = build_engine(config_dir, on_expand=_on_expand)
    return KeyboardService(config_dir=config_dir, engine=engine)


def run_service(config_dir: Path) -> None:
    from .crash_reporting import install_crash_handlers

    setup_logging(config_dir)
    install_crash_handlers(config_dir)
    if platform.system() == "Darwin":
        from .onboarding import maybe_run_onboarding

        maybe_run_onboarding(config_dir)
    service = build_service(config_dir)

    if platform.system() == "Darwin":
        from .menubar import menubar_available, run_with_menubar

        if menubar_available():
            logger.info("Starting Expando with menu bar")
            run_with_menubar(config_dir, service)
            return

    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
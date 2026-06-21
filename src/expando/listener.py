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

from .engine import ExpansionEngine, build_engine
from .hotkeys import shortcut_pressed
from .logging_setup import setup_logging
from .notifications import notify_toggle
from .search import build_search_items, pick_snippet, resolve_snippet_text
from .listener_watchdog import ListenerWatchdog
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
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def cancel(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        if not str(event.src_path).endswith((".yml", ".yaml")):
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce, self._run_reload)
            self._timer.daemon = True
            self._timer.start()

    def _run_reload(self) -> None:
        with self._lock:
            self._timer = None
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
        self._reload_handler: ConfigReloader | None = None
        self._toggle_key = self._resolve_toggle_key(engine._base_bundle.app.toggle_key)
        self._last_toggle_press = 0.0
        self._toggle_window = 0.45
        self._state_lock = threading.Lock()
        self._injecting_depth = 0
        self._injecting_timers: list[threading.Timer] = []
        self._pressed_modifiers: set = set()
        self._listener_dead = False
        self.on_listener_dead: Callable[[], None] | None = None
        self.on_listener_recovered: Callable[[], None] | None = None
        self._watchdog = ListenerWatchdog(
            is_alive=self.is_listener_alive,
            restart=self._restart_listener_with_health,
            on_dead=self._notify_listener_dead,
            on_recovered=self._notify_listener_recovered,
        )

    def open_search(self) -> None:
        from .app_context import capture_frontmost_application_pid, restore_frontmost_application
        from .ui_state import is_ui_active, set_ui_active

        if is_ui_active():
            logger.debug("Search ignored: another UI session is active")
            return

        target_pid = capture_frontmost_application_pid()
        set_ui_active(True)
        try:
            if not self.engine.enabled:
                logger.info("Search ignored: Expando is disabled")
                return
            config = self.engine.config
            items = build_search_items(config.matches, config.app)
            picked = pick_snippet(items, app_config=config.app)
            if not picked:
                return
            text = resolve_snippet_text(picked.match, app_config=config.app)
            if not text:
                return
            restore_frontmost_application(target_pid)
            time.sleep(0.08)
            self._set_injecting(True)
            try:
                self.engine.injector.inject(
                    text,
                    force_clipboard=picked.match.force_clipboard
                    or len(text) >= config.app.clipboard_threshold,
                )
                logger.info("Inserted snippet from search: %s", picked.trigger)
            finally:
                self._schedule_injecting_end()
        finally:
            set_ui_active(False)

    def apply_config_reload(self) -> None:
        from .config_reload_gate import safe_reload_config

        safe_reload_config(self.config_dir, self.engine)
        self._toggle_key = self._resolve_toggle_key(self.engine._base_bundle.app.toggle_key)
        self._sync_file_watcher()
        try:
            from .health import record_config_reload

            record_config_reload(self.config_dir)
        except Exception:
            logger.debug("Failed to record config reload health metric", exc_info=True)
        logger.info("Configuration reloaded")

    def _sync_file_watcher(self) -> None:
        wants_observer = self.engine._base_bundle.app.auto_restart
        if wants_observer and self._observer is None:
            self._reload_handler = ConfigReloader(self.apply_config_reload)
            self._observer = Observer()
            self._observer.schedule(self._reload_handler, str(self.config_dir), recursive=True)
            self._observer.start()
        elif not wants_observer and self._observer is not None:
            if getattr(self, "_reload_handler", None) is not None:
                self._reload_handler.cancel()
                self._reload_handler = None
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

    def is_listener_alive(self) -> bool:
        listener = self._listener
        if listener is None:
            return False
        running = getattr(listener, "running", None)
        if running is not None:
            return bool(running)
        thread = getattr(listener, "_thread", None)
        return bool(thread and thread.is_alive())

    def listener_dead(self) -> bool:
        return self._listener_dead or self._watchdog.listener_dead()

    def restart_listener(self) -> None:
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                logger.debug("Listener stop during restart failed", exc_info=True)
            self._listener = None
        self._listener = Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=False,
        )
        self._listener.start()
        self._watchdog.touch()
        self._listener_dead = False

    def _record_listener_health(self, *, alive: bool, restarted: bool = False) -> None:
        try:
            from .health import (
                record_listener_alive,
                record_listener_restart,
            )

            if restarted:
                record_listener_restart(self.config_dir)
            else:
                record_listener_alive(self.config_dir, alive=alive)
        except Exception:
            logger.debug("Failed to record listener health metric", exc_info=True)

    def _restart_listener_with_health(self) -> None:
        self.restart_listener()
        self._record_listener_health(alive=True, restarted=True)

    def _notify_listener_dead(self) -> None:
        self._listener_dead = True
        self._record_listener_health(alive=False)
        if self.on_listener_dead:
            self.on_listener_dead()

    def _notify_listener_recovered(self) -> None:
        self._listener_dead = False
        self._record_listener_health(alive=True)
        if self.on_listener_recovered:
            self.on_listener_recovered()

    def start(self) -> None:
        from .ui_state import set_ui_active

        set_ui_active(False)
        self._sync_file_watcher()
        self.restart_listener()
        self._watchdog.start()
        self._schedule_permission_check()
        logger.info("Expando keyboard listener started")

    def _schedule_permission_check(self) -> None:
        def _check() -> None:
            time.sleep(0.5)
            listener = self._listener
            accessibility_ok = listener is None or getattr(listener, "IS_TRUSTED", True)
            label = "Expando"
            input_monitoring_ok = True

            if platform.system() == "Darwin":
                try:
                    from .permissions import check_permissions

                    status = check_permissions()
                    if status.runtime is not None:
                        label = status.runtime.grant_label
                    input_monitoring_ok = status.input_monitoring is not False
                except Exception:
                    logger.debug(
                        "Permission check after listener start failed",
                        exc_info=True,
                    )

            from .i18n import tf
            from .notifications import notify

            if not accessibility_ok:
                logger.warning(
                    "Accessibility not granted for the keyboard listener "
                    "(pynput IS_TRUSTED=False)"
                )
                notify(
                    "Expando",
                    tf("listener.permissions.accessibility", grant_label=label),
                )
            if not input_monitoring_ok:
                logger.warning(
                    "Input Monitoring not granted for %s — snippet triggers may not "
                    "be detected. Enable it in System Settings → Privacy → "
                    "Input Monitoring.",
                    label,
                )
                notify(
                    "Expando",
                    tf("listener.permissions.input_monitoring", grant_label=label),
                )

        threading.Thread(target=_check, daemon=True, name="expando-perm-check").start()

    def stop(self) -> None:
        self._watchdog.stop()
        with self._state_lock:
            for timer in self._injecting_timers:
                timer.cancel()
            self._injecting_timers.clear()
            self._injecting_depth = 0
        if getattr(self, "_reload_handler", None) is not None:
            self._reload_handler.cancel()
            self._reload_handler = None
        if self._listener:
            self._listener.stop()
            self._listener = None
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            if self._observer.is_alive():
                logger.warning("Config file watcher did not stop within 2s")
            self._observer = None

    def join(self) -> None:
        if self._listener:
            self._listener.join()

    def _set_injecting(self, value: bool) -> None:
        with self._state_lock:
            if value:
                self._injecting_depth += 1
            else:
                self._injecting_depth = max(0, self._injecting_depth - 1)

    def _is_injecting(self) -> bool:
        with self._state_lock:
            return self._injecting_depth > 0

    def _schedule_injecting_end(self, delay: float = 0.15) -> None:
        timer = threading.Timer(delay, self._finish_injecting)
        timer.daemon = True
        with self._state_lock:
            self._injecting_timers.append(timer)
        timer.start()

    def _finish_injecting(self) -> None:
        with self._state_lock:
            self._injecting_depth = max(0, self._injecting_depth - 1)
            self._injecting_timers = [
                item for item in self._injecting_timers if item.is_alive()
            ]

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
            self._schedule_open_search()
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

    def _schedule_open_search(self) -> None:
        if platform.system() == "Darwin":
            try:
                from .ui_main_thread import call_on_main_thread

                call_on_main_thread(self.open_search, wait=False)
                return
            except Exception:
                logger.debug("Failed to schedule snippet search on main thread", exc_info=True)
        threading.Thread(target=self.open_search, daemon=True).start()

    def _maybe_expand(self, expanded: bool) -> None:
        if expanded:
            self._set_injecting(True)
            self._schedule_injecting_end()


def build_service(config_dir: Path) -> KeyboardService:
    def _on_expand(result) -> None:
        logger.info("Expanded %r -> %r", result.trigger, result.replacement)
        try:
            from .expansion_stats import record_expansion

            record_expansion(config_dir, result.trigger)
        except Exception:
            logger.exception("Failed to record expansion stats")
        try:
            from .health import record_expansion as record_health_expansion

            record_health_expansion(config_dir, result.trigger)
        except Exception:
            logger.debug("Failed to record expansion health metric", exc_info=True)

    engine = build_engine(config_dir, on_expand=_on_expand)
    return KeyboardService(config_dir=config_dir, engine=engine)


def run_service(config_dir: Path) -> None:
    from .crash_loop import apply_startup_crash_policy, is_safe_mode_active
    from .crash_reporting import install_crash_handlers

    setup_logging(config_dir)
    install_crash_handlers(config_dir)
    try:
        from .auto_backup import maybe_run_auto_backup

        archive = maybe_run_auto_backup(config_dir)
        if archive is not None:
            logger.info("Automatic backup created: %s", archive)
    except Exception:
        logger.debug("Automatic backup check failed", exc_info=True)
    try:
        from .health import record_daemon_started

        record_daemon_started(config_dir)
    except Exception:
        logger.debug("Failed to record daemon health metrics", exc_info=True)
    startup = apply_startup_crash_policy(config_dir)
    if startup.get("safe_mode"):
        logger.warning(
            "Expando safe mode active after repeated crashes (backoff=%ss)",
            startup.get("backoff_seconds", 0),
        )
    if platform.system() == "Darwin":
        from .onboarding import maybe_run_onboarding

        maybe_run_onboarding(config_dir)
    service = build_service(config_dir)
    if is_safe_mode_active(config_dir):
        service.engine.enabled = False

    if platform.system() == "Darwin":
        from .menubar import menubar_available, run_with_menubar

        if menubar_available():
            logger.info("Starting Expando with menu bar")
            try:
                run_with_menubar(config_dir, service)
            finally:
                service.stop()
            return

    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
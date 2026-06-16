from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Callable

from pynput.keyboard import Key

from .app_context import get_frontmost_app, is_app_allowed
from .config import ConfigBundle, Match, compile_matches, load_config
from .injector import InjectorSettings, TextInjector
from .renderer import render_match_interactive


WORD_BREAK_KEYS = {
    Key.space,
    Key.enter,
    Key.tab,
}


@dataclass
class ExpansionResult:
    trigger: str
    replacement: str
    match: Match


class ExpansionEngine:
    def __init__(
        self,
        config: ConfigBundle,
        injector: TextInjector,
        on_expand: Callable[[ExpansionResult], None] | None = None,
    ) -> None:
        self.config = config
        self.injector = injector
        self.on_expand = on_expand
        self.enabled = config.app.enabled
        self._buffer = ""
        self._lock = threading.Lock()
        self._literal, self._regex = compile_matches(config.matches)
        self._max_trigger_len = self._compute_max_trigger_len()

    def reload(self, config: ConfigBundle) -> None:
        with self._lock:
            self.config = config
            self.enabled = config.app.enabled
            self._literal, self._regex = compile_matches(config.matches)
            self._max_trigger_len = self._compute_max_trigger_len()
            self._buffer = ""

    def _compute_max_trigger_len(self) -> int:
        literal_max = max((len(trigger) for trigger in self._literal), default=0)
        regex_max = self.config.app.max_regex_buffer_size
        return max(literal_max, regex_max)

    def handle_char(self, char: str) -> bool:
        if not self.enabled or not self._expansion_allowed():
            return False

        with self._lock:
            self._buffer += char
            if len(self._buffer) > self._max_trigger_len:
                self._buffer = self._buffer[-self._max_trigger_len :]
            return self._try_expand(require_word_break=False)

    def handle_key(self, key: Key) -> bool:
        if not self.enabled or not self._expansion_allowed():
            return False

        if key in WORD_BREAK_KEYS:
            with self._lock:
                expanded = self._try_expand(require_word_break=True)
                self._append_key_to_buffer(key)
                return expanded

        char = self._key_to_char(key)
        if char is None:
            return False
        return self.handle_char(char)

    def handle_backspace(self) -> None:
        with self._lock:
            if self._buffer:
                self._buffer = self._buffer[:-1]

    def clear_buffer(self) -> None:
        with self._lock:
            self._buffer = ""

    def toggle_enabled(self) -> bool:
        with self._lock:
            self.enabled = not self.enabled
            return self.enabled

    def _append_key_to_buffer(self, key: Key) -> None:
        char = self._key_to_char(key)
        if char:
            self._buffer += char
            if len(self._buffer) > self._max_trigger_len:
                self._buffer = self._buffer[-self._max_trigger_len :]

    def _key_to_char(self, key: Key) -> str | None:
        if key == Key.space:
            return " "
        if key == Key.tab:
            return "\t"
        if key == Key.enter:
            return "\n"
        return None

    def _expansion_allowed(self) -> bool:
        app_name = get_frontmost_app()
        return is_app_allowed(
            app_name,
            global_blacklist=self.config.app.app_blacklist,
        )

    def _match_allowed(self, match: Match) -> bool:
        app_name = get_frontmost_app()
        return is_app_allowed(
            app_name,
            global_blacklist=self.config.app.app_blacklist,
            if_app=match.if_app or None,
            unless_app=match.unless_app or None,
        )

    def _try_expand(self, require_word_break: bool) -> bool:
        match_info = self._find_match(require_word_break=require_word_break)
        if not match_info:
            return False

        trigger, match = match_info
        replacement = render_match_interactive(match, app_config=self.config.app)
        if replacement is None:
            return False
        self.injector.delete_chars(len(trigger))
        self.injector.inject(replacement, force_clipboard=match.force_clipboard)
        self._buffer = self._buffer[: -len(trigger)]

        if self.on_expand:
            self.on_expand(ExpansionResult(trigger=trigger, replacement=replacement, match=match))
        return True

    def _find_match(self, require_word_break: bool) -> tuple[str, Match] | None:
        for trigger, match in sorted(self._literal.items(), key=lambda item: len(item[0]), reverse=True):
            if self._buffer.endswith(trigger):
                if match.word_break and not require_word_break:
                    continue
                if not self._match_allowed(match):
                    continue
                return trigger, match

        if self._regex and len(self._buffer) <= self.config.app.max_regex_buffer_size:
            for pattern, match in self._regex:
                found = pattern.search(self._buffer)
                if found and found.end() == len(self._buffer):
                    if match.word_break and not require_word_break:
                        continue
                    if not self._match_allowed(match):
                        continue
                    return found.group(0), match
        return None


def build_engine(config_dir, on_expand=None) -> ExpansionEngine:
    config = load_config(config_dir)
    injector = TextInjector(
        InjectorSettings(
            backend=config.app.backend,
            clipboard_threshold=config.app.clipboard_threshold,
        )
    )
    return ExpansionEngine(config=config, injector=injector, on_expand=on_expand)
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pynput.keyboard import Key

from .app_context import AppContext, get_frontmost_context, match_allowed
from .config import ConfigBundle, Match, active_bundle, compile_matches, load_config
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
        *,
        config_dir: Path | None = None,
    ) -> None:
        self._config_dir = config_dir
        self._base_bundle = config
        self.injector = injector
        self.on_expand = on_expand
        self.enabled = config.app.enabled
        self._buffer = ""
        self._lock = threading.Lock()
        self._literal, self._regex = compile_matches(config.matches)
        self._max_trigger_len = self._compute_max_trigger_len()

    @property
    def config(self) -> ConfigBundle:
        if self._config_dir is not None:
            return active_bundle(self._config_dir, self._base_bundle)
        return self._base_bundle

    def reload(self, config: ConfigBundle) -> None:
        literal, regex = compile_matches(config.matches)
        with self._lock:
            self._base_bundle = config
            self.enabled = config.app.enabled
            self._literal = literal
            self._regex = regex
            self._max_trigger_len = self._compute_max_trigger_len()
            self._buffer = ""

    def _compute_max_trigger_len(self) -> int:
        literal_max = max((len(trigger) for trigger in self._literal), default=0)
        regex_max = self._base_bundle.app.max_regex_buffer_size
        return max(literal_max, regex_max)

    def handle_char(self, char: str) -> bool:
        with self._lock:
            if not self.enabled:
                return False
            context = get_frontmost_context()
            config = self.config
            if not self._expansion_allowed(context, config):
                return False
            self._buffer += char
            if len(self._buffer) > self._max_trigger_len:
                self._buffer = self._buffer[-self._max_trigger_len :]
            return self._try_expand(
                require_word_break=False,
                context=context,
                config=config,
            )

    def handle_key(self, key: Key) -> bool:
        with self._lock:
            if not self.enabled:
                return False
            context = get_frontmost_context()
            config = self.config
            if not self._expansion_allowed(context, config):
                return False

            if key in WORD_BREAK_KEYS:
                expanded = self._try_expand(
                    require_word_break=True,
                    context=context,
                    config=config,
                )
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

    def _expansion_allowed(self, context: AppContext, config: ConfigBundle) -> bool:
        return match_allowed(
            context,
            global_blacklist=config.app.app_blacklist,
        )

    def _match_allowed(self, match: Match, context: AppContext, config: ConfigBundle) -> bool:
        return match_allowed(
            context,
            global_blacklist=config.app.app_blacklist,
            if_app=match.if_app or None,
            unless_app=match.unless_app or None,
            if_bundle=match.if_bundle or None,
            unless_bundle=match.unless_bundle or None,
            if_title=match.if_title or None,
            unless_title=match.unless_title or None,
        )

    def _try_expand(
        self,
        *,
        require_word_break: bool,
        context: AppContext,
        config: ConfigBundle,
    ) -> bool:
        match_info = self._find_match(
            require_word_break=require_word_break,
            context=context,
            config=config,
        )
        if not match_info:
            return False

        trigger, match = match_info
        replacement = render_match_interactive(match, app_config=config.app)
        if replacement is None:
            return False
        self.injector.delete_chars(len(trigger))
        self.injector.inject(replacement, force_clipboard=match.force_clipboard)
        self._buffer = self._buffer[: -len(trigger)]

        if self.on_expand:
            self.on_expand(
                ExpansionResult(trigger=trigger, replacement=replacement, match=match)
            )
        return True

    def _find_match(
        self,
        *,
        require_word_break: bool,
        context: AppContext,
        config: ConfigBundle,
    ) -> tuple[str, Match] | None:
        for trigger, match in sorted(self._literal.items(), key=lambda item: len(item[0]), reverse=True):
            if self._buffer.endswith(trigger):
                if match.word_break and not require_word_break and not match.force_break:
                    continue
                if not self._match_allowed(match, context, config):
                    continue
                return trigger, match

        if self._regex and len(self._buffer) <= config.app.max_regex_buffer_size:
            for pattern, match in self._regex:
                found = pattern.search(self._buffer)
                if found and found.end() == len(self._buffer):
                    if match.word_break and not require_word_break and not match.force_break:
                        continue
                    if not self._match_allowed(match, context, config):
                        continue
                    return found.group(0), match
        return None


def build_engine(
    config_dir: Path,
    on_expand: Callable[[ExpansionResult], None] | None = None,
) -> ExpansionEngine:
    config = load_config(config_dir)
    injector = TextInjector(
        InjectorSettings(
            backend=config.app.backend,
            clipboard_threshold=config.app.clipboard_threshold,
        )
    )
    return ExpansionEngine(
        config=config,
        injector=injector,
        on_expand=on_expand,
        config_dir=config_dir,
    )
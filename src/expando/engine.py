from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from pynput.keyboard import Key

from .app_context import (
    AppContext,
    enrich_context_window_title,
    get_frontmost_context,
    match_allowed,
    pattern_matches,
)
from .block_notifications import BlockNotifier
from .config import ConfigBundle, Match, active_bundle, compile_matches, load_config
from .injector import InjectorSettings, TextInjector
from .plugins import PluginManager
from .render_context import RenderContext
from .renderer import render_match_interactive
from .when_conditions import evaluate_when, when_needs_form
from .secure_input import is_secure_input_active
from .text_transform import (
    apply_propagate_case,
    apply_trim,
    strip_cursor_hint,
)

logger = logging.getLogger(__name__)

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


@dataclass
class _LastExpansion:
    trigger: str
    replacement: str
    suffix: str = ""


class ExpansionEngine:
    def __init__(
        self,
        config: ConfigBundle,
        injector: TextInjector,
        on_expand: Callable[[ExpansionResult], None] | None = None,
        *,
        config_dir: Path | None = None,
        block_notifier: BlockNotifier | None = None,
    ) -> None:
        self._config_dir = config_dir
        self._base_bundle = config
        self.injector = injector
        self.on_expand = on_expand
        self._block_notifier = block_notifier
        self.enabled = config.app.enabled
        self._buffer = ""
        self._lock = threading.Lock()
        self._literal, self._regex = compile_matches(config.matches)
        self._literal_triggers = set(self._literal)
        self._max_trigger_len = self._compute_max_trigger_len()
        self._postponed: tuple[str, Match] | None = None
        self._last_expansion: _LastExpansion | None = None
        self._needs_window_title = self._compute_needs_window_title(config.matches)
        self._plugin_manager = (
            PluginManager(config_dir) if config_dir is not None else None
        )

    @property
    def config(self) -> ConfigBundle:
        context = get_frontmost_context()
        return self._resolve_config(context)

    def reload(self, config: ConfigBundle) -> None:
        literal, regex = compile_matches(config.matches)
        with self._lock:
            self._base_bundle = config
            self.enabled = config.app.enabled
            if self._block_notifier is not None:
                self._block_notifier.enabled = config.app.notify_on_block
                self._block_notifier.cooldown_seconds = float(
                    config.app.notify_cooldown_seconds
                )
            self._literal = literal
            self._regex = regex
            self._literal_triggers = set(literal)
            self._max_trigger_len = self._compute_max_trigger_len()
            self._needs_window_title = self._compute_needs_window_title(config.matches)
            self._buffer = ""
            self._postponed = None
            self._last_expansion = None
            if self._plugin_manager is not None:
                self._plugin_manager.reload()

    def undo_last(self) -> bool:
        with self._lock:
            last = self._last_expansion
            if last is None:
                return False
            self._last_expansion = None
            self.injector.delete_chars(len(last.replacement))
            restore = last.trigger + last.suffix
            if restore:
                self.injector.inject(restore)
            self._buffer = restore
            self._postponed = None
            return True

    def _compute_max_trigger_len(self) -> int:
        literal_max = max((len(trigger) for trigger in self._literal), default=0)
        regex_max = self._base_bundle.app.max_regex_buffer_size
        return max(literal_max, regex_max)

    def _compute_needs_window_title(self, matches: list[Match]) -> bool:
        return any(match.if_title or match.unless_title for match in matches)

    def _resolve_config(self, context: AppContext) -> ConfigBundle:
        if self._config_dir is None:
            return self._base_bundle
        return active_bundle(
            self._config_dir,
            self._base_bundle,
            app_name=context.name,
        )

    def _runtime_context(self) -> AppContext:
        context = get_frontmost_context()
        if self._needs_window_title:
            return enrich_context_window_title(context)
        return context

    def handle_char(self, char: str) -> bool:
        with self._lock:
            if not self.enabled:
                return False
            context = self._runtime_context()
            config = self._resolve_config(context)
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
            context = self._runtime_context()
            config = self._resolve_config(context)
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
            self._postponed = None

    def clear_buffer(self) -> None:
        with self._lock:
            self._buffer = ""
            self._postponed = None

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

    def _secure_input_blocks(self, config: ConfigBundle) -> bool:
        return config.app.respect_secure_input and is_secure_input_active()

    def _match_allowed(self, match: Match, context: AppContext, config: ConfigBundle) -> bool:
        if not match_allowed(
            context,
            global_blacklist=config.app.app_blacklist,
            if_app=match.if_app or None,
            unless_app=match.unless_app or None,
            if_bundle=match.if_bundle or None,
            unless_bundle=match.unless_bundle or None,
            if_title=match.if_title or None,
            unless_title=match.unless_title or None,
        ):
            return False
        if match.when and when_needs_form(match.when):
            return True
        if match.when and not evaluate_when(match.when, context):
            return False
        return True

    def _has_left_word_boundary(self, trigger: str) -> bool:
        index = len(self._buffer) - len(trigger)
        if index <= 0:
            return True
        return self._buffer[index - 1].isspace()

    def _could_extend_to_longer_trigger(self) -> bool:
        buffer = self._buffer
        for trigger in self._literal_triggers:
            if len(trigger) > len(buffer) and trigger.startswith(buffer):
                return True
        return False

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

        if self._postponed is not None:
            postponed_trigger, postponed_match = self._postponed
            if match_info and len(match_info[0]) > len(postponed_trigger):
                self._postponed = None
            elif self._could_extend_to_longer_trigger():
                return False
            else:
                self._postponed = None
                suffix = self._buffer[len(postponed_trigger) :]
                return self._execute_expand(
                    postponed_trigger,
                    postponed_match,
                    context=context,
                    config=config,
                    suffix=suffix,
                )

        if not match_info:
            blocked = self._find_blocked_match(
                require_word_break=require_word_break,
                context=context,
                config=config,
            )
            if blocked is not None:
                trigger, match, detail = blocked
                logger.info(
                    "Trigger %r blocked in app %r (%s)",
                    trigger,
                    context.name,
                    detail,
                )
                if self._block_notifier is not None:
                    self._block_notifier.notify_app_rule(
                        trigger=trigger,
                        app_name=context.name or "",
                        detail=detail,
                    )
            return False

        trigger, match = match_info
        if match.postpone and self._buffer.endswith(trigger):
            self._postponed = (trigger, match)
            return False

        return self._execute_expand(
            trigger,
            match,
            context=context,
            config=config,
        )

    def _execute_expand(
        self,
        trigger: str,
        match: Match,
        *,
        context: AppContext,
        config: ConfigBundle,
        suffix: str = "",
    ) -> bool:
        if self._secure_input_blocks(config):
            logger.debug("Expansion of %r blocked by secure input", trigger)
            if self._block_notifier is not None:
                self._block_notifier.notify_secure_input(trigger=trigger)
            return False
        render_ctx = RenderContext(
            config_dir=str(self._config_dir) if self._config_dir else None,
            trigger=trigger,
            app_name=context.name or "",
            bundle_id=context.bundle_id or "",
            window_title=context.window_title or "",
        )
        if self._plugin_manager is not None:
            self._plugin_manager.run_before_expand(render_ctx)
        try:
            replacement = render_match_interactive(
                match,
                app_config=config.app,
                render_context=render_ctx,
            )
        except RuntimeError as exc:
            message = str(exc)
            if "not allowed" in message.lower():
                logger.warning(
                    "Shell variable blocked for trigger %r: %s",
                    trigger,
                    message,
                )
                if self._block_notifier is not None:
                    self._block_notifier.notify_shell_denied(trigger=trigger)
            else:
                logger.exception("Render failed for trigger %r", trigger)
            return False
        if replacement is None:
            return False
        if match.when and when_needs_form(match.when):
            if not evaluate_when(
                match.when,
                context,
                form_values=render_ctx.form_values,
                require_form=True,
            ):
                return False
        if self._plugin_manager is not None:
            replacement = self._plugin_manager.transform_replacement(
                replacement,
                render_ctx,
            )

        typed_trigger = self._buffer[-len(trigger) :]
        if match.propagate_case:
            replacement = apply_propagate_case(
                trigger,
                replacement,
                typed_trigger,
                uppercase_style=match.uppercase_style,
            )
        if match.trim:
            replacement = apply_trim(replacement)
        replacement, cursor_left = strip_cursor_hint(replacement)

        self.injector.delete_chars(len(trigger))
        pasted_image = False
        if match.image and self._config_dir is not None:
            try:
                from .image_paths import resolve_image_path

                image_file = resolve_image_path(self._config_dir, match.image)
                pasted_image = self.injector.inject_image(image_file)
                if not pasted_image and not replacement:
                    replacement = str(image_file)
            except RuntimeError as exc:
                logger.warning("Image expansion failed for %r: %s", trigger, exc)

        if pasted_image:
            if cursor_left:
                self.injector.move_cursor_left(cursor_left)
        else:
            self.injector.inject(
                replacement,
                force_clipboard=match.force_clipboard or bool(match.image),
                cursor_left=cursor_left,
            )
        self._buffer = suffix
        self._last_expansion = _LastExpansion(
            trigger=trigger,
            replacement=replacement,
            suffix=suffix,
        )

        if self._plugin_manager is not None:
            self._plugin_manager.run_after_expand(render_ctx, replacement)
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
        candidates: list[tuple[str, Match]] = []

        for trigger, match_group in self._literal.items():
            for match in match_group:
                if not self._buffer.endswith(trigger):
                    if not (
                        match.ignore_case
                        and self._buffer.casefold().endswith(trigger.casefold())
                    ):
                        continue
                if match.word_break and not require_word_break and not match.force_break:
                    continue
                if match.right_word and not require_word_break and not match.force_break:
                    continue
                if match.left_word and not self._has_left_word_boundary(trigger):
                    continue
                if not self._match_allowed(match, context, config):
                    if self._buffer.casefold().endswith(trigger.casefold()):
                        logger.debug(
                            "Trigger %r matched buffer but blocked in app %r (%s)",
                            trigger,
                            context.name,
                            context.bundle_id,
                        )
                    continue
                candidates.append((trigger, match))

        if self._regex and len(self._buffer) <= config.app.max_regex_buffer_size:
            for pattern, match in self._regex:
                found = pattern.search(self._buffer)
                if not found or found.end() != len(self._buffer):
                    continue
                if match.word_break and not require_word_break and not match.force_break:
                    continue
                if match.right_word and not require_word_break and not match.force_break:
                    continue
                if not self._match_allowed(match, context, config):
                    continue
                candidates.append((found.group(0), match))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[1].priority, len(item[0])), reverse=True)
        return candidates[0]

    def _find_blocked_match(
        self,
        *,
        require_word_break: bool,
        context: AppContext,
        config: ConfigBundle,
    ) -> tuple[str, Match, str] | None:
        blocked: list[tuple[str, Match, str]] = []

        for trigger, match_group in self._literal.items():
            for match in match_group:
                if not self._buffer.endswith(trigger):
                    if not (
                        match.ignore_case
                        and self._buffer.casefold().endswith(trigger.casefold())
                    ):
                        continue
                if match.word_break and not require_word_break and not match.force_break:
                    continue
                if match.right_word and not require_word_break and not match.force_break:
                    continue
                if match.left_word and not self._has_left_word_boundary(trigger):
                    continue
                if self._match_allowed(match, context, config):
                    continue
                detail = self._app_rule_detail(match, context, config)
                if match.when:
                    detail = "when"
                blocked.append((trigger, match, detail))

        if self._regex and len(self._buffer) <= config.app.max_regex_buffer_size:
            for pattern, match in self._regex:
                found = pattern.search(self._buffer)
                if not found or found.end() != len(self._buffer):
                    continue
                if match.word_break and not require_word_break and not match.force_break:
                    continue
                if match.right_word and not require_word_break and not match.force_break:
                    continue
                if self._match_allowed(match, context, config):
                    continue
                detail = self._app_rule_detail(match, context, config)
                blocked.append((found.group(0), match, detail))

        if not blocked:
            return None

        blocked.sort(key=lambda item: (item[1].priority, len(item[0])), reverse=True)
        return blocked[0]

    def _app_rule_detail(
        self,
        match: Match,
        context: AppContext,
        config: ConfigBundle,
    ) -> str:
        if pattern_matches(context.name, config.app.app_blacklist):
            return "app_blacklist"
        if match.unless_app and pattern_matches(context.name, match.unless_app):
            return f"unless_app: {', '.join(match.unless_app)}"
        if match.unless_bundle and pattern_matches(context.bundle_id, match.unless_bundle):
            return f"unless_bundle: {', '.join(match.unless_bundle)}"
        if match.unless_title and pattern_matches(context.window_title, match.unless_title):
            return f"unless_title: {', '.join(match.unless_title)}"
        if match.if_app and not pattern_matches(context.name, match.if_app):
            return f"if_app: {', '.join(match.if_app)}"
        if match.if_bundle and not pattern_matches(context.bundle_id, match.if_bundle):
            return f"if_bundle: {', '.join(match.if_bundle)}"
        if match.if_title and not pattern_matches(context.window_title, match.if_title):
            return f"if_title: {', '.join(match.if_title)}"
        return "app_rule"


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
    block_notifier = BlockNotifier(
        enabled=config.app.notify_on_block,
        cooldown_seconds=float(config.app.notify_cooldown_seconds),
    )
    return ExpansionEngine(
        config=config,
        injector=injector,
        on_expand=on_expand,
        config_dir=config_dir,
        block_notifier=block_notifier,
    )
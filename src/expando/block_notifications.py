from __future__ import annotations

import time
from dataclasses import dataclass

from .i18n import t
from .notifications import notify

_BLOCK_REASONS = frozenset({"secure_input", "app_rule", "shell_denied"})


@dataclass(frozen=True)
class BlockEvent:
    reason: str
    trigger: str = ""
    app_name: str = ""
    detail: str = ""


class BlockNotifier:
    def __init__(self, *, enabled: bool = True, cooldown_seconds: float = 30.0) -> None:
        self.enabled = enabled
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._last_sent: dict[str, float] = {}

    def notify(self, event: BlockEvent) -> None:
        if not self.enabled or event.reason not in _BLOCK_REASONS:
            return
        key = self._cooldown_key(event)
        now = time.monotonic()
        last = self._last_sent.get(key)
        if last is not None and now - last < self.cooldown_seconds:
            return
        self._last_sent[key] = now
        title, message = self._format(event)
        notify(title, message)

    def notify_secure_input(self, *, trigger: str = "") -> None:
        self.notify(BlockEvent(reason="secure_input", trigger=trigger))

    def notify_app_rule(
        self,
        *,
        trigger: str,
        app_name: str,
        detail: str = "",
    ) -> None:
        self.notify(
            BlockEvent(
                reason="app_rule",
                trigger=trigger,
                app_name=app_name,
                detail=detail,
            )
        )

    def notify_shell_denied(self, *, trigger: str) -> None:
        self.notify(BlockEvent(reason="shell_denied", trigger=trigger))

    def _cooldown_key(self, event: BlockEvent) -> str:
        if event.reason == "secure_input":
            return "secure_input"
        if event.reason == "shell_denied":
            return f"shell_denied:{event.trigger}"
        return f"app_rule:{event.trigger}:{event.app_name}"

    def _format(self, event: BlockEvent) -> tuple[str, str]:
        title = t("notify.block.title")
        if event.reason == "secure_input":
            if event.trigger:
                message = t("notify.block.secure_input_trigger").format(
                    trigger=event.trigger
                )
            else:
                message = t("notify.block.secure_input")
        elif event.reason == "shell_denied":
            message = t("notify.block.shell_denied").format(trigger=event.trigger)
        else:
            app_label = event.app_name or t("notify.block.unknown_app")
            if event.detail:
                message = t("notify.block.app_rule_detail").format(
                    trigger=event.trigger,
                    app=app_label,
                    detail=event.detail,
                )
            else:
                message = t("notify.block.app_rule").format(
                    trigger=event.trigger,
                    app=app_label,
                )
        return title, message
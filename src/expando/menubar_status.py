from __future__ import annotations

from .permissions import PermissionStatus, check_permissions, permissions_ready


def permissions_blocking(status: PermissionStatus | None = None) -> bool:
    status = status or check_permissions(include_clipboard=False)
    return not permissions_ready(status)


def resolve_menubar_title(
    *,
    listener_dead: bool,
    enabled: bool,
    hub_updates: int,
    permissions_ok: bool,
    snoozed: bool,
) -> str | None:
    if listener_dead:
        return "⚠"
    if not permissions_ok:
        return "🔒"
    if snoozed:
        return "⏸"
    if hub_updates > 0:
        return f"↑{hub_updates}"
    if not enabled:
        return "○"
    return None
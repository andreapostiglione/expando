"""Per-app injection profiles (terminal vs standard editors)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Apps where selection-based delete fails and paste timing is stricter.
DEFAULT_TERMINAL_APPS: tuple[str, ...] = (
    "Terminal",
    "iTerm2",
    "iTerm",
    "Warp",
    "Alacritty",
    "kitty",
    "Hyper",
    "WezTerm",
    "Ghostty",
    "Tabby",
    "vscode",  # integrated terminal host; safer clipboard path
    "Code",
    "Cursor",
    "Windsurf",
)

DEFAULT_TERMINAL_BUNDLES: tuple[str, ...] = (
    "com.apple.Terminal",
    "com.googlecode.iterm2",
    "dev.warp.Warp-Stable",
    "dev.warp.Warp",
    "io.alacritty",
    "net.kovidgoyal.kitty",
    "co.zeit.hyper",
    "com.github.wez.wezterm",
    "com.mitchellh.ghostty",
    "com.microsoft.VSCode",
    "com.todesktop.",  # Cursor family
)


@dataclass(frozen=True)
class InjectProfile:
    """Timing and backend hints for text injection."""

    name: str
    backspace_delay: float
    pre_delete_settle: float
    post_delete_settle: float
    force_clipboard: bool


STANDARD_PROFILE = InjectProfile(
    name="standard",
    backspace_delay=0.008,
    pre_delete_settle=0.02,
    post_delete_settle=0.02,
    force_clipboard=False,
)

TERMINAL_PROFILE = InjectProfile(
    name="terminal",
    backspace_delay=0.016,
    pre_delete_settle=0.035,
    post_delete_settle=0.04,
    force_clipboard=True,
)


def app_name_matches_terminal_candidate(app_name: str, candidate: str) -> bool:
    """Match terminal app names without treating Xcode as Code.

    Uses equality and whole-token match so short candidates like ``Code`` do
    not match inside ``Xcode``. Multi-word candidates may still match as a
    substring of the full localized name.
    """
    a = app_name.casefold().strip()
    c = candidate.casefold().strip()
    if not a or not c:
        return False
    if a == c:
        return True
    tokens = re.findall(r"[a-z0-9]+", a)
    if c in tokens:
        return True
    if " " in c and c in a:
        return True
    return False


def is_terminal_app(
    app_name: str | None,
    bundle_id: str | None = None,
    *,
    extra_apps: list[str] | None = None,
) -> bool:
    names = list(DEFAULT_TERMINAL_APPS)
    if extra_apps:
        names.extend(extra_apps)
    if app_name:
        for candidate in names:
            if app_name_matches_terminal_candidate(app_name, candidate):
                return True
    if bundle_id:
        bid = bundle_id.casefold()
        for prefix in DEFAULT_TERMINAL_BUNDLES:
            if bid.startswith(prefix.casefold()) or prefix.casefold() in bid:
                return True
    return False


def resolve_inject_profile(
    app_name: str | None,
    bundle_id: str | None = None,
    *,
    extra_terminal_apps: list[str] | None = None,
) -> InjectProfile:
    if is_terminal_app(app_name, bundle_id, extra_apps=extra_terminal_apps):
        return TERMINAL_PROFILE
    return STANDARD_PROFILE

from __future__ import annotations

from pathlib import Path
from typing import Any

from .text_convert import html_to_plain, markdown_to_plain


def espanso_config_candidates() -> list[Path]:
    home = Path.home()
    return [
        home / "Library" / "Application Support" / "espanso",
        home / ".config" / "espanso",
    ]


def find_espanso_config(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        path = explicit.expanduser()
        return path if path.exists() else None
    for candidate in espanso_config_candidates():
        if candidate.exists():
            return candidate
    return None


def convert_espanso_match(raw: dict[str, Any], config_dir: Path | None = None) -> dict[str, Any] | None:
    converted: dict[str, Any] = {}

    if "trigger" in raw:
        converted["trigger"] = str(raw["trigger"])
    if "triggers" in raw:
        converted["triggers"] = [str(item) for item in raw["triggers"]]

    replace = raw.get("replace", "")
    if raw.get("markdown"):
        replace = markdown_to_plain(str(raw["markdown"]))
    elif raw.get("html"):
        replace = html_to_plain(str(raw["html"]))
    elif raw.get("image_path"):
        image_path = str(raw["image_path"])
        if config_dir is not None:
            image_path = image_path.replace("$CONFIG", str(config_dir))
        replace = image_path
        converted["force_clipboard"] = True
        converted["label"] = str(raw.get("label", "Image snippet"))

    if not isinstance(replace, str):
        replace = str(replace)
    if config_dir is not None:
        replace = replace.replace("$CONFIG", str(config_dir))
    converted["replace"] = replace

    for field in (
        "regex",
        "force_clipboard",
        "force_break",
        "if_app",
        "unless_app",
        "if_bundle",
        "unless_bundle",
        "if_title",
        "unless_title",
        "form",
        "vars",
        "label",
        "search_terms",
    ):
        if field in raw:
            converted[field] = raw[field]

    if raw.get("word"):
        converted["word_break"] = True
    if raw.get("word_break") is not None:
        converted["word_break"] = bool(raw["word_break"])
    if raw.get("left_word"):
        converted["left_word"] = True
    if raw.get("right_word"):
        converted["right_word"] = True
    if raw.get("postpone"):
        converted["postpone"] = True
    if "priority" in raw:
        converted["priority"] = int(raw["priority"])
    if raw.get("propagate_case"):
        converted["propagate_case"] = True
    if raw.get("uppercase_style"):
        converted["uppercase_style"] = str(raw["uppercase_style"])
    if raw.get("trim"):
        converted["trim"] = True

    force_mode = str(raw.get("force_mode", "")).lower()
    if force_mode == "clipboard":
        converted["force_clipboard"] = True

    vars_list = converted.get("vars", []) or []
    normalized_vars: list[dict[str, Any]] = []
    for item in vars_list:
        var = dict(item)
        if var.get("type") == "echo":
            var["type"] = "plain"
            params = dict(var.get("params", {}) or {})
            if "echo" in params:
                params["value"] = params.pop("echo")
            var["params"] = params
        normalized_vars.append(var)
    if normalized_vars:
        converted["vars"] = normalized_vars

    if not converted.get("trigger") and not converted.get("triggers"):
        return None
    return converted


def convert_espanso_app_config(data: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "toggle_key": "toggle_key",
        "backend": "backend",
        "auto_restart": "auto_restart",
        "clipboard_threshold": "clipboard_threshold",
        "max_regex_buffer_size": "max_regex_buffer_size",
        "enabled": "enabled",
        "search_shortcut": "search_shortcut",
    }
    converted: dict[str, Any] = {}
    for src, dst in mapping.items():
        if src in data:
            value = data[src]
            if src == "toggle_key" and value is False:
                converted[dst] = "OFF"
            elif src == "toggle_key" and value is True:
                converted[dst] = "ON"
            else:
                converted[dst] = value
    if "app_blacklist" in data:
        converted["app_blacklist"] = data["app_blacklist"]
    if "shell_allowlist" in data:
        converted["shell_allowlist"] = data["shell_allowlist"]
    return converted
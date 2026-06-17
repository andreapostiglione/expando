from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .forms import FormField
from .match_utils import find_conflicting_literal_triggers


class ConfigCompileError(ValueError):
    pass


@dataclass
class AppConfig:
    toggle_key: str = "ALT"
    backend: str = "auto"
    auto_restart: bool = True
    clipboard_threshold: int = 100
    max_regex_buffer_size: int = 30
    enabled: bool = True
    app_blacklist: list[str] = field(default_factory=list)
    shell_allowlist: list[str] = field(default_factory=list)
    search_shortcut: str = "CMD+SHIFT+E"
    respect_secure_input: bool = True
    undo_shortcut: str = "CMD+SHIFT+Z"
    notify_on_block: bool = True
    notify_cooldown_seconds: int = 30
    log_level: str = "INFO"
    check_updates: bool = True
    update_feed_url: str = ""


@dataclass
class Variable:
    name: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Match:
    triggers: list[str]
    replace: str
    regex: bool = False
    word_break: bool = False
    vars: list[Variable] = field(default_factory=list)
    form: list[FormField] = field(default_factory=list)
    force_clipboard: bool = False
    force_break: bool = False
    if_app: list[str] = field(default_factory=list)
    unless_app: list[str] = field(default_factory=list)
    if_bundle: list[str] = field(default_factory=list)
    unless_bundle: list[str] = field(default_factory=list)
    if_title: list[str] = field(default_factory=list)
    unless_title: list[str] = field(default_factory=list)
    priority: int = 0
    postpone: bool = False
    propagate_case: bool = False
    uppercase_style: str = ""
    trim: bool = False
    label: str = ""
    search_terms: list[str] = field(default_factory=list)
    left_word: bool = False
    right_word: bool = False
    ignore_case: bool = False
    when: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigBundle:
    app: AppConfig
    matches: list[Match]


def normalize_match(raw: dict[str, Any]) -> Match:
    triggers: list[str] = []
    if "trigger" in raw:
        triggers.append(str(raw["trigger"]))
    if "triggers" in raw:
        triggers.extend(str(item) for item in raw["triggers"])

    if not triggers:
        raise ValueError("Match must define trigger or triggers")

    replace = raw.get("replace", "")
    if not isinstance(replace, str):
        replace = str(replace)

    variables: list[Variable] = []
    for item in raw.get("vars", []) or []:
        variables.append(
            Variable(
                name=str(item["name"]),
                type=str(item.get("type", "plain")),
                params=dict(item.get("params", {}) or {}),
            )
        )

    form_fields: list[FormField] = []
    for item in raw.get("form", []) or []:
        form_fields.append(
            FormField(
                name=str(item["name"]),
                label=str(item.get("label", item["name"])),
                default=str(item.get("default", "")),
            )
        )

    return Match(
        triggers=triggers,
        replace=replace,
        regex=bool(raw.get("regex", False)),
        word_break=bool(raw.get("word_break", False)),
        vars=variables,
        form=form_fields,
        force_clipboard=bool(raw.get("force_clipboard", False)),
        force_break=bool(raw.get("force_break", False)),
        if_app=[str(item) for item in raw.get("if_app", []) or []],
        unless_app=[str(item) for item in raw.get("unless_app", []) or []],
        if_bundle=[str(item) for item in raw.get("if_bundle", []) or []],
        unless_bundle=[str(item) for item in raw.get("unless_bundle", []) or []],
        if_title=[str(item) for item in raw.get("if_title", []) or []],
        unless_title=[str(item) for item in raw.get("unless_title", []) or []],
        priority=int(raw.get("priority", 0)),
        postpone=bool(raw.get("postpone", False)),
        propagate_case=bool(raw.get("propagate_case", False)),
        uppercase_style=str(raw.get("uppercase_style", "")),
        trim=bool(raw.get("trim", False)),
        label=str(raw.get("label", "")),
        search_terms=[str(item) for item in raw.get("search_terms", []) or []],
        left_word=bool(raw.get("left_word", False)),
        right_word=bool(raw.get("right_word", False)),
        ignore_case=bool(raw.get("ignore_case", False)),
        when=dict(raw.get("when", {}) or {}),
    )


def _normalize_variables(raw_vars: list[dict[str, Any]] | None) -> list[Variable]:
    variables: list[Variable] = []
    for item in raw_vars or []:
        variables.append(
            Variable(
                name=str(item["name"]),
                type=str(item.get("type", "plain")),
                params=dict(item.get("params", {}) or {}),
            )
        )
    return variables


def _merge_global_vars(match: Match, global_vars: list[Variable]) -> Match:
    if not global_vars:
        return match
    local_names = {variable.name for variable in match.vars}
    merged = [variable for variable in global_vars if variable.name not in local_names]
    merged.extend(match.vars)
    if len(merged) == len(match.vars):
        return match
    return Match(
        triggers=match.triggers,
        replace=match.replace,
        regex=match.regex,
        word_break=match.word_break,
        vars=merged,
        form=match.form,
        force_clipboard=match.force_clipboard,
        force_break=match.force_break,
        if_app=match.if_app,
        unless_app=match.unless_app,
        if_bundle=match.if_bundle,
        unless_bundle=match.unless_bundle,
        if_title=match.if_title,
        unless_title=match.unless_title,
        priority=match.priority,
        postpone=match.postpone,
        propagate_case=match.propagate_case,
        uppercase_style=match.uppercase_style,
        trim=match.trim,
        label=match.label,
        search_terms=match.search_terms,
        left_word=match.left_word,
        right_word=match.right_word,
        ignore_case=match.ignore_case,
        when=dict(match.when),
    )


def load_app_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    return AppConfig(
        toggle_key=str(data.get("toggle_key", "ALT")),
        backend=str(data.get("backend", "auto")).lower(),
        auto_restart=bool(data.get("auto_restart", True)),
        clipboard_threshold=int(data.get("clipboard_threshold", 100)),
        max_regex_buffer_size=int(data.get("max_regex_buffer_size", 30)),
        enabled=bool(data.get("enabled", True)),
        app_blacklist=[str(item) for item in data.get("app_blacklist", []) or []],
        shell_allowlist=[str(item) for item in data.get("shell_allowlist", []) or []],
        search_shortcut=str(data.get("search_shortcut", "CMD+SHIFT+E")),
        respect_secure_input=bool(data.get("respect_secure_input", True)),
        undo_shortcut=str(data.get("undo_shortcut", "CMD+SHIFT+Z")),
        notify_on_block=bool(data.get("notify_on_block", True)),
        notify_cooldown_seconds=int(data.get("notify_cooldown_seconds", 30)),
        log_level=str(data.get("log_level", "INFO")).upper(),
        check_updates=bool(data.get("check_updates", True)),
        update_feed_url=str(data.get("update_feed_url", "") or ""),
    )


def load_matches(match_directory: Path) -> list[Match]:
    if not match_directory.exists():
        return []

    matches: list[Match] = []
    for path in sorted(match_directory.glob("*.yml")) + sorted(
        match_directory.glob("*.yaml")
    ):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        global_vars = _normalize_variables(data.get("global_vars", []) or [])
        for raw in data.get("matches", []) or []:
            match = normalize_match(raw)
            matches.append(_merge_global_vars(match, global_vars))

    from .packages import load_package_matches

    matches.extend(load_package_matches(match_directory))
    return matches


def load_config(config_dir: Path) -> ConfigBundle:
    base = load_app_config(config_dir / "config" / "default.yml")
    matches = load_matches(config_dir / "match")
    return ConfigBundle(app=base, matches=matches)


def active_bundle(
    config_dir: Path,
    bundle: ConfigBundle,
    *,
    app_name: str | None = None,
) -> ConfigBundle:
    from .profiles import resolve_app_config

    return ConfigBundle(
        app=resolve_app_config(config_dir, bundle.app, app_name=app_name),
        matches=bundle.matches,
    )


def compile_matches(
    matches: list[Match],
) -> tuple[dict[str, list[Match]], list[tuple[re.Pattern[str], Match]]]:
    conflicts = find_conflicting_literal_triggers(matches)
    if conflicts:
        raise ConfigCompileError(
            "Conflicting literal triggers (duplicate without when:): "
            + ", ".join(conflicts)
        )

    literal: dict[str, list[Match]] = {}
    regex_matches: list[tuple[re.Pattern[str], Match]] = []

    for match in matches:
        for trigger in match.triggers:
            if match.regex:
                try:
                    pattern = re.compile(trigger)
                except re.error as exc:
                    raise ConfigCompileError(
                        f"Invalid regex trigger {trigger!r}: {exc}"
                    ) from exc
                regex_matches.append((pattern, match))
            else:
                literal.setdefault(trigger, []).append(match)

    regex_matches.sort(key=lambda item: len(item[0].pattern), reverse=True)
    return literal, regex_matches
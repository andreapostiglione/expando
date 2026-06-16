from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    toggle_key: str = "ALT"
    backend: str = "auto"
    auto_restart: bool = True
    clipboard_threshold: int = 100
    max_regex_buffer_size: int = 30
    enabled: bool = True


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
    force_clipboard: bool = False
    force_break: bool = False


@dataclass
class ConfigBundle:
    app: AppConfig
    matches: list[Match]


def _normalize_match(raw: dict[str, Any]) -> Match:
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

    return Match(
        triggers=triggers,
        replace=replace,
        regex=bool(raw.get("regex", False)),
        word_break=bool(raw.get("word_break", False)),
        vars=variables,
        force_clipboard=bool(raw.get("force_clipboard", False)),
        force_break=bool(raw.get("force_break", False)),
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
        for raw in data.get("matches", []) or []:
            matches.append(_normalize_match(raw))
    return matches


def load_config(config_dir: Path) -> ConfigBundle:
    app = load_app_config(config_dir / "config" / "default.yml")
    matches = load_matches(config_dir / "match")
    return ConfigBundle(app=app, matches=matches)


def compile_matches(matches: list[Match]) -> tuple[dict[str, Match], list[tuple[re.Pattern[str], Match]]]:
    literal: dict[str, Match] = {}
    regex_matches: list[tuple[re.Pattern[str], Match]] = []

    for match in matches:
        for trigger in match.triggers:
            if match.regex:
                regex_matches.append((re.compile(trigger), match))
            else:
                literal[trigger] = match

    regex_matches.sort(key=lambda item: len(item[0].pattern), reverse=True)
    return literal, regex_matches
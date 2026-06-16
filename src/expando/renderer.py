from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Match, Variable

TEMPLATE_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

BUILTIN_ENV = {
    "USER": lambda: os.environ.get("USER", os.environ.get("USERNAME", "")),
    "HOME": lambda: str(Path.home()),
    "cwd": lambda: os.getcwd(),
}


def _resolve_env(name: str) -> str:
    if name in BUILTIN_ENV:
        return BUILTIN_ENV[name]()
    return os.environ.get(name, "")


def _resolve_variable(variable: Variable) -> str:
    if variable.type == "date":
        fmt = variable.params.get("format", "%Y-%m-%d")
        return datetime.now().strftime(fmt)

    if variable.type == "shell":
        cmd = variable.params.get("cmd", "")
        if not cmd:
            return ""
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(stderr or f"shell command failed: {cmd}")
        return result.stdout.rstrip("\n")

    if variable.type == "clipboard":
        try:
            return subprocess.check_output(["pbpaste"], text=True)
        except Exception:
            return ""

    if variable.type == "env":
        name = str(variable.params.get("name", variable.name))
        return _resolve_env(name)

    return str(variable.params.get("value", ""))


def _apply_builtin_tokens(text: str, values: dict[str, Any]) -> str:
    def replace_token(token_match: re.Match[str]) -> str:
        name = token_match.group(1)
        if name in values:
            return str(values[name])
        if name in BUILTIN_ENV:
            return _resolve_env(name)
        raise KeyError(f"Unknown template variable: {name}")

    return TEMPLATE_RE.sub(replace_token, text)


def render_match(match: Match) -> str:
    values: dict[str, Any] = {}
    for variable in match.vars:
        values[variable.name] = _resolve_variable(variable)

    return _apply_builtin_tokens(match.replace, values)
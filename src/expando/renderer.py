from __future__ import annotations

import re
import subprocess
from datetime import datetime
from typing import Any

from .config import Match, Variable

TEMPLATE_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


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
            import subprocess as sp

            return sp.check_output(["pbpaste"], text=True)
        except Exception:
            return ""

    return str(variable.params.get("value", ""))


def render_match(match: Match) -> str:
    values: dict[str, Any] = {}
    for variable in match.vars:
        values[variable.name] = _resolve_variable(variable)

    def replace_token(token_match: re.Match[str]) -> str:
        name = token_match.group(1)
        if name not in values:
            raise KeyError(f"Unknown template variable: {name}")
        return str(values[name])

    return TEMPLATE_RE.sub(replace_token, match.replace)
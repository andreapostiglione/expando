from __future__ import annotations

import os
import random
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from pathlib import Path

from .config import AppConfig, Match, Variable
from .forms import collect_form_values
from .render_context import RenderContext
from .text_transform import decode_unicode_escapes

TEMPLATE_RE = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
SHELL_CHAIN_RE = re.compile(r"[;|&`$()<>]")


def _resolve_env(name: str) -> str:
    if name in BUILTIN_ENV:
        return BUILTIN_ENV[name]()
    return os.environ.get(name, "")


BUILTIN_ENV = {
    "USER": lambda: os.environ.get("USER", os.environ.get("USERNAME", "")),
    "HOME": lambda: str(Path.home()),
    "cwd": lambda: os.getcwd(),
}


def _shell_executable(cmd: str) -> str:
    stripped = cmd.strip()
    if not stripped:
        return ""
    try:
        parts = shlex.split(stripped)
    except ValueError:
        return ""
    return parts[0] if parts else ""


def _shell_allowed(cmd: str, allowlist: list[str]) -> bool:
    if not allowlist:
        return False
    if SHELL_CHAIN_RE.search(cmd):
        return False
    executable = _shell_executable(cmd)
    if not executable:
        return False
    executable_name = Path(executable).name.casefold()
    return any(
        executable_name == prefix.casefold() or executable.casefold() == prefix.casefold()
        for prefix in allowlist
    )


def _resolve_variable(
    variable: Variable,
    app_config: AppConfig | None = None,
    *,
    render_context: RenderContext | None = None,
) -> str:
    if variable.type == "date":
        fmt = variable.params.get("format", "%Y-%m-%d")
        return datetime.now().strftime(fmt)

    if variable.type == "shell":
        cmd = variable.params.get("cmd", "")
        if not cmd:
            return ""
        allowlist = app_config.shell_allowlist if app_config else []
        if not _shell_allowed(cmd, allowlist):
            raise RuntimeError(f"Shell command not allowed: {cmd}")
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

    if variable.type == "random":
        choices = variable.params.get("choices", []) or []
        if not choices:
            return ""
        return str(random.choice(choices))

    if variable.type == "unicode":
        value = str(variable.params.get("value", ""))
        return decode_unicode_escapes(value)

    if variable.type == "script":
        script_path = str(variable.params.get("path", "")).strip()
        if not script_path:
            raise RuntimeError("Script variable requires params.path")
        if render_context is None or not render_context.config_dir:
            raise RuntimeError("Script variable requires an active config directory")
        from .plugins import resolve_plugin_script, run_plugin_script

        resolved = resolve_plugin_script(Path(render_context.config_dir), script_path)
        return run_plugin_script(resolved, render_context)

    if variable.type in {"plain", "echo"}:
        return str(variable.params.get("value", ""))

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


def render_match(
    match: Match,
    app_config: AppConfig | None = None,
    extra_values: dict[str, str] | None = None,
    *,
    render_context: RenderContext | None = None,
) -> str:
    values: dict[str, Any] = dict(extra_values or {})
    for variable in match.vars:
        values[variable.name] = _resolve_variable(
            variable,
            app_config=app_config,
            render_context=render_context,
        )
    rendered = _apply_builtin_tokens(match.replace, values)
    return decode_unicode_escapes(rendered)


def render_match_interactive(
    match: Match,
    app_config: AppConfig | None = None,
    *,
    render_context: RenderContext | None = None,
) -> str | None:
    context = render_context or RenderContext()
    if match.form:
        collected = collect_form_values(match.form)
        if collected is None:
            return None
        context.form_values.update(collected)
    return render_match(
        match,
        app_config=app_config,
        extra_values=context.form_values,
        render_context=context,
    )
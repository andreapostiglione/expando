from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class FormField:
    name: str
    label: str
    default: str = ""


def _escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def prompt_field(field: FormField) -> str | None:
    script = f'''
        set theResponse to display dialog "{_escape_applescript(field.label)}" default answer "{_escape_applescript(field.default)}"
        return text returned of theResponse
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def collect_form_values(fields: list[FormField]) -> dict[str, str] | None:
    values: dict[str, str] = {}
    for field in fields:
        value = prompt_field(field)
        if value is None:
            return None
        values[field.name] = value
    return values
from __future__ import annotations

from dataclasses import dataclass

from .ui_bridge import show_form_dialog


@dataclass
class FormField:
    name: str
    label: str
    default: str = ""


def collect_form_values(fields: list[FormField]) -> dict[str, str] | None:
    if not fields:
        return {}

    payload = [
        {
            "name": field.name,
            "label": field.label,
            "default": field.default,
        }
        for field in fields
    ]
    result = show_form_dialog(payload)
    if result is None:
        return None
    return {field.name: result.get(field.name, field.default) for field in fields}
from __future__ import annotations

from pathlib import Path

from .snippet_editor_data import (
    create_snippet_entry,
    delete_snippet_entry,
    entries_for_editor,
    parse_form_from_editor,
    parse_vars_from_editor,
    update_snippet_entry,
)
from .snippet_editor_ui import run_snippet_editor


def _parse_if_app(value: str) -> list[str] | None:
    apps = [part.strip() for part in value.split(",") if part.strip()]
    return apps or None


def _parse_editor_payload(payload: dict[str, str]) -> tuple[list | None, list | None]:
    try:
        form = parse_form_from_editor(payload.get("form", ""))
        variables = parse_vars_from_editor(payload.get("vars", ""))
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return form or None, variables or None


def open_snippet_editor(config_dir: Path) -> dict[str, str] | None:
    def reload() -> list[dict[str, str]]:
        return entries_for_editor(config_dir)

    def on_save(payload: dict[str, str]) -> str | None:
        try:
            form, variables = _parse_editor_payload(payload)
            update_snippet_entry(
                config_dir,
                payload["id"],
                trigger=payload["trigger"],
                replace=payload["replace"],
                if_app=_parse_if_app(payload.get("if_app", "")),
                form=form,
                variables=variables,
            )
        except ValueError as exc:
            return str(exc)
        return None

    def on_create(payload: dict[str, str]) -> str | None:
        try:
            form, variables = _parse_editor_payload(payload)
            create_snippet_entry(
                config_dir,
                payload["trigger"],
                payload["replace"],
                if_app=_parse_if_app(payload.get("if_app", "")),
                form=form,
                variables=variables,
            )
        except ValueError as exc:
            return str(exc)
        return None

    def on_delete(entry_id: str) -> str | None:
        try:
            delete_snippet_entry(config_dir, entry_id)
        except ValueError as exc:
            return str(exc)
        return None

    return run_snippet_editor(
        reload(),
        on_save=on_save,
        on_create=on_create,
        on_delete=on_delete,
        reload_items=reload,
    )
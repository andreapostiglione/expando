from __future__ import annotations

from pathlib import Path

from .snippet_editor_data import (
    _parse_csv_field,
    _parse_when_field,
    create_snippet_entry,
    delete_snippet_entry,
    duplicate_snippet_entry,
    entries_for_editor,
    list_match_files,
    move_snippet_entry,
    parse_form_from_editor,
    parse_vars_from_editor,
    update_snippet_entry,
)
from .snippet_editor_ui import run_snippet_editor


def _parse_editor_payload(payload: dict[str, str]) -> dict:
    try:
        form = parse_form_from_editor(payload.get("form", ""))
        variables = parse_vars_from_editor(payload.get("vars", ""))
        when = _parse_when_field(payload.get("when", ""))
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    priority_raw = payload.get("priority", "").strip()
    priority = int(priority_raw) if priority_raw else 0
    return {
        "if_app": _parse_csv_field(payload.get("if_app", "")),
        "unless_app": _parse_csv_field(payload.get("unless_app", "")),
        "if_bundle": _parse_csv_field(payload.get("if_bundle", "")),
        "unless_bundle": _parse_csv_field(payload.get("unless_bundle", "")),
        "if_title": _parse_csv_field(payload.get("if_title", "")),
        "unless_title": _parse_csv_field(payload.get("unless_title", "")),
        "form": form or None,
        "variables": variables or None,
        "regex": payload.get("regex", "").strip() in {"1", "true", "yes"},
        "when": when,
        "image": payload.get("image", "").strip(),
        "priority": priority,
        "force_clipboard": payload.get("force_clipboard", "").strip() in {"1", "true", "yes"},
        "target_file": payload.get("target_file", "").strip() or "dev.yml",
    }


def open_snippet_editor(config_dir: Path) -> dict[str, str] | None:
    match_files = list_match_files(config_dir)

    def reload() -> list[dict[str, str]]:
        rows = entries_for_editor(config_dir)
        for row in rows:
            row["target_file"] = row.get("source_file", "dev.yml")
        return rows

    def on_save(payload: dict[str, str]) -> str | None:
        try:
            parsed = _parse_editor_payload(payload)
            update_snippet_entry(
                config_dir,
                payload["id"],
                trigger=payload["trigger"],
                replace=payload["replace"],
                **{key: parsed[key] for key in parsed if key not in {"target_file", "variables"}},
                variables=parsed["variables"],
            )
        except ValueError as exc:
            return str(exc)
        return None

    def on_create(payload: dict[str, str]) -> str | None:
        try:
            parsed = _parse_editor_payload(payload)
            create_snippet_entry(
                config_dir,
                payload["trigger"],
                payload["replace"],
                target_file=parsed["target_file"],
                **{key: parsed[key] for key in parsed if key not in {"target_file", "variables"}},
                variables=parsed["variables"],
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

    def on_duplicate(entry_id: str, target_file: str) -> str | None:
        try:
            duplicate_snippet_entry(config_dir, entry_id, target_file=target_file)
        except ValueError as exc:
            return str(exc)
        return None

    def on_move(entry_id: str, target_file: str) -> str | None:
        try:
            move_snippet_entry(config_dir, entry_id, target_file=target_file)
        except ValueError as exc:
            return str(exc)
        return None

    initial = reload()
    for row in initial:
        row.setdefault("target_file", row.get("source_file", match_files[0]))
        row["match_files"] = ",".join(match_files)
    return run_snippet_editor(
        initial,
        on_save=on_save,
        on_create=on_create,
        on_delete=on_delete,
        on_duplicate=on_duplicate,
        on_move=on_move,
        reload_items=reload,
        match_files=match_files,
        config_dir=config_dir,
    )
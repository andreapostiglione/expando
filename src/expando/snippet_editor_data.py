from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import Match, normalize_match
from .match_utils import extract_triggers


@dataclass(frozen=True)
class SnippetEntry:
    entry_id: str
    source_file: str
    index: int
    match: Match
    editable: bool = True


def _match_path(config_dir: Path, source_file: str) -> Path:
    return config_dir / "match" / source_file


def list_snippet_entries(config_dir: Path) -> list[SnippetEntry]:
    entries: list[SnippetEntry] = []
    directory = config_dir / "match"
    if not directory.exists():
        return entries

    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for index, raw in enumerate(data.get("matches", []) or []):
            match = normalize_match(raw)
            entries.append(
                SnippetEntry(
                    entry_id=f"{path.name}:{index}",
                    source_file=path.name,
                    index=index,
                    match=match,
                    editable=True,
                )
            )

    from .packages import load_package_matches

    for pkg_index, match in enumerate(load_package_matches(directory)):
        entries.append(
            SnippetEntry(
                entry_id=f"packages:{pkg_index}",
                source_file="packages",
                index=pkg_index,
                match=match,
                editable=False,
            )
        )
    return entries


def _load_match_file(path: Path) -> dict:
    if not path.exists():
        return {"matches": []}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {"matches": []}


def _write_match_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)


def _parse_entry_id(entry_id: str) -> tuple[str, int]:
    if ":" not in entry_id:
        raise ValueError(f"Invalid snippet id: {entry_id}")
    source_file, raw_index = entry_id.rsplit(":", 1)
    if source_file == "packages":
        raise ValueError("Hub packages cannot be edited from the snippet editor")
    return source_file, int(raw_index)


def _build_entry_dict(
    trigger: str,
    replace: str,
    *,
    if_app: list[str] | None = None,
) -> dict:
    entry: dict = {"trigger": trigger, "replace": replace}
    if if_app:
        entry["if_app"] = if_app
    return entry


def create_snippet_entry(
    config_dir: Path,
    trigger: str,
    replace: str,
    *,
    target_file: str = "dev.yml",
    if_app: list[str] | None = None,
) -> SnippetEntry:
    path = _match_path(config_dir, target_file)
    data = _load_match_file(path)
    matches = list(data.get("matches", []) or [])
    for item in matches:
        if trigger in extract_triggers(item):
            raise ValueError(f"Trigger already exists in {target_file}: {trigger}")
    matches.append(_build_entry_dict(trigger, replace, if_app=if_app))
    data["matches"] = matches
    _write_match_file(path, data)
    index = len(matches) - 1
    return SnippetEntry(
        entry_id=f"{target_file}:{index}",
        source_file=target_file,
        index=index,
        match=normalize_match(matches[index]),
        editable=True,
    )


def update_snippet_entry(
    config_dir: Path,
    entry_id: str,
    *,
    trigger: str,
    replace: str,
    if_app: list[str] | None = None,
) -> SnippetEntry:
    source_file, index = _parse_entry_id(entry_id)
    path = _match_path(config_dir, source_file)
    data = _load_match_file(path)
    matches = list(data.get("matches", []) or [])
    if index < 0 or index >= len(matches):
        raise ValueError(f"Snippet not found: {entry_id}")

    for other_index, item in enumerate(matches):
        if other_index == index:
            continue
        if trigger in extract_triggers(item):
            raise ValueError(f"Trigger already exists in {source_file}: {trigger}")

    matches[index] = _build_entry_dict(trigger, replace, if_app=if_app)
    data["matches"] = matches
    _write_match_file(path, data)
    return SnippetEntry(
        entry_id=entry_id,
        source_file=source_file,
        index=index,
        match=normalize_match(matches[index]),
        editable=True,
    )


def delete_snippet_entry(config_dir: Path, entry_id: str) -> None:
    source_file, index = _parse_entry_id(entry_id)
    path = _match_path(config_dir, source_file)
    data = _load_match_file(path)
    matches = list(data.get("matches", []) or [])
    if index < 0 or index >= len(matches):
        raise ValueError(f"Snippet not found: {entry_id}")
    del matches[index]
    data["matches"] = matches
    _write_match_file(path, data)


def entries_for_editor(config_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in list_snippet_entries(config_dir):
        trigger = entry.match.triggers[0] if entry.match.triggers else ""
        preview = " ".join(entry.match.replace.split())
        if len(preview) > 80:
            preview = preview[:79] + "…"
        scope = ""
        if entry.match.if_app:
            scope = f" [{', '.join(entry.match.if_app)}]"
        rows.append(
            {
                "id": entry.entry_id,
                "trigger": trigger,
                "label": f"{trigger} ({entry.source_file}){scope}",
                "preview": entry.match.replace,
                "replace": entry.match.replace,
                "if_app": ", ".join(entry.match.if_app),
                "editable": "1" if entry.editable else "0",
                "source_file": entry.source_file,
            }
        )
    return rows
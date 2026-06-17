from __future__ import annotations

import csv
import plistlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXCLUDED_TE_GROUPS = frozenset({"Suggested Snippets"})


@dataclass
class TextExpanderSnippet:
    abbreviation: str
    text: str
    label: str = ""
    group: str = ""
    snippet_type: int = 0


def textexpander_source_candidates() -> list[Path]:
    home = Path.home()
    return [
        home / "Library" / "Application Support" / "TextExpander" / "Settings.textexpander",
        home / "Library" / "Group Containers" / "5ZSL2CJU2T.com.smileonmymac.textexpander" / "Settings.textexpander",
    ]


def find_textexpander_source(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        path = explicit.expanduser()
        return path if path.exists() else None
    for candidate in textexpander_source_candidates():
        if candidate.exists():
            return candidate
    return None


def detect_textexpander_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".textexpander", ".plist"}:
        return "plist"
    if path.is_dir():
        return "directory"
    try:
        with path.open("rb") as handle:
            header = handle.read(8)
        if header.startswith(b"bplist") or header.startswith(b"<?xml"):
            return "plist"
    except OSError:
        pass
    return "csv"


def _csv_field_limit() -> int:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return limit
        except OverflowError:
            limit = int(limit / 10)


def _normalize_header(value: str) -> str:
    return value.lstrip("\ufeff").strip().lower()


def parse_textexpander_csv(path: Path) -> list[TextExpanderSnippet]:
    _csv_field_limit()
    snippets: list[TextExpanderSnippet] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        return snippets

    header = [_normalize_header(cell) for cell in rows[0]]
    has_header = "abbreviation" in header and "snippet" in header
    start = 1 if has_header else 0

    abbr_idx = header.index("abbreviation") if has_header else 0
    snippet_idx = header.index("snippet") if has_header else 1
    label_idx = header.index("label") if has_header and "label" in header else None

    group = path.stem
    for row in rows[start:]:
        if len(row) <= snippet_idx:
            continue
        abbreviation = row[abbr_idx].strip()
        text = row[snippet_idx]
        if not abbreviation:
            continue
        label = row[label_idx].strip() if label_idx is not None and len(row) > label_idx else ""
        snippets.append(
            TextExpanderSnippet(
                abbreviation=abbreviation,
                text=text,
                label=label,
                group=group,
            )
        )
    return snippets


def parse_textexpander_plist(path: Path) -> list[TextExpanderSnippet]:
    with path.open("rb") as handle:
        data = plistlib.load(handle)

    all_snippets = list(data.get("snippetsTE2") or [])
    all_groups = list(data.get("groupsTE2") or [])

    uuid_to_group: dict[str, str] = {}
    excluded_uuids: set[str] = set()
    for group in all_groups:
        group_name = str(group.get("name") or "Ungrouped")
        uuids = [str(item) for item in (group.get("snippetUUIDs") or [])]
        if group_name in EXCLUDED_TE_GROUPS:
            excluded_uuids.update(uuids)
            continue
        for uuid in uuids:
            uuid_to_group[uuid] = group_name

    snippets: list[TextExpanderSnippet] = []
    for raw in all_snippets:
        uuid = str(raw.get("uuidString") or "")
        if uuid and uuid in excluded_uuids:
            continue
        abbreviation = str(raw.get("abbreviation") or "").strip()
        text = str(raw.get("plainText") or "")
        label = str(raw.get("label") or "").strip()
        snippet_type = int(raw.get("snippetType") or 0)
        group_name = uuid_to_group.get(uuid, "Ungrouped")
        snippets.append(
            TextExpanderSnippet(
                abbreviation=abbreviation,
                text=text,
                label=label,
                group=group_name,
                snippet_type=snippet_type,
            )
        )
    return snippets


def load_textexpander_snippets(path: Path) -> list[TextExpanderSnippet]:
    fmt = detect_textexpander_format(path)
    if fmt == "plist":
        return parse_textexpander_plist(path)
    if fmt == "directory":
        snippets: list[TextExpanderSnippet] = []
        for csv_path in sorted(path.glob("*.csv")):
            snippets.extend(parse_textexpander_csv(csv_path))
        return snippets
    return parse_textexpander_csv(path)


def convert_textexpander_snippet(snippet: TextExpanderSnippet) -> dict[str, Any] | None:
    trigger = snippet.abbreviation.strip()
    if not trigger:
        return None

    converted: dict[str, Any] = {
        "trigger": trigger,
        "replace": snippet.text,
    }

    label = snippet.label.strip()
    if not label:
        label = trigger
    if snippet.group and snippet.group != "Ungrouped":
        label = f"[{snippet.group}] {label}"
    converted["label"] = label

    if snippet.snippet_type in {2, 3}:
        converted["label"] = f"{converted['label']} (script)"
    return converted
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from .config import Match, load_matches


def list_matches(config_dir: Path) -> list[tuple[Match, str]]:
    results: list[tuple[Match, str]] = []
    directory = config_dir / "match"
    if not directory.exists():
        return results

    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for raw in data.get("matches", []) or []:
            triggers = []
            if "trigger" in raw:
                triggers.append(str(raw["trigger"]))
            if "triggers" in raw:
                triggers.extend(str(item) for item in raw["triggers"])
            for trigger in triggers:
                results.append((_match_from_raw(raw, trigger), path.name))

    from .packages import load_package_matches

    for match in load_package_matches(directory):
        for trigger in match.triggers:
            results.append((match, "packages"))
    return results


def _match_from_raw(raw: dict, trigger: str) -> Match:
    return Match(
        triggers=[trigger],
        replace=str(raw.get("replace", "")),
        regex=bool(raw.get("regex", False)),
        word_break=bool(raw.get("word_break", False)),
        if_app=[str(item) for item in raw.get("if_app", []) or []],
        unless_app=[str(item) for item in raw.get("unless_app", []) or []],
    )


def _preview(text: str, limit: int = 60) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def format_match_list(config_dir: Path) -> str:
    rows = list_matches(config_dir)
    if not rows:
        return "No snippets configured."

    lines: list[str] = []
    for match, source in rows:
        trigger = match.triggers[0]
        preview = _preview(match.replace)
        scope = ""
        if match.if_app:
            scope = f" [{', '.join(match.if_app)} only]"
        elif match.unless_app:
            scope = f" [except {', '.join(match.unless_app)}]"
        lines.append(f"{trigger:20} {preview:40} ({source}){scope}")
    return "\n".join(lines)


def append_match(
    config_dir: Path,
    trigger: str,
    replace: str,
    *,
    target_file: str = "dev.yml",
    if_app: list[str] | None = None,
    unless_app: list[str] | None = None,
) -> Path:
    path = config_dir / "match" / target_file
    path.parent.mkdir(parents=True, exist_ok=True)

    entry: dict = {"trigger": trigger, "replace": replace}
    if if_app:
        entry["if_app"] = if_app
    if unless_app:
        entry["unless_app"] = unless_app

    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        matches = list(data.get("matches", []) or [])
        for item in matches:
            existing = []
            if "trigger" in item:
                existing.append(str(item["trigger"]))
            if "triggers" in item:
                existing.extend(str(value) for value in item["triggers"])
            if trigger in existing:
                raise ValueError(f"Trigger already exists in {path.name}: {trigger}")
        matches.append(entry)
        data["matches"] = matches
    else:
        data = {"matches": [entry]}

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
    return path


def import_matches(config_dir: Path, source: Path) -> list[str]:
    destination_dir = config_dir / "match"
    destination_dir.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []

    if source.is_file():
        if source.suffix not in {".yml", ".yaml"}:
            raise ValueError("Import source must be a .yml or .yaml file")
        target = destination_dir / source.name
        shutil.copy2(source, target)
        imported.append(target.name)
        return imported

    if not source.is_dir():
        raise ValueError(f"Import source not found: {source}")

    for path in sorted(source.glob("*.yml")) + sorted(source.glob("*.yaml")):
        target = destination_dir / path.name
        shutil.copy2(path, target)
        imported.append(target.name)

    if not imported:
        raise ValueError(f"No YAML match files found in {source}")

    return imported
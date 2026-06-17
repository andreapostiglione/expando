from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from .config import Match, normalize_match
from .match_utils import extract_triggers


def list_matches(config_dir: Path) -> list[tuple[Match, str]]:
    results: list[tuple[Match, str]] = []
    directory = config_dir / "match"
    if not directory.exists():
        return results

    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for raw in data.get("matches", []) or []:
            match = normalize_match(raw)
            for trigger in match.triggers:
                single = Match(
                    triggers=[trigger],
                    replace=match.replace,
                    regex=match.regex,
                    word_break=match.word_break,
                    vars=match.vars,
                    form=match.form,
                    force_clipboard=match.force_clipboard,
                    force_break=match.force_break,
                    if_app=match.if_app,
                    unless_app=match.unless_app,
                    if_bundle=match.if_bundle,
                    unless_bundle=match.unless_bundle,
                    if_title=match.if_title,
                    unless_title=match.unless_title,
                )
                results.append((single, path.name))

    from .packages import load_package_matches

    for match in load_package_matches(directory):
        for trigger in match.triggers:
            single = Match(
                triggers=[trigger],
                replace=match.replace,
                regex=match.regex,
                word_break=match.word_break,
                vars=match.vars,
                form=match.form,
                force_clipboard=match.force_clipboard,
                force_break=match.force_break,
                if_app=match.if_app,
                unless_app=match.unless_app,
                if_bundle=match.if_bundle,
                unless_bundle=match.unless_bundle,
                if_title=match.if_title,
                unless_title=match.unless_title,
            )
            results.append((single, "packages"))
    return results


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
        if match.if_bundle:
            scope += f" [bundle: {', '.join(match.if_bundle)}]"
        if match.if_title:
            scope += f" [title: {', '.join(match.if_title)}]"
        lines.append(f"{trigger:20} {preview:40} ({source}){scope}")
    return "\n".join(lines)


def append_match_entry(
    config_dir: Path,
    entry: dict,
    *,
    target_file: str = "dev.yml",
) -> Path:
    path = config_dir / "match" / target_file
    path.parent.mkdir(parents=True, exist_ok=True)

    triggers = extract_triggers(entry)
    if not triggers:
        raise ValueError("Match entry must define trigger or triggers")

    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        matches = list(data.get("matches", []) or [])
        for item in matches:
            for trigger in triggers:
                if trigger in extract_triggers(item):
                    raise ValueError(f"Trigger already exists in {path.name}: {trigger}")
        matches.append(entry)
        data["matches"] = matches
    else:
        data = {"matches": [entry]}

    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=True, sort_keys=False)
    return path


def append_match(
    config_dir: Path,
    trigger: str,
    replace: str,
    *,
    target_file: str = "dev.yml",
    if_app: list[str] | None = None,
    unless_app: list[str] | None = None,
) -> Path:
    entry: dict = {"trigger": trigger, "replace": replace}
    if if_app:
        entry["if_app"] = if_app
    if unless_app:
        entry["unless_app"] = unless_app
    return append_match_entry(config_dir, entry, target_file=target_file)


def import_matches(config_dir: Path, source: Path, *, force: bool = False) -> list[str]:
    destination_dir = config_dir / "match"
    destination_dir.mkdir(parents=True, exist_ok=True)
    imported: list[str] = []

    def _copy(path: Path) -> None:
        target = destination_dir / path.name
        if target.exists() and not force:
            raise ValueError(f"File already exists: {target.name} (use --force to overwrite)")
        shutil.copy2(path, target)
        imported.append(target.name)

    if source.is_file():
        if source.suffix not in {".yml", ".yaml"}:
            raise ValueError("Import source must be a .yml or .yaml file")
        _copy(source)
        return imported

    if not source.is_dir():
        raise ValueError(f"Import source not found: {source}")

    for path in sorted(source.glob("*.yml")) + sorted(source.glob("*.yaml")):
        _copy(path)

    if not imported:
        raise ValueError(f"No YAML match files found in {source}")

    return imported
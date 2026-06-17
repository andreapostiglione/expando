from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from .backup import backup_config
from .raycast_compat import convert_raycast_snippet, load_raycast_snippets
from .textexpander_compat import (
    convert_textexpander_snippet,
    find_textexpander_source,
    load_textexpander_snippets,
)


@dataclass
class ExternalImportReport:
    source: Path
    provider: str
    match_files: list[str] = field(default_factory=list)
    matches_imported: int = 0
    matches_skipped: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExternalMigrateReport:
    backup_path: Path
    import_report: ExternalImportReport


def _target_name(provider: str, source: Path) -> str:
    stem = source.stem.lower().replace(" ", "-")
    if stem in {"settings", "snippets"}:
        stem = provider
    return f"{provider}-{stem}.yml"


def _write_match_file(
    destination: Path,
    *,
    provider: str,
    source: Path,
    matches: list[dict[str, Any]],
    force: bool,
    report: ExternalImportReport,
) -> None:
    target = destination / "match" / _target_name(provider, source)
    if target.exists() and not force:
        report.warnings.append(f"Skipped existing file: {target.name}")
        report.matches_skipped += len(matches)
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"matches": matches}, handle, allow_unicode=True, sort_keys=False)
    report.match_files.append(str(target.relative_to(destination)))
    report.matches_imported += len(matches)


def _import_converted_matches(
    destination: Path,
    *,
    provider: str,
    source: Path,
    raw_snippets: list[Any],
    convert: Callable[[Any], dict[str, Any] | None],
    force: bool,
    extra_warnings: list[str] | None = None,
) -> ExternalImportReport:
    report = ExternalImportReport(source=source, provider=provider)
    if extra_warnings:
        report.warnings.extend(extra_warnings)

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "match").mkdir(parents=True, exist_ok=True)

    matches: list[dict[str, Any]] = []
    for raw in raw_snippets:
        converted = convert(raw)
        if converted is None:
            report.matches_skipped += 1
            continue
        matches.append(converted)

    if not matches and report.matches_skipped:
        report.warnings.append("No snippets with triggers/keywords were importable")
    elif matches:
        _write_match_file(
            destination,
            provider=provider,
            source=source,
            matches=matches,
            force=force,
            report=report,
        )
    return report


def import_textexpander_snippets(
    destination: Path,
    *,
    source: Path | None = None,
    force: bool = False,
) -> ExternalImportReport:
    te_source = find_textexpander_source(source)
    if te_source is None:
        raise FileNotFoundError(
            "TextExpander data not found. Pass --source with a CSV or Settings.textexpander file."
        )

    raw = load_textexpander_snippets(te_source)
    warnings: list[str] = []
    rich = sum(1 for item in raw if item.snippet_type == 1)
    scripts = sum(1 for item in raw if item.snippet_type in {2, 3})
    no_trigger = sum(1 for item in raw if not item.abbreviation.strip())
    if rich:
        warnings.append(f"{rich} rich-text snippet(s): formatting not preserved (plain text only)")
    if scripts:
        warnings.append(f"{scripts} script snippet(s): exported as plain text (no auto-execution)")
    if no_trigger:
        warnings.append(f"{no_trigger} snippet(s) without abbreviation skipped")

    return _import_converted_matches(
        destination,
        provider="textexpander",
        source=te_source,
        raw_snippets=raw,
        convert=convert_textexpander_snippet,
        force=force,
        extra_warnings=warnings,
    )


def import_raycast_snippets(
    destination: Path,
    *,
    source: Path,
    force: bool = False,
) -> ExternalImportReport:
    path = source.expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Raycast export not found: {path}")

    raw = load_raycast_snippets(path)
    no_keyword = sum(1 for item in raw if not item.keyword.strip())
    warnings: list[str] = []
    if no_keyword:
        warnings.append(
            f"{no_keyword} snippet(s) without keyword skipped (Raycast search-only snippets)"
        )

    return _import_converted_matches(
        destination,
        provider="raycast",
        source=path,
        raw_snippets=raw,
        convert=convert_raycast_snippet,
        force=force,
        extra_warnings=warnings,
    )


def migrate_textexpander_snippets(
    config_dir: Path,
    *,
    source: Path | None = None,
    force: bool = False,
) -> ExternalMigrateReport:
    backup_path = backup_config(config_dir)
    import_report = import_textexpander_snippets(
        config_dir,
        source=source,
        force=force,
    )
    return ExternalMigrateReport(backup_path=backup_path, import_report=import_report)


def migrate_raycast_snippets(
    config_dir: Path,
    *,
    source: Path,
    force: bool = False,
) -> ExternalMigrateReport:
    backup_path = backup_config(config_dir)
    import_report = import_raycast_snippets(
        config_dir,
        source=source,
        force=force,
    )
    return ExternalMigrateReport(backup_path=backup_path, import_report=import_report)
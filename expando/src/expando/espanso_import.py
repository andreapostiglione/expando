from __future__ import annotations

# AC1 cleanup (this round): removed unused import for shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .espanso_compat import (
    convert_espanso_app_config,
    convert_espanso_match,
    find_espanso_config,
)


@dataclass
class EspansoImportReport:
    source: Path
    match_files: list[str] = field(default_factory=list)
    matches_imported: int = 0
    matches_skipped: int = 0
    config_merged: bool = False
    warnings: list[str] = field(default_factory=list)


def import_espanso_config(
    destination: Path,
    *,
    source: Path | None = None,
    force: bool = False,
) -> EspansoImportReport:
    espanso_dir = find_espanso_config(source)
    if espanso_dir is None:
        raise FileNotFoundError(
            "Espanso config not found. Pass --source or install Espanso first."
        )

    report = EspansoImportReport(source=espanso_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "config").mkdir(parents=True, exist_ok=True)
    (destination / "match").mkdir(parents=True, exist_ok=True)

    default_src = espanso_dir / "config" / "default.yml"
    default_dst = destination / "config" / "default.yml"
    if default_src.exists():
        with default_src.open("r", encoding="utf-8") as handle:
            espanso_default = yaml.safe_load(handle) or {}
        converted = convert_espanso_app_config(espanso_default)
        if converted:
            if default_dst.exists() and not force:
                with default_dst.open("r", encoding="utf-8") as handle:
                    existing = yaml.safe_load(handle) or {}
                existing.update(converted)
                converted = existing
            with default_dst.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(converted, handle, allow_unicode=True, sort_keys=False)
            report.config_merged = True

    match_src = espanso_dir / "match"
    if match_src.exists():
        for path in sorted(match_src.rglob("*.yml")) + sorted(match_src.rglob("*.yaml")):
            relative = path.relative_to(match_src)
            if relative.parts[0] == "packages":
                target = destination / "match" / "packages" / Path(*relative.parts[1:])
            else:
                target = destination / "match" / f"espanso-{relative.name}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and not force:
                report.warnings.append(f"Skipped existing file: {target.name}")
                continue
            imported = _convert_match_file(path, destination)
            report.match_files.append(str(target.relative_to(destination)))
            report.matches_imported += imported["imported"]
            report.matches_skipped += imported["skipped"]
            with target.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(imported["data"], handle, allow_unicode=True, sort_keys=False)

    user_src = espanso_dir / "match" / "user" if (espanso_dir / "match" / "user").exists() else None
    if user_src:
        for path in sorted(user_src.glob("*.yml")) + sorted(user_src.glob("*.yaml")):
            target = destination / "match" / f"espanso-user-{path.name}"
            if target.exists() and not force:
                continue
            imported = _convert_match_file(path, destination)
            report.match_files.append(str(target.relative_to(destination)))
            report.matches_imported += imported["imported"]
            report.matches_skipped += imported["skipped"]
            with target.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(imported["data"], handle, allow_unicode=True, sort_keys=False)

    return report


def _convert_match_file(path: Path, config_dir: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    global_vars = data.get("global_vars", []) or []
    converted_globals: list[dict] = []
    for item in global_vars:
        var = dict(item)
        if var.get("type") == "echo":
            var["type"] = "plain"
            params = dict(var.get("params", {}) or {})
            if "echo" in params:
                params["value"] = params.pop("echo")
            var["params"] = params
        converted_globals.append(var)

    matches: list[dict] = []
    skipped = 0
    for raw in data.get("matches", []) or []:
        converted = convert_espanso_match(raw, config_dir=config_dir)
        if converted is None:
            skipped += 1
            continue
        matches.append(converted)

    output: dict = {"matches": matches}
    if converted_globals:
        output["global_vars"] = converted_globals
    return {"data": output, "imported": len(matches), "skipped": skipped}
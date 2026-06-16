from __future__ import annotations

from pathlib import Path

import yaml

from .config import Match, _merge_global_vars, _normalize_variables, normalize_match


def load_package_matches(match_directory: Path) -> list[Match]:
    packages_dir = match_directory / "packages"
    if not packages_dir.exists():
        return []

    matches: list[Match] = []
    for path in sorted(packages_dir.rglob("*.yml")) + sorted(packages_dir.rglob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        global_vars = _normalize_variables(data.get("global_vars", []) or [])
        for raw in data.get("matches", []) or []:
            match = normalize_match(raw)
            matches.append(_merge_global_vars(match, global_vars))
    return matches


def list_installed_packages(match_directory: Path) -> list[str]:
    packages_dir = match_directory / "packages"
    if not packages_dir.exists():
        return []
    return sorted(
        {
            child.name
            for child in packages_dir.iterdir()
            if child.is_dir() and any(child.glob("*.y*ml"))
        }
    )
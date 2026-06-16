from __future__ import annotations

from pathlib import Path

import yaml

from .config import Match, normalize_match


def load_package_matches(match_directory: Path) -> list[Match]:
    packages_dir = match_directory / "packages"
    if not packages_dir.exists():
        return []

    matches: list[Match] = []
    for path in sorted(packages_dir.rglob("*.yml")) + sorted(packages_dir.rglob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for raw in data.get("matches", []) or []:
            matches.append(normalize_match(raw))
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
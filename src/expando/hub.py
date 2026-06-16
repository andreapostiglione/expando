from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .paths import match_dir, package_root


DEFAULT_INDEX_URL = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/packages/hub/index.json"
)
DEFAULT_FILES_BASE = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/default_config/match/packages"
)


@dataclass
class HubPackage:
    id: str
    name: str
    description: str
    author: str = ""
    tags: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HubPackage:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            tags=[str(item) for item in data.get("tags", []) or []],
        )


def _index_url() -> str:
    return os.environ.get("EXPANDO_HUB_INDEX_URL", DEFAULT_INDEX_URL)


def _files_base() -> str:
    return os.environ.get("EXPANDO_HUB_FILES_BASE", DEFAULT_FILES_BASE)


def _local_index_path() -> Path:
    return package_root() / "packages" / "hub" / "index.json"


def _local_package_dir(package_id: str) -> Path:
    return package_root() / "default_config" / "match" / "packages" / package_id


def fetch_registry() -> list[HubPackage]:
    local_index = _local_index_path()
    if local_index.exists():
        data = json.loads(local_index.read_text(encoding="utf-8"))
        return [HubPackage.from_dict(item) for item in data.get("packages", []) or []]

    try:
        with urlopen(_index_url(), timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Could not fetch package hub index: {exc}") from exc

    return [HubPackage.from_dict(item) for item in data.get("packages", []) or []]


def search_hub_packages(query: str) -> list[HubPackage]:
    packages = fetch_registry()
    if not query.strip():
        return packages

    from .fuzzy import fuzzy_score

    results: list[tuple[int, HubPackage]] = []
    for package in packages:
        haystack = " ".join(
            [package.id, package.name, package.description, package.author, *(package.tags or [])]
        )
        score = fuzzy_score(query, haystack)
        if score > 0:
            results.append((score, package))

    results.sort(key=lambda item: (-item[0], item[1].name))
    return [package for _, package in results]


def _remote_package_files(package_id: str) -> list[str]:
    base = f"{_files_base().rstrip('/')}/{package_id}/"
    names = ["snippets.yml", "snippets.yaml", "base.yml", "base.yaml"]
    found: list[str] = []
    for name in names:
        try:
            with urlopen(base + name, timeout=15) as response:
                if response.status == 200:
                    found.append(name)
        except URLError:
            continue
    if found:
        return found

    # Fallback: try to discover any yaml file via common names only.
    raise FileNotFoundError(f"No package files found for {package_id!r} at {base}")


def _download_package_file(package_id: str, filename: str) -> str:
    url = f"{_files_base().rstrip('/')}/{package_id}/{filename}"
    with urlopen(url, timeout=15) as response:
        return response.read().decode("utf-8")


def install_hub_package(config_dir: Path, package_id: str, *, force: bool = False) -> Path:
    package_id = _validate_package_id(package_id)
    registry = {item.id: item for item in fetch_registry()}
    if package_id not in registry:
        raise ValueError(f"Unknown hub package: {package_id}")

    destination = match_dir(config_dir) / "packages" / package_id
    if destination.exists() and any(destination.glob("*.y*ml")) and not force:
        raise FileExistsError(f"Package already installed: {package_id}")

    destination.mkdir(parents=True, exist_ok=True)
    local_source = _local_package_dir(package_id)
    if local_source.exists():
        for path in sorted(local_source.glob("*.yml")) + sorted(local_source.glob("*.yaml")):
            shutil.copy2(path, destination / path.name)
        return destination

    for filename in _remote_package_files(package_id):
        content = _download_package_file(package_id, filename)
        (destination / filename).write_text(content, encoding="utf-8")

    return destination


def uninstall_hub_package(config_dir: Path, package_id: str) -> bool:
    package_id = _validate_package_id(package_id)
    destination = match_dir(config_dir) / "packages" / package_id
    if not destination.exists():
        return False
    shutil.rmtree(destination)
    return True


def _validate_package_id(package_id: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", package_id):
        raise ValueError(f"Invalid package id: {package_id!r}")
    return package_id


def hub_packages_for_picker(config_dir: Path) -> list[dict[str, str]]:
    from .packages import list_installed_packages

    installed = set(list_installed_packages(match_dir(config_dir)))
    items: list[dict[str, str]] = []
    for index, package in enumerate(fetch_registry()):
        status = "installed" if package.id in installed else "available"
        items.append(
            {
                "id": str(index),
                "trigger": package.id,
                "label": f"{package.name} ({status})",
                "preview": "\n".join(
                    part
                    for part in [
                        package.description,
                        f"Author: {package.author}" if package.author else "",
                        f"Tags: {', '.join(package.tags)}" if package.tags else "",
                    ]
                    if part
                ),
                "package_id": package.id,
                "installed": "1" if package.id in installed else "0",
            }
        )
    return items
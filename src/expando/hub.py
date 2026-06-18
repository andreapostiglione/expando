from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import yaml

from .config import normalize_match
from .paths import match_dir, package_root


DEFAULT_INDEX_URL = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/packages/hub/index.json"
)
DEFAULT_FILES_BASE = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/default_config/match/packages"
)
DEFAULT_COMMUNITY_FILES_BASE = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/packages/community"
)


@dataclass
class HubPackage:
    id: str
    name: str
    description: str
    author: str = ""
    tags: list[str] | None = None
    status: str | None = None
    submitted_at: str | None = None
    reviewed_at: str | None = None
    reviewer: str | None = None
    review_note: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HubPackage:
        return cls(
            id=str(data["id"]),
            name=str(data.get("name", data["id"])),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            tags=[str(item) for item in data.get("tags", []) or []],
            status=str(data["status"]) if data.get("status") else None,
            submitted_at=str(data["submitted_at"]) if data.get("submitted_at") else None,
            reviewed_at=str(data["reviewed_at"]) if data.get("reviewed_at") else None,
            reviewer=str(data["reviewer"]) if data.get("reviewer") else None,
            review_note=str(data["review_note"]) if data.get("review_note") else None,
        )


def _index_url() -> str:
    return os.environ.get("EXPANDO_HUB_INDEX_URL", DEFAULT_INDEX_URL)


def _files_base() -> str:
    return os.environ.get("EXPANDO_HUB_FILES_BASE", DEFAULT_FILES_BASE)


def _community_files_base() -> str:
    return os.environ.get("EXPANDO_HUB_COMMUNITY_FILES_BASE", DEFAULT_COMMUNITY_FILES_BASE)


def _local_index_path() -> Path:
    return package_root() / "packages" / "hub" / "index.json"


def _local_package_dir(package_id: str) -> Path:
    return package_root() / "default_config" / "match" / "packages" / package_id


def _community_package_dir(package_id: str) -> Path:
    return package_root() / "packages" / "community" / package_id


def _local_package_sources(package_id: str) -> list[Path]:
    return [_local_package_dir(package_id), _community_package_dir(package_id)]


def _remote_files_bases() -> list[str]:
    return [_files_base().rstrip("/"), _community_files_base().rstrip("/")]


def _load_index_data(path: Path | None = None) -> list[HubPackage]:
    if path is None:
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

    data = json.loads(path.read_text(encoding="utf-8"))
    return [HubPackage.from_dict(item) for item in data.get("packages", []) or []]


def fetch_registry(*, include_marketplace: bool = True) -> list[HubPackage]:
    packages = _load_index_data()
    if not include_marketplace:
        return packages

    try:
        from .hub_marketplace import fetch_marketplace_packages

        known = {item.id for item in packages}
        for item in fetch_marketplace_packages():
            if item.id not in known:
                packages.append(item)
                known.add(item.id)
    except RuntimeError:
        pass
    return packages


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
    names = ["snippets.yml", "snippets.yaml", "base.yml", "base.yaml"]
    for base in _remote_files_bases():
        package_base = f"{base}/{package_id}/"
        found: list[str] = []
        for name in names:
            try:
                with urlopen(package_base + name, timeout=15) as response:
                    if response.status == 200:
                        found.append(name)
            except URLError:
                continue
        if found:
            return found

    raise FileNotFoundError(f"No package files found for {package_id!r}")


def _download_package_file(package_id: str, filename: str) -> str:
    errors: list[str] = []
    for base in _remote_files_bases():
        url = f"{base}/{package_id}/{filename}"
        try:
            with urlopen(url, timeout=15) as response:
                return response.read().decode("utf-8")
        except URLError as exc:
            errors.append(f"{url}: {exc}")
            continue
    raise FileNotFoundError("; ".join(errors))


def install_hub_package(config_dir: Path, package_id: str, *, force: bool = False) -> Path:
    package_id = _validate_package_id(package_id)
    registry = {item.id: item for item in fetch_registry()}
    if package_id not in registry:
        raise ValueError(f"Unknown hub package: {package_id}")

    destination = match_dir(config_dir) / "packages" / package_id
    if destination.exists() and any(destination.glob("*.y*ml")) and not force:
        raise FileExistsError(f"Package already installed: {package_id}")

    destination.mkdir(parents=True, exist_ok=True)
    for local_source in _local_package_sources(package_id):
        if not local_source.exists():
            continue
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


@dataclass
class HubPublishReport:
    package_id: str
    match_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    installed_to: Path | None = None
    bundled_to: Path | None = None
    registered: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors


def _package_yaml_files(package_dir: Path) -> list[Path]:
    names = ("snippets.yml", "snippets.yaml", "base.yml", "base.yaml")
    found = [package_dir / name for name in names if (package_dir / name).exists()]
    if found:
        return found
    return sorted(package_dir.glob("*.yml")) + sorted(package_dir.glob("*.yaml"))


def _read_hub_manifest(package_dir: Path) -> HubPackage:
    manifest_path = package_dir / "hub.json"
    if not manifest_path.exists():
        raise ValueError("hub.json mancante: serve id, name e description")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_id = _validate_package_id(str(data["id"]))
    if package_dir.name != package_id:
        raise ValueError(
            f"La cartella deve chiamarsi {package_id!r}, trovata {package_dir.name!r}"
        )
    return HubPackage.from_dict(data)


def validate_hub_package_dir(package_dir: Path) -> HubPublishReport:
    package_dir = package_dir.expanduser().resolve()
    report = HubPublishReport(package_id=package_dir.name)
    if not package_dir.is_dir():
        report.errors.append(f"Cartella package non trovata: {package_dir}")
        return report

    try:
        manifest = _read_hub_manifest(package_dir)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        report.errors.append(str(exc))
        return report

    report.package_id = manifest.id
    yaml_files = _package_yaml_files(package_dir)
    if not yaml_files:
        report.errors.append("Nessun file YAML snippet trovato (snippets.yml o *.yml)")
        return report

    match_count = 0
    for yaml_path in yaml_files:
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            report.errors.append(f"{yaml_path.name}: YAML non valido ({exc})")
            continue
        matches = data.get("matches", []) or []
        if not matches:
            report.warnings.append(f"{yaml_path.name}: nessun match definito")
            continue
        for index, raw in enumerate(matches):
            if not isinstance(raw, dict):
                report.errors.append(f"{yaml_path.name}[{index}]: match non è un oggetto")
                continue
            try:
                normalize_match(raw)
                match_count += 1
            except ValueError as exc:
                report.errors.append(f"{yaml_path.name}[{index}]: {exc}")

    report.match_count = match_count
    if match_count == 0 and not report.errors:
        report.errors.append("Il package non contiene match validi")
    return report


def _copy_package_tree(source_dir: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source_dir.iterdir()):
        if path.name.startswith("."):
            continue
        target = destination / path.name
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)


def _register_package_in_index(manifest: HubPackage) -> None:
    index_path = _local_index_path()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    packages = [item for item in data.get("packages", []) or [] if item.get("id") != manifest.id]
    packages.append(
        {
            "id": manifest.id,
            "name": manifest.name,
            "description": manifest.description,
            "author": manifest.author,
            "tags": manifest.tags or [],
        }
    )
    packages.sort(key=lambda item: str(item.get("id", "")))
    data["packages"] = packages
    index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publish_hub_package(
    package_dir: Path,
    *,
    config_dir: Path | None = None,
    install: bool = False,
    bundle: bool = False,
    register: bool = False,
) -> HubPublishReport:
    report = validate_hub_package_dir(package_dir)
    if not report.ok:
        return report

    manifest = _read_hub_manifest(package_dir.expanduser().resolve())
    source = package_dir.expanduser().resolve()

    if install:
        if config_dir is None:
            report.errors.append("config_dir richiesto con --install")
            return report
        destination = match_dir(config_dir) / "packages" / manifest.id
        _copy_package_tree(source, destination)
        report.installed_to = destination

    if bundle:
        destination = _local_package_dir(manifest.id)
        _copy_package_tree(source, destination)
        report.bundled_to = destination

    if register:
        _register_package_in_index(manifest)
        report.registered = True

    return report


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
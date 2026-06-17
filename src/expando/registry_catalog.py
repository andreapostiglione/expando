from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .hub import fetch_registry
from .i18n import t
from .packages import list_installed_packages
from .paths import match_dir, package_root, plugins_dir
from .plugins import PluginManager


@dataclass
class RegistryCatalog:
    hub_packages: list[dict[str, object]] = field(default_factory=list)
    installed_packages: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    index_path: str = ""


def build_registry_catalog(config_dir: Path) -> RegistryCatalog:
    installed = list_installed_packages(match_dir(config_dir))
    hub = [
        {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "author": package.author,
            "tags": package.tags or [],
            "installed": package.id in installed,
        }
        for package in fetch_registry()
    ]
    manager = PluginManager(config_dir)
    index_path = str(package_root() / "packages" / "hub" / "index.json")
    return RegistryCatalog(
        hub_packages=hub,
        installed_packages=installed,
        plugins=manager.list_plugins(),
        index_path=index_path,
    )


def format_registry_report(catalog: RegistryCatalog, *, config_dir: Path) -> str:
    lines = [
        t("registry.title"),
        f"{t('registry.index')}: {catalog.index_path}",
        "",
        t("registry.hub_packages"),
    ]
    for package in catalog.hub_packages:
        marker = t("cli.hub.installed_marker") if package.get("installed") else ""
        lines.append(f"  {package['id']}: {package['name']}{marker}")
    lines.append("")
    lines.append(t("registry.installed_packages"))
    if catalog.installed_packages:
        for name in catalog.installed_packages:
            lines.append(f"  - {name}")
    else:
        lines.append(f"  ({t('cli.packages.none')})")
    lines.append("")
    lines.append(t("registry.plugins"))
    if catalog.plugins:
        plugin_root = plugins_dir(config_dir)
        for name in catalog.plugins:
            lines.append(f"  - {name} ({plugin_root / name})")
    else:
        lines.append(f"  ({t('cli.plugins.none')})")
    return "\n".join(lines)


def format_registry_json(catalog: RegistryCatalog) -> str:
    return json.dumps(
        {
            "hub_packages": catalog.hub_packages,
            "installed_packages": catalog.installed_packages,
            "plugins": catalog.plugins,
            "index_path": catalog.index_path,
        },
        indent=2,
        ensure_ascii=False,
    ) + "\n"
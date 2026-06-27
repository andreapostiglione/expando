from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from .config import load_config
from .hub import DEFAULT_FILES_BASE, DEFAULT_INDEX_URL, _validate_package_id
from .paths import match_dir, plugins_dir
from .plugins import resolve_plugin_script
from .renderer import SHELL_CHAIN_RE

_PACKAGE_ID_PROBE = "valid-id"


@dataclass
class SecurityFinding:
    check_id: str
    status: str
    message: str


@dataclass
class SecurityAuditReport:
    ok: bool
    findings: list[SecurityFinding] = field(default_factory=list)

    def add(self, check_id: str, status: str, message: str) -> None:
        self.findings.append(SecurityFinding(check_id=check_id, status=status, message=message))


def _hub_url_status(name: str, url: str) -> SecurityFinding:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return SecurityFinding(
            check_id=f"hub.{name}",
            status="fail",
            message=f"{name} must use HTTPS: {url}",
        )
    if not parsed.netloc:
        return SecurityFinding(
            check_id=f"hub.{name}",
            status="fail",
            message=f"{name} URL is invalid: {url}",
        )
    return SecurityFinding(
        check_id=f"hub.{name}",
        status="pass",
        message=f"{name} uses HTTPS ({parsed.netloc})",
    )


def _iter_shell_commands(config_dir: Path) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    directory = match_dir(config_dir)
    if not directory.exists():
        return results
    for path in sorted(directory.rglob("*.yml")) + sorted(directory.rglob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        location = str(path.relative_to(config_dir))
        for index, var in enumerate(data.get("global_vars", []) or []):
            if str(var.get("type", "")).lower() == "shell":
                cmd = str(var.get("params", {}).get("cmd", ""))
                results.append((f"{location}:global#{index + 1}", "global_var", cmd))
        for index, match in enumerate(data.get("matches", []) or []):
            triggers = match.get("triggers") or ([match["trigger"]] if "trigger" in match else ["?"])
            trigger = str(triggers[0])
            for var in match.get("vars", []) or []:
                if str(var.get("type", "")).lower() == "shell":
                    cmd = str(var.get("params", {}).get("cmd", ""))
                    results.append((f"{location}#{index + 1}", trigger, cmd))
    return results


def run_security_audit(config_dir: Path) -> SecurityAuditReport:
    report = SecurityAuditReport(ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        bundle = load_config(config_dir)
    except Exception as exc:
        report.add("config.load", "fail", f"Cannot load config: {exc}")
        report.ok = False
        return report

    allowlist = bundle.app.shell_allowlist
    shell_commands = _iter_shell_commands(config_dir)
    if shell_commands and not allowlist:
        report.add(
            "shell.allowlist",
            "fail",
            f"{len(shell_commands)} shell variable(s) found but shell_allowlist is empty",
        )
        report.ok = False
    elif not allowlist:
        report.add(
            "shell.allowlist",
            "warn",
            "shell_allowlist is empty — shell variables are denied by default",
        )
    else:
        report.add(
            "shell.allowlist",
            "pass",
            f"shell_allowlist defines {len(allowlist)} allowed command(s)",
        )

    for location, trigger, cmd in shell_commands:
        if cmd and SHELL_CHAIN_RE.search(cmd):
            report.add(
                "shell.chaining",
                "fail",
                f"Shell chaining blocked in {location} ({trigger}): {cmd!r}",
            )
            report.ok = False

    try:
        resolve_plugin_script(config_dir, "../outside.py")
        report.add(
            "plugins.path_traversal",
            "fail",
            "Plugin script resolver accepted a path outside plugins/",
        )
        report.ok = False
    except RuntimeError:
        report.add(
            "plugins.path_traversal",
            "pass",
            "Plugin script paths cannot escape plugins/",
        )

    plugins_root = plugins_dir(config_dir)
    if plugins_root.exists():
        resolved_plugins_root = plugins_root.resolve()
        for path in plugins_root.rglob("*.py"):
            resolved = path.resolve()
            try:
                resolved.relative_to(resolved_plugins_root)
            except ValueError:
                report.add(
                    "plugins.symlink",
                    "warn",
                    f"Plugin file resolves outside plugins/: {path.name}",
                )

    for finding in (
        _hub_url_status("index", DEFAULT_INDEX_URL),
        _hub_url_status("files_base", DEFAULT_FILES_BASE),
    ):
        report.findings.append(finding)
        if finding.status == "fail":
            report.ok = False

    try:
        _validate_package_id(_PACKAGE_ID_PROBE)
        _validate_package_id("../evil")
        report.add("hub.package_id", "fail", "Package id validator accepted traversal")
        report.ok = False
    except ValueError:
        report.add(
            "hub.package_id",
            "pass",
            "Hub package ids reject path traversal characters",
        )

    import_dir = config_dir / "match"
    if import_dir.exists():
        report.add(
            "import.yaml_only",
            "pass",
            "Import copies only .yml/.yaml files into match/",
        )

    try:
        from .image_paths import resolve_image_path

        resolve_image_path(config_dir, "../outside.png")
        report.add("image.path_traversal", "fail", "Image path resolver accepted traversal")
        report.ok = False
    except RuntimeError:
        report.add(
            "image.path_traversal",
            "pass",
            "Image paths cannot escape config directory",
        )

    return report


def format_security_audit_report(report: SecurityAuditReport) -> str:
    from .i18n import t

    status_icon = {"pass": "✓", "warn": "!", "fail": "✗"}
    title = t("security.title.ok") if report.ok else t("security.title.issues")
    lines = [title]
    for item in report.findings:
        icon = status_icon.get(item.status, "?")
        lines.append(f"  [{icon}] {item.check_id}: {item.message}")
    return "\n".join(lines)

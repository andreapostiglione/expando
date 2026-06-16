from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import load_config
from .daemon import is_running
from .permissions import PermissionStatus, check_permissions


@dataclass
class DoctorReport:
    ok: bool
    config_dir: Path
    running: bool
    pid: int | None
    process_count: int
    match_count: int
    duplicate_triggers: list[str] = field(default_factory=list)
    config_errors: list[str] = field(default_factory=list)
    permissions: PermissionStatus | None = None
    warnings: list[str] = field(default_factory=list)


def find_expando_processes() -> list[int]:
    try:
        result = subprocess.run(
            ["ps", "-ax", "-o", "pid=,command="],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []

    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"(\d+)\s+(.*)", line)
        if not match:
            continue
        pid = int(match.group(1))
        command = match.group(2)
        if "expando doctor" in command or "expando stop" in command:
            continue
        if any(
            token in command
            for token in (
                "expando run",
                "expando.daemon",
                "Expando.app/Contents",
                "-m expando.daemon",
            )
        ):
            pids.append(pid)
    return pids


def find_duplicate_triggers(config_dir: Path) -> list[str]:
    trigger_map: dict[str, int] = {}
    match_dir = config_dir / "match"
    if not match_dir.exists():
        return []

    for path in sorted(match_dir.glob("*.yml")) + sorted(match_dir.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for item in data.get("matches", []) or []:
            triggers: list[str] = []
            if "trigger" in item:
                triggers.append(str(item["trigger"]))
            if "triggers" in item:
                triggers.extend(str(value) for value in item["triggers"])
            for trigger in triggers:
                trigger_map[trigger] = trigger_map.get(trigger, 0) + 1

    return sorted(trigger for trigger, count in trigger_map.items() if count > 1)


def validate_config_files(config_dir: Path) -> list[str]:
    errors: list[str] = []
    for relative in ("config/default.yml",):
        path = config_dir / relative
        if not path.exists():
            errors.append(f"Missing config file: {relative}")
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            errors.append(f"Invalid YAML in {relative}: {exc}")

    match_dir = config_dir / "match"
    if not match_dir.exists():
        errors.append("Missing match directory")
        return errors

    for path in sorted(match_dir.glob("*.yml")) + sorted(match_dir.glob("*.yaml")):
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            for index, item in enumerate(data.get("matches", []) or []):
                if "trigger" not in item and "triggers" not in item:
                    errors.append(f"{path.name}: match #{index + 1} has no trigger")
        except yaml.YAMLError as exc:
            errors.append(f"Invalid YAML in {path.name}: {exc}")
        except Exception as exc:
            errors.append(f"Error in {path.name}: {exc}")

    return errors


def run_doctor(config_dir: Path) -> DoctorReport:
    config_dir.mkdir(parents=True, exist_ok=True)
    running, pid = is_running(config_dir)
    process_count = len(find_expando_processes())
    config_errors = validate_config_files(config_dir)
    duplicate_triggers = find_duplicate_triggers(config_dir)
    permissions = check_permissions()

    warnings: list[str] = []
    if process_count > 1:
        warnings.append(
            f"Trovati {process_count} processi Expando: esegui `expando stop` e riavvia"
        )
    if duplicate_triggers:
        warnings.append(
            "Trigger duplicati: " + ", ".join(duplicate_triggers)
        )
    if permissions:
        warnings.extend(permissions.notes)

    try:
        bundle = load_config(config_dir)
        match_count = len(bundle.matches)
    except Exception as exc:
        match_count = 0
        config_errors.append(f"Failed to load config: {exc}")

    ok = not config_errors and process_count <= 1 and not duplicate_triggers

    return DoctorReport(
        ok=ok,
        config_dir=config_dir,
        running=running,
        pid=pid,
        process_count=process_count,
        match_count=match_count,
        duplicate_triggers=duplicate_triggers,
        config_errors=config_errors,
        permissions=permissions,
        warnings=warnings,
    )


def format_doctor_report(report: DoctorReport) -> str:
    lines = [
        f"Config dir: {report.config_dir}",
        f"Status: {'OK' if report.ok else 'ISSUES FOUND'}",
        f"Daemon running: {'yes' if report.running else 'no'}",
    ]
    if report.pid:
        lines.append(f"PID: {report.pid}")
    lines.append(f"Expando processes: {report.process_count}")
    lines.append(f"Matches loaded: {report.match_count}")

    if report.permissions:
        acc = report.permissions.accessibility
        inp = report.permissions.input_monitoring
        lines.append(
            f"Accessibility: {_fmt_bool(acc)}"
        )
        lines.append(
            f"Input monitoring: {_fmt_bool(inp)}"
        )

    if report.config_errors:
        lines.append("")
        lines.append("Config errors:")
        lines.extend(f"  - {item}" for item in report.config_errors)

    if report.duplicate_triggers:
        lines.append("")
        lines.append("Duplicate triggers:")
        lines.extend(f"  - {item}" for item in report.duplicate_triggers)

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  - {item}" for item in report.warnings)

    return "\n".join(lines)


def _fmt_bool(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "granted" if value else "missing"
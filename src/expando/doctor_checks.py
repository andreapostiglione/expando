from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import ConfigCompileError, compile_matches, load_config
from .daemon import is_running
from .i18n import t
from .match_utils import find_duplicate_literal_triggers
from .permissions import PermissionStatus, check_permissions, permissions_ready
from .runtime_info import RuntimeInfo, detect_runtime


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
    runtime: RuntimeInfo | None = None
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
    try:
        bundle = load_config(config_dir)
    except Exception:
        return []
    return find_duplicate_literal_triggers(bundle.matches)


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

    try:
        bundle = load_config(config_dir)
        compile_matches(bundle.matches)
    except ConfigCompileError as exc:
        errors.append(str(exc))

    return errors


def _runtime_label(mode: str) -> str:
    return t(f"runtime.{mode}")


def run_doctor(config_dir: Path) -> DoctorReport:
    config_dir.mkdir(parents=True, exist_ok=True)
    running, pid = is_running(config_dir)
    process_count = len(find_expando_processes())
    config_errors = validate_config_files(config_dir)
    duplicate_triggers = find_duplicate_triggers(config_dir)
    permissions = check_permissions()
    runtime = permissions.runtime or detect_runtime()

    warnings: list[str] = []
    if process_count > 1:
        warnings.append(
            f"Trovati {process_count} processi Expando: esegui `expando stop` e riavvia."
        )
    if duplicate_triggers:
        warnings.append(
            "Trigger duplicati: " + ", ".join(duplicate_triggers)
        )
    if permissions:
        warnings.extend(permissions.notes)
    if permissions and not permissions_ready(permissions):
        warnings.append(
            "L'espansione automatica non funzionerà finché Accessibilità non è concessa "
            f"per {runtime.grant_label}."
        )

    try:
        bundle = load_config(config_dir)
        match_count = len(bundle.matches)
    except Exception as exc:
        match_count = 0
        config_errors.append(f"Failed to load config: {exc}")

    ok = (
        not config_errors
        and process_count <= 1
        and not duplicate_triggers
        and (permissions is None or permissions_ready(permissions))
    )

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
        runtime=runtime,
        warnings=warnings,
    )


def format_doctor_report(report: DoctorReport) -> str:
    title = t("doctor.title.ok") if report.ok else t("doctor.title.issues")
    lines = [
        f"{title}",
        f"{t('doctor.config_dir')}: {report.config_dir}",
        f"{t('doctor.daemon_running')}: {t('doctor.yes') if report.running else t('doctor.no')}",
    ]
    if report.pid:
        lines.append(f"{t('doctor.pid')}: {report.pid}")
    lines.append(f"{t('doctor.processes')}: {report.process_count}")
    lines.append(f"{t('doctor.matches')}: {report.match_count}")

    if report.runtime:
        lines.append(
            f"{t('doctor.runtime')}: {_runtime_label(report.runtime.mode)}"
        )
        lines.append(
            f"{t('doctor.grant_target')}: {report.runtime.grant_label}"
        )
        lines.append(f"  → {report.runtime.grant_hint}")

    if report.permissions:
        acc = report.permissions.accessibility
        inp = report.permissions.input_monitoring
        inj = report.permissions.injection_ready
        lines.append(
            f"{t('doctor.accessibility')}: {_fmt_bool(acc)}"
        )
        lines.append(
            f"{t('doctor.input_monitoring')}: {_fmt_bool(inp)}"
        )
        lines.append(
            f"{t('doctor.injection')}: {_fmt_bool(inj)}"
        )

    if report.config_errors:
        lines.append("")
        lines.append(f"{t('doctor.config_errors')}:")
        lines.extend(f"  - {item}" for item in report.config_errors)

    if report.duplicate_triggers:
        lines.append("")
        lines.append(f"{t('doctor.duplicates')}:")
        lines.extend(f"  - {item}" for item in report.duplicate_triggers)

    if report.warnings:
        lines.append("")
        lines.append(f"{t('doctor.warnings')}:")
        lines.extend(f"  - {item}" for item in report.warnings)

    return "\n".join(lines)


def _fmt_bool(value: bool | None) -> str:
    if value is None:
        return t("doctor.perm.unknown")
    return t("doctor.perm.granted") if value else t("doctor.perm.missing")
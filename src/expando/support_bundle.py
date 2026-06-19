from __future__ import annotations

import json
import re
import shutil
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .crash_reporting import list_crash_reports
from .doctor_checks import doctor_document
from .health import build_health_document
from .log_viewer import tail_log_entries
from .paths import crashes_dir, log_file

SECRET_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|private[_-]?key|auth)",
    re.IGNORECASE,
)
REDACTED = "***REDACTED***"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _redact_mapping(data: Any) -> Any:
    if isinstance(data, dict):
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                redacted[key] = REDACTED
            else:
                redacted[key] = _redact_mapping(value)
        return redacted
    if isinstance(data, list):
        return [_redact_mapping(item) for item in data]
    if isinstance(data, str) and SECRET_KEY_PATTERN.search(data) and len(data) > 8:
        return REDACTED
    return data


def redact_config_tree(config_dir: Path, destination: Path) -> None:
    for relative in ("config", "match"):
        source = config_dir / relative
        if not source.exists():
            continue
        for path in sorted(source.rglob("*.yml")) + sorted(source.rglob("*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                shutil.copy2(path, destination / path.relative_to(config_dir))
                continue
            redacted = _redact_mapping(data)
            target = destination / path.relative_to(config_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                yaml.safe_dump(redacted, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _copy_recent_logs(config_dir: Path, destination: Path, *, lines: int = 500) -> None:
    log_path = log_file(config_dir)
    if not log_path.exists():
        return
    entries = tail_log_entries(log_path, lines=lines)
    _write_json(destination / "logs.json", {"lines": lines, "entries": entries})
    text_lines = [entry.get("raw", "") for entry in entries if entry.get("raw")]
    (destination / "expando.log.tail").write_text("\n".join(text_lines) + "\n", encoding="utf-8")


def _copy_crash_reports(config_dir: Path, destination: Path, *, limit: int = 10) -> None:
    crash_root = destination / "crashes"
    crash_root.mkdir(parents=True, exist_ok=True)
    summaries = list_crash_reports(config_dir, limit=limit)
    for summary in summaries:
        target = crash_root / summary.path.name
        shutil.copy2(summary.path, target)
    index = [
        {
            "path": summary.path.name,
            "timestamp": summary.timestamp.isoformat(),
            "source": summary.source,
            "exception_type": summary.exception_type,
            "message": summary.message,
        }
        for summary in summaries
    ]
    _write_json(crash_root / "index.json", {"reports": index})


def create_support_bundle(config_dir: Path, output_path: Path) -> Path:
    config_dir = config_dir.expanduser()
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        staging = Path(temp_dir) / "bundle"
        staging.mkdir(parents=True)

        redact_config_tree(config_dir, staging)
        _write_json(staging / "doctor.json", doctor_document(config_dir))
        _write_json(staging / "health.json", build_health_document(config_dir))
        _copy_recent_logs(config_dir, staging)
        if crashes_dir(config_dir).exists():
            _copy_crash_reports(config_dir, staging)

        manifest = {
            "generated_at": _utc_now(),
            "config_dir": str(config_dir),
            "includes": [
                "config/ (redacted)",
                "match/ (redacted)",
                "doctor.json",
                "health.json",
                "logs.json",
                "expando.log.tail",
                "crashes/ (recent)",
            ],
        }
        _write_json(staging / "manifest.json", manifest)

        with tarfile.open(output_path, "w:gz") as archive:
            archive.add(staging, arcname="expando-support")

    return output_path
from __future__ import annotations

import faulthandler
import json
import platform
import sys
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .paths import crashes_dir

_MAX_CRASH_REPORTS = 50
_installed_for: Path | None = None
_fault_file_handle = None


@dataclass
class CrashReportSummary:
    path: Path
    timestamp: datetime
    source: str
    exception_type: str
    message: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%S")


def _build_payload(
    *,
    source: str,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    exc_tb,
) -> dict[str, Any]:
    if exc_type is None and exc_value is not None:
        exc_type = type(exc_value)
    return {
        "timestamp": _utc_now().isoformat(),
        "version": __version__,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "pid": os_getpid(),
        "source": source,
        "exception_type": exc_type.__name__ if exc_type else "Unknown",
        "message": str(exc_value) if exc_value is not None else "",
        "traceback": "".join(
            traceback.format_exception(exc_type, exc_value, exc_tb)
        )
        if exc_type is not None
        else "",
    }


def os_getpid() -> int:
    import os

    return os.getpid()


def write_crash_report(
    config_dir: Path,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    exc_tb,
    *,
    source: str = "main",
) -> Path:
    directory = crashes_dir(config_dir)
    directory.mkdir(parents=True, exist_ok=True)
    moment = _utc_now()
    filename = f"crash-{_timestamp_slug(moment)}-{os_getpid()}.json"
    path = directory / filename
    payload = _build_payload(
        source=source,
        exc_type=exc_type,
        exc_value=exc_value,
        exc_tb=exc_tb,
    )
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _prune_old_reports(directory)
    return path


def _prune_old_reports(directory: Path) -> None:
    reports = sorted(directory.glob("crash-*.json"), key=lambda item: item.stat().st_mtime)
    overflow = len(reports) - _MAX_CRASH_REPORTS
    for path in reports[:overflow]:
        path.unlink(missing_ok=True)


def list_crash_reports(config_dir: Path, *, limit: int = 20) -> list[CrashReportSummary]:
    directory = crashes_dir(config_dir)
    if not directory.exists():
        return []

    summaries: list[CrashReportSummary] = []
    for path in sorted(directory.glob("crash-*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        timestamp_raw = payload.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_raw)
        except ValueError:
            timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        summaries.append(
            CrashReportSummary(
                path=path,
                timestamp=timestamp,
                source=str(payload.get("source", "unknown")),
                exception_type=str(payload.get("exception_type", "Unknown")),
                message=str(payload.get("message", "")),
            )
        )
        if len(summaries) >= limit:
            break
    return summaries


def format_crash_report(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = [
        f"Timestamp: {payload.get('timestamp', '')}",
        f"Version: {payload.get('version', '')}",
        f"Source: {payload.get('source', '')}",
        f"Exception: {payload.get('exception_type', '')}: {payload.get('message', '')}",
        "",
        payload.get("traceback", "").rstrip(),
    ]
    return "\n".join(lines)


def install_crash_handlers(config_dir: Path) -> None:
    global _installed_for, _fault_file_handle
    if _installed_for == config_dir:
        return

    directory = crashes_dir(config_dir)
    directory.mkdir(parents=True, exist_ok=True)

    if _fault_file_handle is not None:
        try:
            _fault_file_handle.close()
        except OSError:
            pass

    fault_path = directory / "faulthandler.log"
    _fault_file_handle = fault_path.open("a", encoding="utf-8")
    faulthandler.enable(file=_fault_file_handle, all_threads=True)

    original_excepthook = sys.excepthook

    def excepthook(exc_type, exc_value, exc_tb) -> None:
        try:
            write_crash_report(
                config_dir,
                exc_type,
                exc_value,
                exc_tb,
                source="main",
            )
        except Exception:
            pass
        original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = excepthook

    if hasattr(threading, "excepthook"):
        original_thread_hook = threading.excepthook

        def thread_excepthook(args) -> None:
            try:
                write_crash_report(
                    config_dir,
                    args.exc_type,
                    args.exc_value,
                    args.exc_traceback,
                    source=f"thread:{args.thread.name}",
                )
            except Exception:
                pass
            original_thread_hook(args)

        threading.excepthook = thread_excepthook  # type: ignore[attr-defined]

    _installed_for = config_dir


def recent_crash_count(config_dir: Path, *, days: int = 7) -> int:
    cutoff = _utc_now().timestamp() - (days * 86400)
    directory = crashes_dir(config_dir)
    if not directory.exists():
        return 0
    count = 0
    for path in directory.glob("crash-*.json"):
        if path.stat().st_mtime >= cutoff:
            count += 1
    return count
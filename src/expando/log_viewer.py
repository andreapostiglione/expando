from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

LOG_LINE_RE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\[(?P<level>[A-Z]+)\] "
    r"(?P<logger>[^:]+): "
    r"(?P<message>.*)$"
)


def resolve_log_level(name: str | None = None) -> int:
    raw = (name or os.environ.get("EXPANDO_LOG_LEVEL", "INFO")).upper()
    return getattr(logging, raw, logging.INFO)


def parse_log_line(line: str) -> dict[str, Any]:
    stripped = line.rstrip("\n")
    match = LOG_LINE_RE.match(stripped)
    if not match:
        return {"raw": stripped, "parsed": False}
    return {
        "raw": stripped,
        "parsed": True,
        "timestamp": match.group("timestamp"),
        "level": match.group("level"),
        "logger": match.group("logger"),
        "message": match.group("message"),
    }


def tail_log_entries(log_path: Path, *, lines: int = 50) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = content[-lines:] if lines > 0 else content
    return [parse_log_line(line) for line in selected]


def logs_as_json(log_path: Path, *, lines: int = 50) -> dict[str, Any]:
    return {
        "path": str(log_path),
        "lines": lines,
        "entries": tail_log_entries(log_path, lines=lines),
    }


def print_log_tail(
    log_path: Path,
    *,
    lines: int = 50,
    follow: bool = False,
    poll_interval: float = 0.5,
    as_json: bool = False,
) -> None:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    if as_json:
        print(json.dumps(logs_as_json(log_path, lines=lines), indent=2, ensure_ascii=False))
        if follow:
            raise RuntimeError("JSON log output does not support --tail follow mode")
        return

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        if lines > 0:
            content = handle.read().splitlines()
            for line in content[-lines:]:
                print(line)
        else:
            for line in handle:
                print(line.rstrip("\n"))

        if not follow:
            return

        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                print(line.rstrip("\n"))
            else:
                time.sleep(poll_interval)
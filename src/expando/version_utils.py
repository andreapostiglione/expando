from __future__ import annotations

import re


def normalize_version(value: str) -> str:
    return value.strip().lstrip("vV")


def version_tuple(value: str) -> tuple[int, ...]:
    cleaned = normalize_version(value)
    parts: list[int] = []
    for segment in cleaned.split("."):
        match = re.match(r"(\d+)", segment)
        parts.append(int(match.group(1)) if match else 0)
    return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
    return version_tuple(candidate) > version_tuple(current)
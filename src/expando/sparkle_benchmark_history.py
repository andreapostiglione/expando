from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .benchmark import (
    SparkleBenchmarkResult,
    sparkle_benchmark_result_to_dict,
    sparkle_helper_latency_fail,
    sparkle_helper_latency_slow,
)

HISTORY_VERSION = 1
MAX_HISTORY_ENTRIES = 50
SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def default_history_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "sparkle-benchmark-history.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_history_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": HISTORY_VERSION, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Sparkle benchmark history must be a JSON object")
    data.setdefault("entries", [])
    return data


def _save_history_document(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_sparkle_benchmark_entry(
    result: SparkleBenchmarkResult,
    *,
    version: str,
    warn_ms: int | None = None,
    fail_ms: int | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    slow = sparkle_helper_latency_slow(result.helper_check_ms, warn_ms)
    failed = sparkle_helper_latency_fail(result.helper_check_ms, fail_ms)
    return {
        "recorded_at": _utc_now(),
        "version": version,
        "tag": tag or f"v{version}",
        "warn_ms": warn_ms,
        "fail_ms": fail_ms,
        "slow": slow,
        "failed": failed,
        "benchmark": sparkle_benchmark_result_to_dict(
            result,
            warn_ms=warn_ms,
            fail_ms=fail_ms,
        ),
    }


def record_sparkle_benchmark(
    result: SparkleBenchmarkResult,
    path: Path,
    *,
    version: str,
    warn_ms: int | None = None,
    fail_ms: int | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    path = path.expanduser().resolve()
    data = _load_history_document(path)
    entry = build_sparkle_benchmark_entry(
        result,
        version=version,
        warn_ms=warn_ms,
        fail_ms=fail_ms,
        tag=tag,
    )
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    data["entries"] = entries[-MAX_HISTORY_ENTRIES:]
    data["version"] = HISTORY_VERSION
    data["updated_at"] = _utc_now()
    _save_history_document(path, data)
    return entry


def load_sparkle_benchmark_history(path: Path | None = None) -> list[dict[str, Any]]:
    document = _load_history_document(path or default_history_path())
    entries = document.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def _helper_check_ms_from_entry(item: dict[str, Any]) -> float | None:
    benchmark = item.get("benchmark", {})
    if not isinstance(benchmark, dict):
        return None
    helper_ms = benchmark.get("helper_check_ms")
    return float(helper_ms) if isinstance(helper_ms, (int, float)) else None


def sparkle_benchmark_sparkline(
    entries: list[dict[str, Any]],
    *,
    width: int = 20,
) -> str:
    values = [
        value
        for value in (_helper_check_ms_from_entry(item) for item in entries[-width:])
        if value is not None
    ]
    if not values:
        return ""
    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return SPARKLINE_CHARS[-1] * len(values)
    span = maximum - minimum
    chars: list[str] = []
    for value in values:
        rank = int(round(((value - minimum) / span) * (len(SPARKLINE_CHARS) - 1)))
        chars.append(SPARKLINE_CHARS[max(0, min(len(SPARKLINE_CHARS) - 1, rank))])
    return "".join(chars)


def sparkle_benchmark_history_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    slow_count = sum(1 for item in entries if item.get("slow"))
    failed_count = sum(1 for item in entries if item.get("failed"))
    last = entries[-1] if entries else {}
    benchmark = last.get("benchmark", {}) if isinstance(last.get("benchmark"), dict) else {}
    helper_ms = benchmark.get("helper_check_ms")
    latencies = [
        value
        for value in (_helper_check_ms_from_entry(item) for item in entries)
        if value is not None
    ]
    trend_avg = round(sum(latencies) / len(latencies), 2) if latencies else None
    return {
        "total": len(entries),
        "slow": slow_count,
        "failed": failed_count,
        "last_helper_ms": helper_ms,
        "last_version": last.get("version"),
        "last_recorded_at": last.get("recorded_at"),
        "trend_min_ms": round(min(latencies), 2) if latencies else None,
        "trend_max_ms": round(max(latencies), 2) if latencies else None,
        "trend_avg_ms": trend_avg,
        "trend_sparkline": sparkle_benchmark_sparkline(entries),
    }


def sparkle_benchmark_history_to_dict(
    path: Path | None = None,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    history_path = (path or default_history_path()).expanduser().resolve()
    entries = load_sparkle_benchmark_history(history_path)
    stats = sparkle_benchmark_history_stats(entries)
    recent = entries[-limit:] if limit is not None else entries
    return {
        "path": str(history_path),
        "version": HISTORY_VERSION,
        "stats": stats,
        "entries": recent,
    }


def format_sparkle_benchmark_history_report(
    path: Path | None = None,
    *,
    limit: int = 10,
) -> str:
    from .i18n import t

    history_path = (path or default_history_path()).expanduser().resolve()
    entries = load_sparkle_benchmark_history(history_path)
    stats = sparkle_benchmark_history_stats(entries)
    last_ms = (
        f"{stats['last_helper_ms']:.2f}"
        if isinstance(stats["last_helper_ms"], (int, float))
        else t("sparkle.benchmark.history.na")
    )
    lines = [
        t("sparkle.benchmark.history.title"),
        f"  {t('sparkle.benchmark.history.path')}: {history_path}",
        t("sparkle.benchmark.history.stats").format(
            total=stats["total"],
            slow=stats["slow"],
            last_ms=last_ms,
        ),
    ]
    if not entries:
        lines.append(t("sparkle.benchmark.history.empty"))
        return "\n".join(lines)

    sparkline = stats.get("trend_sparkline")
    if sparkline:
        lines.append(
            t("sparkle.benchmark.history.trend").format(
                sparkline=sparkline,
                min_ms=stats.get("trend_min_ms", t("sparkle.benchmark.history.na")),
                max_ms=stats.get("trend_max_ms", t("sparkle.benchmark.history.na")),
                avg_ms=stats.get("trend_avg_ms", t("sparkle.benchmark.history.na")),
            )
        )

    lines.append(t("sparkle.benchmark.history.recent").format(limit=min(limit, len(entries))))
    for item in entries[-limit:]:
        benchmark = item.get("benchmark", {})
        if not isinstance(benchmark, dict):
            benchmark = {}
        helper_ms = benchmark.get("helper_check_ms")
        helper_text = (
            f"{helper_ms:.2f}"
            if isinstance(helper_ms, (int, float))
            else t("sparkle.benchmark.history.na")
        )
        lines.append(
            t("sparkle.benchmark.history.entry").format(
                recorded_at=item.get("recorded_at", "?"),
                version=item.get("version", "?"),
                helper_ms=helper_text,
                slow=t("doctor.yes") if item.get("slow") else t("doctor.no"),
            )
        )
    return "\n".join(lines)
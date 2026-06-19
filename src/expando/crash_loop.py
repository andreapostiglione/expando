from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_VERSION = 1
MAX_ENTRIES = 20
DEFAULT_WINDOW_SECONDS = 600
DEFAULT_MAX_CRASHES = 5


def crash_loop_file(config_dir: Path) -> Path:
    return config_dir / "crash-loop.json"


def safe_mode_file(config_dir: Path) -> Path:
    return config_dir / "safe-mode.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": HISTORY_VERSION, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("crash-loop.json must be a JSON object")
    data.setdefault("entries", [])
    return data


def _save_document(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_daemon_start(config_dir: Path) -> None:
    path = crash_loop_file(config_dir)
    data = _load_document(path)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    entries.append({"recorded_at": _utc_now(), "event": "start"})
    data["entries"] = entries[-MAX_ENTRIES:]
    data["version"] = HISTORY_VERSION
    _save_document(path, data)


def record_daemon_crash(config_dir: Path, *, reason: str = "crash") -> None:
    path = crash_loop_file(config_dir)
    data = _load_document(path)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    entries.append({"recorded_at": _utc_now(), "event": "crash", "reason": reason})
    data["entries"] = entries[-MAX_ENTRIES:]
    _save_document(path, data)


def crash_count_in_window(
    config_dir: Path,
    *,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> int:
    path = crash_loop_file(config_dir)
    if not path.exists():
        return 0
    data = _load_document(path)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return 0
    cutoff = time.time() - window_seconds
    count = 0
    for item in entries:
        if not isinstance(item, dict) or item.get("event") != "crash":
            continue
        recorded_at = item.get("recorded_at")
        if not isinstance(recorded_at, str):
            continue
        try:
            ts = datetime.fromisoformat(recorded_at.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if ts >= cutoff:
            count += 1
    return count


def should_enter_safe_mode(
    config_dir: Path,
    *,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    max_crashes: int = DEFAULT_MAX_CRASHES,
) -> bool:
    return crash_count_in_window(config_dir, window_seconds=window_seconds) >= max_crashes


def activate_safe_mode(config_dir: Path, *, reason: str) -> dict[str, Any]:
    payload = {
        "active": True,
        "reason": reason,
        "activated_at": _utc_now(),
    }
    path = safe_mode_file(config_dir)
    _save_document(path, payload)
    return payload


def clear_safe_mode(config_dir: Path) -> None:
    safe_mode_file(config_dir).unlink(missing_ok=True)


def safe_mode_status(config_dir: Path) -> dict[str, Any] | None:
    path = safe_mode_file(config_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("active"):
        return data
    return None


def is_safe_mode_active(config_dir: Path) -> bool:
    return safe_mode_status(config_dir) is not None


def startup_backoff_seconds(config_dir: Path) -> float:
    crashes = crash_count_in_window(config_dir)
    if crashes <= 1:
        return 0.0
    return min(60.0, float(2 ** min(crashes - 1, 5)))


SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def load_crash_loop_entries(config_dir: Path) -> list[dict[str, Any]]:
    path = crash_loop_file(config_dir)
    if not path.exists():
        return []
    data = _load_document(path)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def crash_loop_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    crash_count = sum(1 for item in entries if item.get("event") == "crash")
    start_count = sum(1 for item in entries if item.get("event") == "start")
    return {
        "total": len(entries),
        "crash_count": crash_count,
        "start_count": start_count,
        "trend_sparkline": crash_loop_sparkline(entries),
    }


def crash_loop_sparkline(
    entries: list[dict[str, Any]],
    *,
    width: int = 20,
) -> str:
    recent = entries[-width:]
    if not recent:
        return ""
    values: list[int] = []
    for item in recent:
        event = item.get("event")
        if event == "crash":
            values.append(2)
        elif event == "start":
            values.append(1)
        else:
            values.append(0)
    if not any(values):
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


def crash_loop_trend_svg(
    entries: list[dict[str, Any]],
    *,
    width: int = 480,
    height: int = 160,
    padding: int = 28,
) -> str:
    import html

    if not entries:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<text x="{width // 2}" y="{height // 2}" text-anchor="middle" '
            f'fill="#9aa3b2" font-family="system-ui,sans-serif" font-size="12">'
            "No crash loop history</text></svg>"
        )

    plot_width = max(1, width - padding * 2)
    plot_height = max(1, height - padding * 2)
    bar_width = plot_width / max(len(entries), 1)
    bars: list[str] = []
    labels: list[str] = []
    crash_count = 0
    for position, item in enumerate(entries):
        is_crash = item.get("event") == "crash"
        if is_crash:
            crash_count += 1
        color = "#ff6b6b" if is_crash else "#4f8cff"
        x = padding + position * bar_width + bar_width * 0.15
        bar_w = max(4.0, bar_width * 0.7)
        y = padding + plot_height * 0.15
        bar_h = plot_height * 0.7
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'fill="{color}" rx="3"/>'
        )
        recorded_at = str(item.get("recorded_at", ""))
        label = recorded_at[5:16] if len(recorded_at) >= 16 else str(position + 1)
        labels.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 6}" text-anchor="middle" '
            f'fill="#9aa3b2" font-family="ui-monospace,Menlo,monospace" font-size="9">'
            f"{html.escape(label)}</text>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Crash loop trend">
  <rect width="{width}" height="{height}" fill="#0b0d12" rx="8"/>
  <line x1="{padding}" y1="{padding + plot_height}" x2="{width - padding}" y2="{padding + plot_height}" stroke="#232a36"/>
  <text x="{padding}" y="{padding - 8}" fill="#9aa3b2" font-family="system-ui,sans-serif" font-size="10">daemon events ({crash_count} crashes / {len(entries)} total)</text>
  {''.join(bars)}
  {''.join(labels)}
</svg>"""


def crash_loop_document(config_dir: Path, *, limit: int = 20) -> dict[str, Any]:
    entries = load_crash_loop_entries(config_dir)
    if limit is not None:
        entries = entries[-limit:]
    stats = crash_loop_stats(entries)
    return {
        "path": str(crash_loop_file(config_dir)),
        "stats": stats,
        "entries": entries,
    }


def apply_startup_crash_policy(config_dir: Path) -> dict[str, Any]:
    record_daemon_start(config_dir)
    backoff = startup_backoff_seconds(config_dir)
    if backoff > 0:
        time.sleep(backoff)
    if should_enter_safe_mode(config_dir):
        payload = activate_safe_mode(
            config_dir,
            reason="too_many_crashes",
        )
        os.environ["EXPANDO_SAFE_MODE"] = "1"
        return {"safe_mode": True, "backoff_seconds": backoff, **payload}
    os.environ.pop("EXPANDO_SAFE_MODE", None)
    clear_safe_mode(config_dir)
    return {"safe_mode": False, "backoff_seconds": backoff}
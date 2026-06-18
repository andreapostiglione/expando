from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .notarization_audit import NotarizationAuditReport, notarization_audit_report_to_dict

HISTORY_VERSION = 1
MAX_HISTORY_ENTRIES = 100


def history_file(config_dir: Path) -> Path:
    return config_dir / "notarize-audit-history.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_history_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": HISTORY_VERSION, "entries": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Notarization history must be a JSON object")
    data.setdefault("entries", [])
    return data


def _save_history_document(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _summarize_findings(report: NotarizationAuditReport) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for item in report.findings:
        status = item.status if item.status in counts else "warn"
        counts[status] += 1
    return counts


def record_notarization_audit(
    config_dir: Path,
    report: NotarizationAuditReport,
    *,
    app_bundle: Path | None = None,
    dmg: Path | None = None,
) -> dict[str, Any]:
    path = history_file(config_dir)
    data = _load_history_document(path)
    entry = {
        "recorded_at": _utc_now(),
        "ok": report.ok,
        "summary": _summarize_findings(report),
        "targets": {
            "app": str(app_bundle) if app_bundle is not None else None,
            "dmg": str(dmg) if dmg is not None else None,
        },
        "report": notarization_audit_report_to_dict(report),
    }
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    data["entries"] = entries[-MAX_HISTORY_ENTRIES:]
    data["version"] = HISTORY_VERSION
    _save_history_document(path, data)
    return entry


def load_notarization_history(config_dir: Path) -> list[dict[str, Any]]:
    data = _load_history_document(history_file(config_dir))
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def notarization_history_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "total": 0,
            "ok": 0,
            "failed": 0,
            "last_ok": None,
            "last_recorded_at": None,
            "recent_ok_rate": None,
        }

    ok_count = sum(1 for item in entries if item.get("ok"))
    recent = entries[-10:]
    recent_ok = sum(1 for item in recent if item.get("ok"))
    last = entries[-1]
    return {
        "total": len(entries),
        "ok": ok_count,
        "failed": len(entries) - ok_count,
        "last_ok": bool(last.get("ok")),
        "last_recorded_at": last.get("recorded_at"),
        "recent_ok_rate": round(recent_ok / len(recent), 2) if recent else None,
    }


def notarization_history_to_dict(
    config_dir: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    entries = load_notarization_history(config_dir)
    stats = notarization_history_stats(entries)
    recent = entries[-limit:] if limit is not None else entries
    return {
        "path": str(history_file(config_dir)),
        "stats": stats,
        "entries": recent,
    }


def doctor_notarization_lines(config_dir: Path) -> list[str]:
    from .i18n import t

    entries = load_notarization_history(config_dir)
    if not entries:
        return []

    stats = notarization_history_stats(entries)
    last = entries[-1]
    summary = last.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    recent_rate = (
        f"{int(stats['recent_ok_rate'] * 100)}%"
        if stats["recent_ok_rate"] is not None
        else t("notarize.history.na")
    )
    last_status = (
        t("notarize.history.ok") if last.get("ok") else t("notarize.history.fail")
    )
    lines = [
        t("doctor.notarize_history.title"),
        t("doctor.notarize_history.stats").format(
            total=stats["total"],
            ok=stats["ok"],
            failed=stats["failed"],
            recent_rate=recent_rate,
        ),
        t("doctor.notarize_history.last").format(
            recorded_at=last.get("recorded_at", "?"),
            status=last_status,
            pass_count=summary.get("pass", 0),
            warn_count=summary.get("warn", 0),
            fail_count=summary.get("fail", 0),
        ),
    ]
    if not last.get("ok"):
        lines.append(t("doctor.notarize_history.hint_fail"))
    return lines


def default_trend_svg_path(config_dir: Path) -> Path:
    return config_dir / "notarize-audit-trend.svg"


def notarization_history_trend_svg(
    entries: list[dict[str, Any]],
    *,
    width: int = 480,
    height: int = 160,
    padding: int = 28,
) -> str:
    if not entries:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<text x="{width // 2}" y="{height // 2}" text-anchor="middle" '
            f'fill="#9aa3b2" font-family="system-ui,sans-serif" font-size="12">'
            "No notarization history</text></svg>"
        )

    plot_width = max(1, width - padding * 2)
    plot_height = max(1, height - padding * 2)
    bar_width = plot_width / max(len(entries), 1)
    bars: list[str] = []
    labels: list[str] = []
    for position, item in enumerate(entries):
        ok = bool(item.get("ok"))
        color = "#3ecf8e" if ok else "#ff6b6b"
        x = padding + position * bar_width + bar_width * 0.15
        bar_w = max(4.0, bar_width * 0.7)
        y = padding + plot_height * 0.15
        bar_h = plot_height * 0.7
        bars.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'fill="{color}" rx="3"/>'
        )
        recorded_at = str(item.get("recorded_at", ""))
        label = recorded_at[5:10] if len(recorded_at) >= 10 else str(position + 1)
        labels.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 6}" text-anchor="middle" '
            f'fill="#9aa3b2" font-family="ui-monospace,Menlo,monospace" font-size="9">'
            f"{html.escape(label)}</text>"
        )

    ok_count = sum(1 for item in entries if item.get("ok"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Notarization audit trend">
  <rect width="{width}" height="{height}" fill="#0b0d12" rx="8"/>
  <line x1="{padding}" y1="{padding + plot_height}" x2="{width - padding}" y2="{padding + plot_height}" stroke="#232a36"/>
  <text x="{padding}" y="{padding - 8}" fill="#9aa3b2" font-family="system-ui,sans-serif" font-size="10">notarization audits ({ok_count}/{len(entries)} ok)</text>
  {''.join(bars)}
  {''.join(labels)}
</svg>"""


def write_notarization_history_trend_svg(
    config_dir: Path,
    path: Path | None = None,
    *,
    limit: int | None = None,
) -> Path:
    destination = (path or default_trend_svg_path(config_dir)).expanduser().resolve()
    entries = load_notarization_history(config_dir)
    if limit is not None:
        entries = entries[-limit:]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        notarization_history_trend_svg(entries) + "\n",
        encoding="utf-8",
    )
    return destination


def format_notarization_history_report(
    config_dir: Path,
    *,
    limit: int = 10,
) -> str:
    from .i18n import t

    path = history_file(config_dir)
    entries = load_notarization_history(config_dir)
    stats = notarization_history_stats(entries)

    lines = [
        t("notarize.history.title"),
        f"  {t('notarize.history.path')}: {path}",
        t("notarize.history.stats").format(
            total=stats["total"],
            ok=stats["ok"],
            failed=stats["failed"],
            recent_rate=(
                f"{int(stats['recent_ok_rate'] * 100)}%"
                if stats["recent_ok_rate"] is not None
                else t("notarize.history.na")
            ),
        ),
    ]
    if not entries:
        lines.append(t("notarize.history.empty"))
        return "\n".join(lines)

    lines.append(t("notarize.history.recent").format(limit=min(limit, len(entries))))
    for item in reversed(entries[-limit:]):
        recorded_at = str(item.get("recorded_at", "?"))
        status = t("notarize.history.ok") if item.get("ok") else t("notarize.history.fail")
        summary = item.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        lines.append(
            t("notarize.history.entry").format(
                recorded_at=recorded_at,
                status=status,
                pass_count=summary.get("pass", 0),
                warn_count=summary.get("warn", 0),
                fail_count=summary.get("fail", 0),
            )
        )
    return "\n".join(lines)
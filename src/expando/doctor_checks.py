from __future__ import annotations

import html
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ConfigCompileError, compile_matches, load_config
from .daemon import is_running
from .i18n import t, tf
from .match_utils import find_duplicate_literal_triggers
from .permissions import PermissionStatus, check_permissions, permissions_ready
from .crash_reporting import recent_crash_count
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
    crash_count = recent_crash_count(config_dir)
    if crash_count:
        warnings.append(tf("doctor.crash_warning", count=crash_count))

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

    from .notarization_history import doctor_notarization_lines

    notarize_lines = doctor_notarization_lines(report.config_dir)
    if notarize_lines:
        lines.append("")
        lines.extend(notarize_lines)

    from .hub_marketplace import doctor_marketplace_lines

    marketplace_lines = doctor_marketplace_lines()
    if marketplace_lines:
        lines.append("")
        lines.extend(marketplace_lines)

    return "\n".join(lines)


def doctor_report_to_dict(report: DoctorReport) -> dict[str, Any]:
    permissions: dict[str, Any] | None = None
    if report.permissions is not None:
        permissions = {
            "accessibility": report.permissions.accessibility,
            "input_monitoring": report.permissions.input_monitoring,
            "injection_ready": report.permissions.injection_ready,
        }
    runtime: dict[str, Any] | None = None
    if report.runtime is not None:
        runtime = {
            "mode": report.runtime.mode,
            "grant_label": report.runtime.grant_label,
            "grant_hint": report.runtime.grant_hint,
        }
    return {
        "ok": report.ok,
        "config_dir": str(report.config_dir),
        "running": report.running,
        "pid": report.pid,
        "process_count": report.process_count,
        "match_count": report.match_count,
        "duplicate_triggers": report.duplicate_triggers,
        "config_errors": report.config_errors,
        "warnings": report.warnings,
        "permissions": permissions,
        "runtime": runtime,
    }


def doctor_document(config_dir: Path) -> dict[str, Any]:
    report = run_doctor(config_dir)
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "doctor": doctor_report_to_dict(report),
    }


def doctor_combined_document(config_dir: Path) -> dict[str, Any]:
    from .hub_marketplace import doctor_marketplace_document

    payload = doctor_document(config_dir)
    payload["marketplace"] = doctor_marketplace_document()
    return payload


def doctor_full_document(
    config_dir: Path,
    *,
    history_limit: int = 10,
) -> dict[str, Any]:
    from .hub_marketplace import community_validation_document
    from .notarization_history import notarization_history_to_dict
    from .sparkle_benchmark_history import sparkle_benchmark_history_to_dict

    payload = doctor_combined_document(config_dir)
    payload["notarization_history"] = notarization_history_to_dict(
        config_dir,
        limit=history_limit,
    )
    payload["sparkle_benchmark_history"] = sparkle_benchmark_history_to_dict(
        limit=history_limit,
    )
    payload["community_validation"] = community_validation_document()
    return payload


def default_doctor_full_html_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "doctor-health.html"


def publish_site_config_dir(root: Path | None = None) -> Path:
    from .paths import package_root

    return (root or package_root()) / "default_config"


def default_publish_site_health_html_path(root: Path | None = None) -> Path:
    from .paths import package_root

    return (root or package_root()) / "docs" / "doctor-health.html"


def default_publish_site_health_json_path(root: Path | None = None) -> Path:
    from .paths import package_root

    return (root or package_root()) / "docs" / "hub" / "doctor-full.json"


def annotate_release_health_document(
    document: dict[str, Any],
    *,
    release_tag: str,
) -> dict[str, Any]:
    annotated = dict(document)
    annotated["publish_context"] = "release-ci"
    annotated["release_context"] = release_tag
    return annotated


def export_publish_site_health(
    root: Path | None = None,
    *,
    html_destination: Path | None = None,
    json_destination: Path | None = None,
    history_limit: int = 10,
) -> dict[str, Path]:
    import json

    config_dir = publish_site_config_dir(root)
    document = doctor_full_document(config_dir, history_limit=history_limit)
    document["publish_context"] = "github-pages"
    html_dest = (
        html_destination or default_publish_site_health_html_path(root)
    ).expanduser().resolve()
    json_dest = (
        json_destination or default_publish_site_health_json_path(root)
    ).expanduser().resolve()
    html_dest.parent.mkdir(parents=True, exist_ok=True)
    json_dest.parent.mkdir(parents=True, exist_ok=True)
    html_dest.write_text(build_doctor_full_html(document), encoding="utf-8")
    json_dest.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {"health_html": html_dest, "health_json": json_dest}


def _html_status_badge(ok: bool) -> tuple[str, str]:
    if ok:
        return "OK", "ok"
    return "Issues", "fail"


def _html_list_items(items: list[str]) -> str:
    if not items:
        return '<li class="empty">None</li>'
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items)


def build_doctor_full_html(document: dict[str, Any]) -> str:
    generated_at = html.escape(str(document.get("generated_at", "")))
    publish_context = str(document.get("publish_context", "") or "")
    publish_note = ""
    if publish_context == "github-pages":
        publish_note = (
            '<p class="meta">Publish-site snapshot using bundled '
            "<code>default_config</code> and repo release histories "
            "(not a live local daemon).</p>"
        )
    elif publish_context == "release-ci":
        release_tag = html.escape(str(document.get("release_context", "")))
        publish_note = (
            f'<p class="meta">Release CI snapshot from signed build '
            f"<code>{release_tag}</code> (post-sparkle doctor).</p>"
        )
    doctor = document.get("doctor", {})
    if not isinstance(doctor, dict):
        doctor = {}
    doctor_ok = bool(doctor.get("ok"))
    doctor_label, doctor_class = _html_status_badge(doctor_ok)

    permissions = doctor.get("permissions", {})
    if not isinstance(permissions, dict):
        permissions = {}
    runtime = doctor.get("runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}

    marketplace = document.get("marketplace", {})
    if not isinstance(marketplace, dict):
        marketplace = {}
    community_packages = marketplace.get("community_packages", [])
    if not isinstance(community_packages, list):
        community_packages = []
    package_rows = []
    for item in community_packages[:12]:
        if not isinstance(item, dict):
            continue
        package_rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(item.get('id', '')))}</code></td>"
            f"<td>{html.escape(str(item.get('name', '')))}</td>"
            "</tr>"
        )
    marketplace_table = (
        "\n".join(package_rows)
        if package_rows
        else '<tr><td colspan="2" class="empty">No community packages</td></tr>'
    )

    notarization = document.get("notarization_history", {})
    if not isinstance(notarization, dict):
        notarization = {}
    notarize_stats = notarization.get("stats", {})
    if not isinstance(notarize_stats, dict):
        notarize_stats = {}
    notarize_entries = notarization.get("entries", [])
    if not isinstance(notarize_entries, list):
        notarize_entries = []
    notarize_rows = []
    for item in notarize_entries[-8:]:
        if not isinstance(item, dict):
            continue
        summary = item.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        status = "OK" if item.get("ok") else "FAIL"
        row_class = "ok" if item.get("ok") else "fail"
        notarize_rows.append(
            f'<tr class="{row_class}">'
            f"<td>{html.escape(str(item.get('recorded_at', '')))}</td>"
            f"<td>{status}</td>"
            f"<td>{summary.get('pass', 0)}</td>"
            f"<td>{summary.get('warn', 0)}</td>"
            f"<td>{summary.get('fail', 0)}</td>"
            "</tr>"
        )
    notarize_table = (
        "\n".join(notarize_rows)
        if notarize_rows
        else '<tr><td colspan="5" class="empty">No notarization history</td></tr>'
    )

    sparkle = document.get("sparkle_benchmark_history", {})
    if not isinstance(sparkle, dict):
        sparkle = {}
    sparkle_stats = sparkle.get("stats", {})
    if not isinstance(sparkle_stats, dict):
        sparkle_stats = {}
    sparkle_entries = sparkle.get("entries", [])
    if not isinstance(sparkle_entries, list):
        sparkle_entries = []
    sparkle_rows = []
    for item in sparkle_entries[-8:]:
        if not isinstance(item, dict):
            continue
        benchmark = item.get("benchmark", {})
        if not isinstance(benchmark, dict):
            benchmark = {}
        helper_ms = benchmark.get("helper_check_ms")
        helper_text = f"{helper_ms:.2f}" if isinstance(helper_ms, (int, float)) else "n/a"
        row_class = "fail" if item.get("failed") else ("warn" if item.get("slow") else "ok")
        sparkle_rows.append(
            f'<tr class="{row_class}">'
            f"<td>{html.escape(str(item.get('recorded_at', '')))}</td>"
            f"<td>{html.escape(str(item.get('version', '')))}</td>"
            f"<td>{helper_text}</td>"
            f"<td>{'yes' if item.get('slow') else 'no'}</td>"
            "</tr>"
        )
    sparkle_table = (
        "\n".join(sparkle_rows)
        if sparkle_rows
        else '<tr><td colspan="4" class="empty">No sparkle benchmark history</td></tr>'
    )

    validation = document.get("community_validation", {})
    if not isinstance(validation, dict):
        validation = {}
    validation_ok = bool(validation.get("ok"))
    validation_label, validation_class = _html_status_badge(validation_ok)
    suggestions = validation.get("trigger_suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = []
    duplicate_count = len(validation.get("trigger_duplicates", {}) or {})
    collision_count = sum(
        len(items)
        for items in (validation.get("official_collisions", {}) or {}).values()
        if isinstance(items, list)
    )

    from .hub_marketplace import community_validation_html_fragments
    from .notarization_history import notarization_history_trend_svg
    from .sparkle_benchmark_history import sparkle_benchmark_trend_svg

    notarize_svg = notarization_history_trend_svg(notarize_entries)
    sparkle_svg = sparkle_benchmark_trend_svg(sparkle_entries)
    validation_tables = community_validation_html_fragments(validation)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Expando — Health Dashboard</title>
  <meta name="description" content="Full Expando health snapshot from expando doctor --full-html." />
  <style>
    :root {{
      --bg: #0b0d12;
      --panel: #141820;
      --text: #f4f6fb;
      --muted: #9aa3b2;
      --accent: #4f8cff;
      --border: #232a36;
      --ok: #3ecf8e;
      --fail: #ff6b6b;
      --warn: #f5c542;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1a2240 0%, transparent 60%),
                  var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 48px 24px 80px; }}
    h1, h2 {{ letter-spacing: -0.03em; }}
    h2 {{ margin-top: 40px; font-size: 1.2rem; }}
    .lead {{ color: var(--muted); max-width: 760px; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin: 12px 0 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin: 16px 0; }}
    .card {{
      background: rgba(20, 24, 32, 0.9);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}
    .card strong {{ display: block; font-size: 1.4rem; margin-bottom: 4px; }}
    .card span {{ color: var(--muted); font-size: 0.9rem; }}
    .badge {{
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 600;
      border: 1px solid var(--border);
    }}
    .badge.ok {{ color: var(--ok); border-color: rgba(62, 207, 142, 0.35); }}
    .badge.fail {{ color: var(--fail); border-color: rgba(255, 107, 107, 0.35); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0 8px;
      background: rgba(20, 24, 32, 0.9);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      font-size: 0.92rem;
    }}
    th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--muted); font-weight: 600; background: var(--panel); }}
    tr.ok td:nth-child(2) {{ color: var(--ok); }}
    tr.fail td:nth-child(2) {{ color: var(--fail); }}
    tr.warn td:nth-child(4) {{ color: var(--warn); }}
    td.empty {{ color: var(--muted); text-align: center; }}
    ul {{ margin: 8px 0; padding-left: 20px; }}
    li.empty {{ color: var(--muted); list-style: none; margin-left: -20px; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.88rem;
    }}
    pre {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px;
      overflow-x: auto;
      font-size: 0.88rem;
    }}
    .chart {{ margin: 16px 0; max-width: 100%; overflow-x: auto; }}
    .chart svg {{ display: block; max-width: 100%; height: auto; }}
    footer {{ margin-top: 48px; color: var(--muted); font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Expando Health Dashboard</h1>
    <p class="lead">Snapshot from <code>expando doctor --full-html</code>: daemon, marketplace, release histories, and community validation.</p>
    {publish_note}
    <p class="meta">Generated {generated_at} · Doctor <span class="badge {doctor_class}">{doctor_label}</span> · Community <span class="badge {validation_class}">{validation_label}</span></p>

    <div class="grid">
      <div class="card"><strong>{'yes' if doctor.get('running') else 'no'}</strong><span>Daemon running</span></div>
      <div class="card"><strong>{doctor.get('match_count', 0)}</strong><span>Loaded snippets</span></div>
      <div class="card"><strong>{marketplace.get('community_count', 0)}</strong><span>Community packages</span></div>
      <div class="card"><strong>{len(suggestions)}</strong><span>Trigger similarity warnings</span></div>
    </div>

    <h2>Doctor</h2>
    <table>
      <tbody>
        <tr><th>Config dir</th><td><code>{html.escape(str(doctor.get('config_dir', '')))}</code></td></tr>
        <tr><th>PID</th><td>{html.escape(str(doctor.get('pid', 'n/a')))}</td></tr>
        <tr><th>Accessibility</th><td>{html.escape(str(permissions.get('accessibility', 'unknown')))}</td></tr>
        <tr><th>Input monitoring</th><td>{html.escape(str(permissions.get('input_monitoring', 'unknown')))}</td></tr>
        <tr><th>Injection ready</th><td>{html.escape(str(permissions.get('injection_ready', 'unknown')))}</td></tr>
        <tr><th>Runtime</th><td>{html.escape(str(runtime.get('mode', 'unknown')))}</td></tr>
      </tbody>
    </table>
    <h3>Warnings</h3>
    <ul>{_html_list_items([str(item) for item in doctor.get('warnings', []) if isinstance(doctor.get('warnings'), list)])}</ul>
    <h3>Config errors</h3>
    <ul>{_html_list_items([str(item) for item in doctor.get('config_errors', []) if isinstance(doctor.get('config_errors'), list)])}</ul>

    <h2>Marketplace</h2>
    <table>
      <tbody>
        <tr><th>Remote URL</th><td>{html.escape(str(marketplace.get('remote_url') or 'disabled'))}</td></tr>
        <tr><th>Approved</th><td>{marketplace.get('approved_count', 0)}</td></tr>
        <tr><th>Pending diffs</th><td>{len(marketplace.get('pending_diffs', [])) if isinstance(marketplace.get('pending_diffs'), list) else 0}</td></tr>
      </tbody>
    </table>
    <table>
      <thead><tr><th>Community package</th><th>Name</th></tr></thead>
      <tbody>{marketplace_table}</tbody>
    </table>

    <h2>Notarization history</h2>
    <p class="meta">Runs: {notarize_stats.get('total', 0)} · OK: {notarize_stats.get('ok', 0)} · Failed: {notarize_stats.get('failed', 0)}</p>
    <div class="chart">{notarize_svg}</div>
    <table>
      <thead><tr><th>Recorded</th><th>Status</th><th>Pass</th><th>Warn</th><th>Fail</th></tr></thead>
      <tbody>{notarize_table}</tbody>
    </table>

    <h2>Sparkle benchmark history</h2>
    <p class="meta">Runs: {sparkle_stats.get('total', 0)} · Trend: <code>{html.escape(str(sparkle_stats.get('trend_sparkline', '')))}</code></p>
    <div class="chart">{sparkle_svg}</div>
    <table>
      <thead><tr><th>Recorded</th><th>Version</th><th>Helper ms</th><th>Slow</th></tr></thead>
      <tbody>{sparkle_table}</tbody>
    </table>

    <h2>Community validation</h2>
    <p class="meta">Packages validated: {len(validation.get('packages', [])) if isinstance(validation.get('packages'), list) else 0} · Duplicates: {duplicate_count} · Official collisions: {collision_count} · Similarity warnings: {len(suggestions)}</p>
    <h3>Packages</h3>
    <table>
      <thead><tr><th>Package</th><th>Snippets</th><th>Status</th></tr></thead>
      <tbody>{validation_tables["packages_table"]}</tbody>
    </table>
    <h3>Cross-package duplicates</h3>
    <table>
      <thead><tr><th>Trigger</th><th>Packages</th></tr></thead>
      <tbody>{validation_tables["duplicates_table"]}</tbody>
    </table>
    <h3>Official collisions</h3>
    <table>
      <thead><tr><th>Trigger</th><th>Community</th><th>Official</th></tr></thead>
      <tbody>{validation_tables["collisions_table"]}</tbody>
    </table>
    <h3>Similarity suggestions</h3>
    <table>
      <thead><tr><th>Community</th><th>Official</th><th>Score</th><th>Reason</th><th>Community pkg</th><th>Official pkg</th></tr></thead>
      <tbody>{validation_tables["suggestions_table"]}</tbody>
    </table>

    <h2>Regenerate</h2>
    <pre>expando doctor --full-html
expando doctor --full-html --full-html-output doctor-health.html
expando doctor --full-json --full-output doctor-full.json</pre>

    <footer>
      <a href="hub/community-validation.json">community-validation.json</a>
      · <a href="hub-maintainer.html">Maintainer portal</a>
      · <a href="hub-trigger-suggestions.html">Trigger dashboard</a>
      · <a href="hub-marketplace.html">Hub marketplace</a>
    </footer>
  </div>
</body>
</html>
"""


def write_doctor_full_html(
    config_dir: Path,
    destination: Path | None = None,
    *,
    history_limit: int = 10,
) -> Path:
    destination = (destination or default_doctor_full_html_path()).expanduser().resolve()
    document = doctor_full_document(config_dir, history_limit=history_limit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_doctor_full_html(document), encoding="utf-8")
    return destination


def _fmt_bool(value: bool | None) -> str:
    if value is None:
        return t("doctor.perm.unknown")
    return t("doctor.perm.granted") if value else t("doctor.perm.missing")
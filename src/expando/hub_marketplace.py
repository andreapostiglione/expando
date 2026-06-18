from __future__ import annotations

import html
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import urlopen

from .hub import HubPackage, _local_index_path, validate_hub_package_dir


MARKETPLACE_DOCS_URL = "https://github.com/andreapostiglione/expando/blob/main/docs/HUB_MARKETPLACE.md"
SUBMIT_ISSUE_URL = "https://github.com/andreapostiglione/expando/issues/new?template=hub-package.yml"
DEFAULT_MARKETPLACE_URL = (
    "https://andreapostiglione.github.io/expando/hub/marketplace.json"
)
MARKETPLACE_STATUSES = ("pending", "approved", "rejected")
ReviewAction = Literal["approve", "reject"]


@dataclass
class HubSubmission:
    package_id: str
    bundle_path: Path
    manifest: dict[str, object]
    match_count: int


def marketplace_index_url() -> str | None:
    override = os.environ.get("EXPANDO_HUB_MARKETPLACE_URL", "").strip()
    if override:
        return override
    disabled = os.environ.get("EXPANDO_HUB_MARKETPLACE_DISABLE", "").strip().lower()
    if disabled in {"1", "true", "yes"}:
        return None
    return DEFAULT_MARKETPLACE_URL


def marketplace_index_path() -> Path:
    override = os.environ.get("EXPANDO_HUB_MARKETPLACE_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return local_marketplace_index_path()


def local_marketplace_index_path() -> Path:
    return _local_index_path().parent / "marketplace.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_marketplace_document(path: Path | None = None) -> dict[str, Any]:
    path = path or marketplace_index_path()
    if not path.exists():
        return {"version": 1, "packages": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Marketplace index must be a JSON object")
    data.setdefault("packages", [])
    return data


def _save_marketplace_document(data: dict[str, Any], path: Path | None = None) -> Path:
    path = path or marketplace_index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    packages = data.get("packages", [])
    if isinstance(packages, list):
        packages.sort(key=lambda item: str(item.get("id", "")))
        data["packages"] = packages
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _package_entry_visible(data: dict[str, Any]) -> bool:
    status = str(data.get("status", "approved")).lower()
    return status == "approved"


def _entry_to_package(data: dict[str, Any]) -> HubPackage:
    return HubPackage.from_dict(data)


def _approved_packages_from_document(data: dict[str, Any]) -> list[HubPackage]:
    packages = data.get("packages", data) if isinstance(data, dict) else data
    if not isinstance(packages, list):
        raise RuntimeError("Marketplace index must contain a packages array")
    return [
        _entry_to_package(item)
        for item in packages
        if isinstance(item, dict) and _package_entry_visible(item)
    ]


def fetch_marketplace_packages() -> list[HubPackage]:
    merged: dict[str, HubPackage] = {}
    path = marketplace_index_path()
    if path.exists():
        data = _load_marketplace_document(path)
        for package in _approved_packages_from_document(data):
            merged[package.id] = package

    url = marketplace_index_url()
    if url:
        try:
            with urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            for package in _approved_packages_from_document(data):
                merged[package.id] = package
        except (URLError, json.JSONDecodeError, TimeoutError) as exc:
            if merged:
                return sorted(merged.values(), key=lambda item: item.id)
            raise RuntimeError(f"Could not fetch marketplace index: {exc}") from exc

    return sorted(merged.values(), key=lambda item: item.id)


def list_marketplace_queue(*, status: str | None = None) -> list[HubPackage]:
    data = _load_marketplace_document()
    entries: list[HubPackage] = []
    for item in data.get("packages", []):
        if not isinstance(item, dict):
            continue
        entry_status = str(item.get("status", "approved")).lower()
        if status is not None and entry_status != status.lower():
            continue
        entries.append(_entry_to_package(item))
    return entries


def queue_marketplace_submission(package_dir: Path) -> HubPackage:
    report = validate_hub_package_dir(package_dir)
    if not report.ok:
        raise ValueError("; ".join(report.errors))

    source = package_dir.expanduser().resolve()
    manifest = json.loads((source / "hub.json").read_text(encoding="utf-8"))
    package = HubPackage.from_dict(manifest)
    data = _load_marketplace_document()
    packages = [item for item in data.get("packages", []) if item.get("id") != package.id]
    packages.append(
        {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "author": package.author,
            "tags": package.tags or [],
            "status": "pending",
            "submitted_at": _utc_now(),
        }
    )
    data["packages"] = packages
    _save_marketplace_document(data)
    return HubPackage.from_dict(packages[-1])


def review_marketplace_package(
    package_id: str,
    action: ReviewAction,
    *,
    reviewer: str = "",
    note: str = "",
) -> HubPackage:
    if action not in ("approve", "reject"):
        raise ValueError(f"Unsupported review action: {action}")

    data = _load_marketplace_document()
    updated: dict[str, Any] | None = None
    packages: list[dict[str, Any]] = []
    for item in data.get("packages", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("id")) != package_id:
            packages.append(item)
            continue
        entry = dict(item)
        entry["status"] = "approved" if action == "approve" else "rejected"
        entry["reviewed_at"] = _utc_now()
        if reviewer:
            entry["reviewer"] = reviewer
        if note:
            entry["review_note"] = note
        updated = entry
        packages.append(entry)

    if updated is None:
        raise ValueError(f"Package {package_id!r} not found in marketplace queue")

    data["packages"] = packages
    _save_marketplace_document(data)
    return HubPackage.from_dict(updated)


def create_submission_bundle(package_dir: Path) -> HubSubmission:
    report = validate_hub_package_dir(package_dir)
    if not report.ok:
        raise ValueError("; ".join(report.errors))

    source = package_dir.expanduser().resolve()
    manifest = json.loads((source / "hub.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="expando-hub-submit-"))
    bundle = tmp / f"{report.package_id}.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.iterdir()):
            if path.name.startswith("."):
                continue
            if path.is_file():
                archive.write(path, arcname=path.name)
            elif path.is_dir():
                for child in sorted(path.rglob("*")):
                    if child.is_file():
                        archive.write(child, arcname=str(child.relative_to(source)))
    return HubSubmission(
        package_id=report.package_id,
        bundle_path=bundle,
        manifest=manifest,
        match_count=report.match_count,
    )


def publish_submission_bundle(submission: HubSubmission, destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(submission.bundle_path, destination)
    return destination


def format_submission_instructions(
    submission: HubSubmission,
    *,
    bundle_path: Path | None = None,
) -> str:
    from .i18n import t

    lines = [
        t("hub.submit.ok").format(
            package_id=submission.package_id,
            matches=submission.match_count,
        ),
    ]
    if bundle_path is not None:
        lines.append(t("hub.submit.bundle").format(path=bundle_path))
    lines.extend(
        [
            "",
            t("hub.submit.steps"),
            f"  1. {t('hub.submit.step_issue')}",
            f"     {SUBMIT_ISSUE_URL}",
            f"  2. {t('hub.submit.step_attach')}",
            f"  3. {t('hub.submit.step_docs')}",
            f"     {MARKETPLACE_DOCS_URL}",
            "",
            t("hub.submit.review_hint"),
            f"  expando hub review queue ./my-package",
            f"  expando hub review approve {submission.package_id}",
            "",
            t("hub.submit.maintainer"),
            f"  expando hub publish {submission.package_id} --bundle --register",
        ]
    )
    return "\n".join(lines)


def format_review_queue_report(packages: list[HubPackage], *, status: str) -> str:
    from .i18n import t

    if not packages:
        return t("hub.review.empty").format(status=status)
    lines = [t("hub.review.header").format(status=status, count=len(packages))]
    for package in packages:
        lines.append(f"  {package.id}: {package.name}")
        if package.submitted_at:
            lines.append(f"    {t('hub.review.submitted')}: {package.submitted_at}")
        if package.reviewed_at:
            lines.append(f"    {t('hub.review.reviewed')}: {package.reviewed_at}")
        if package.reviewer:
            lines.append(f"    {t('hub.review.reviewer')}: {package.reviewer}")
        if package.review_note:
            lines.append(f"    {t('hub.review.note')}: {package.review_note}")
    return "\n".join(lines)


def merged_registry_ids() -> set[str]:
    from .hub import fetch_registry

    ids = {package.id for package in fetch_registry()}
    try:
        ids.update(package.id for package in fetch_marketplace_packages())
    except RuntimeError:
        pass
    return ids


def _package_entry_dict(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in item.items()
        if key in {
            "id",
            "name",
            "description",
            "author",
            "tags",
            "status",
            "submitted_at",
            "reviewed_at",
            "reviewer",
            "review_note",
        }
    }


def marketplace_portal_stats() -> dict[str, Any]:
    data = _load_marketplace_document()
    counts = {status: 0 for status in MARKETPLACE_STATUSES}
    for item in data.get("packages", []):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "approved")).lower()
        if status in counts:
            counts[status] += 1
    remote_url = marketplace_index_url()
    remote_approved = 0
    if remote_url:
        try:
            remote_approved = len(fetch_marketplace_packages())
        except RuntimeError:
            remote_approved = -1
    return {
        "local_path": str(marketplace_index_path()),
        "remote_url": remote_url,
        "counts": counts,
        "total": len(data.get("packages", [])),
        "remote_approved": remote_approved,
    }


def build_publishable_portal_index() -> dict[str, Any]:
    data = _load_marketplace_document()
    packages = [
        _package_entry_dict(item)
        for item in data.get("packages", [])
        if isinstance(item, dict) and _package_entry_visible(item)
    ]
    packages.sort(key=lambda item: str(item.get("id", "")))
    return {
        "version": int(data.get("version", 1)),
        "description": str(
            data.get("description", "Expando hub marketplace — approved community packages")
        ),
        "updated_at": _utc_now(),
        "packages": packages,
    }


def export_portal_index(destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_publishable_portal_index()
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def fetch_remote_marketplace_document() -> dict[str, Any]:
    url = marketplace_index_url()
    if not url:
        raise RuntimeError(
            "Remote marketplace index is disabled — unset EXPANDO_HUB_MARKETPLACE_DISABLE "
            "or set EXPANDO_HUB_MARKETPLACE_URL"
        )
    try:
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch marketplace index: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Remote marketplace index must be a JSON object")
    data.setdefault("packages", [])
    return data


def sync_remote_marketplace_index(*, dry_run: bool = False) -> dict[str, int]:
    remote = fetch_remote_marketplace_document()
    local = _load_marketplace_document()
    local_by_id = {
        str(item.get("id")): item
        for item in local.get("packages", [])
        if isinstance(item, dict) and item.get("id")
    }
    stats = {"added": 0, "updated": 0, "unchanged": 0}
    merged = dict(local_by_id)

    for item in remote.get("packages", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        package_id = str(item["id"])
        incoming = _package_entry_dict(item)
        if package_id not in merged:
            merged[package_id] = incoming
            stats["added"] += 1
            continue
        if merged[package_id] != incoming:
            merged[package_id] = incoming
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    if dry_run:
        return stats

    local["packages"] = sorted(merged.values(), key=lambda item: str(item.get("id", "")))
    _save_marketplace_document(local)
    return stats


def default_portal_site_paths(root: Path | None = None) -> tuple[Path, Path]:
    from .paths import package_root as resolve_package_root

    base = root or resolve_package_root()
    return base / "docs" / "hub-marketplace.html", base / "docs" / "hub" / "marketplace.json"


def build_portal_site_html(payload: dict[str, Any]) -> str:
    packages = payload.get("packages", [])
    if not isinstance(packages, list):
        packages = []
    updated_at = str(payload.get("updated_at", ""))
    package_cards: list[str] = []
    for item in packages:
        if not isinstance(item, dict):
            continue
        package_id = html.escape(str(item.get("id", "")))
        name = html.escape(str(item.get("name", item.get("id", ""))))
        description = html.escape(str(item.get("description", "")))
        author = html.escape(str(item.get("author", "")))
        tags = item.get("tags", [])
        tag_html = ""
        if isinstance(tags, list) and tags:
            tag_html = "".join(
                f'<span class="tag">{html.escape(str(tag))}</span>'
                for tag in tags
                if str(tag).strip()
            )
        author_html = f'<p class="author">{author}</p>' if author else ""
        package_cards.append(
            "\n".join(
                [
                    '<article class="card package">',
                    f"  <h3>{name}</h3>",
                    f'  <p class="package-id"><code>{package_id}</code></p>',
                    f"  <p>{description}</p>",
                    author_html,
                    f'  <div class="tags">{tag_html}</div>' if tag_html else "",
                    '  <p class="install"><code>expando hub install '
                    f"{package_id}</code></p>",
                    "</article>",
                ]
            )
        )

    if package_cards:
        packages_html = "\n".join(package_cards)
    else:
        packages_html = (
            '<p class="empty">No approved community packages yet. '
            'Submit yours with <code>expando hub submit ./my-package</code>.</p>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Expando Hub Marketplace</title>
  <meta name="description" content="Approved community packages for Expando hub." />
  <style>
    :root {{
      --bg: #0b0d12;
      --panel: #141820;
      --text: #f4f6fb;
      --muted: #9aa3b2;
      --accent: #4f8cff;
      --accent-2: #7c5cff;
      --border: #232a36;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1a2240 0%, transparent 60%),
                  radial-gradient(900px 500px at 90% 0%, #2a1840 0%, transparent 55%),
                  var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 48px 24px 80px; }}
    h1 {{ font-size: 2.2rem; margin: 0 0 8px; letter-spacing: -0.03em; }}
    .lead {{ color: var(--muted); max-width: 720px; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin: 12px 0 32px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin: 24px 0 40px;
    }}
    .card {{
      background: rgba(20, 24, 32, 0.9);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
    }}
    .card h3 {{ margin: 0 0 8px; font-size: 1.05rem; }}
    .card p {{ margin: 0 0 8px; color: var(--muted); font-size: 0.95rem; }}
    .package-id code, .install code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.85rem;
    }}
    .author {{ font-size: 0.85rem; }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
    .tag {{
      font-size: 0.75rem;
      padding: 4px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
    }}
    .empty {{ color: var(--muted); }}
    pre {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.9rem;
    }}
    footer {{ margin-top: 56px; color: var(--muted); font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="index.html">← Expando home</a></p>
    <h1>Hub Marketplace</h1>
    <p class="lead">Approved community snippet packages for <code>expando hub install</code>.</p>
    <p class="meta">Updated {updated_at} · <a href="hub/marketplace.json">marketplace.json</a></p>

    <div class="grid">
      {packages_html}
    </div>

    <h2>Submit a package</h2>
    <pre>expando hub submit ./my-package
expando hub review approve &lt;package-id&gt;
expando hub portal publish-site</pre>

    <footer>
      <a href="https://github.com/andreapostiglione/expando/blob/main/docs/HUB_MARKETPLACE.md">Maintainer docs</a>
      · <a href="https://github.com/andreapostiglione/expando/issues/new?template=hub-package.yml">Submit via GitHub</a>
    </footer>
  </div>
</body>
</html>
"""


def publish_portal_site(
    *,
    html_path: Path | None = None,
    json_path: Path | None = None,
) -> dict[str, Path]:
    default_html, default_json = default_portal_site_paths()
    html_destination = (html_path or default_html).expanduser().resolve()
    json_destination = (json_path or default_json).expanduser().resolve()
    payload = build_publishable_portal_index()
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    html_destination.parent.mkdir(parents=True, exist_ok=True)
    html_destination.write_text(build_portal_site_html(payload), encoding="utf-8")
    return {"html": html_destination, "json": json_destination}


def format_portal_status_report(stats: dict[str, Any]) -> str:
    from .i18n import t

    lines = [
        t("hub.portal.title"),
        f"  {t('hub.portal.local')}: {stats['local_path']}",
    ]
    remote = stats.get("remote_url")
    if remote:
        lines.append(f"  {t('hub.portal.remote')}: {remote}")
        remote_approved = stats.get("remote_approved", 0)
        if remote_approved >= 0:
            lines.append(
                t("hub.portal.remote_approved").format(count=remote_approved)
            )
    else:
        lines.append(f"  {t('hub.portal.remote')}: {t('hub.portal.remote_none')}")

    counts = stats.get("counts", {})
    lines.append(
        t("hub.portal.counts").format(
            pending=counts.get("pending", 0),
            approved=counts.get("approved", 0),
            rejected=counts.get("rejected", 0),
            total=stats.get("total", 0),
        )
    )
    return "\n".join(lines)
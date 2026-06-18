from __future__ import annotations

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
MARKETPLACE_STATUSES = ("pending", "approved", "rejected")
ReviewAction = Literal["approve", "reject"]


@dataclass
class HubSubmission:
    package_id: str
    bundle_path: Path
    manifest: dict[str, object]
    match_count: int


def marketplace_index_url() -> str | None:
    return os.environ.get("EXPANDO_HUB_MARKETPLACE_URL") or None


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


def fetch_marketplace_packages() -> list[HubPackage]:
    url = marketplace_index_url()
    if url:
        try:
            with urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (URLError, json.JSONDecodeError, TimeoutError) as exc:
            raise RuntimeError(f"Could not fetch marketplace index: {exc}") from exc
        packages = data.get("packages", data) if isinstance(data, dict) else data
        if not isinstance(packages, list):
            raise RuntimeError("Marketplace index must contain a packages array")
        return [
            _entry_to_package(item)
            for item in packages
            if isinstance(item, dict) and _package_entry_visible(item)
        ]

    path = marketplace_index_path()
    if not path.exists():
        return []
    data = _load_marketplace_document(path)
    return [
        _entry_to_package(item)
        for item in data.get("packages", [])
        if isinstance(item, dict) and _package_entry_visible(item)
    ]


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
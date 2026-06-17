from __future__ import annotations

import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .hub import HubPackage, _local_index_path, validate_hub_package_dir


MARKETPLACE_DOCS_URL = "https://github.com/andreapostiglione/expando/blob/main/docs/HUB_MARKETPLACE.md"
SUBMIT_ISSUE_URL = "https://github.com/andreapostiglione/expando/issues/new?template=hub-package.yml"


@dataclass
class HubSubmission:
    package_id: str
    bundle_path: Path
    manifest: dict[str, object]
    match_count: int


def marketplace_index_url() -> str | None:
    return os.environ.get("EXPANDO_HUB_MARKETPLACE_URL") or None


def fetch_marketplace_packages() -> list[HubPackage]:
    url = marketplace_index_url()
    if not url:
        return []
    try:
        with urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as exc:
        raise RuntimeError(f"Could not fetch marketplace index: {exc}") from exc
    packages = data.get("packages", data) if isinstance(data, dict) else data
    if not isinstance(packages, list):
        raise RuntimeError("Marketplace index must contain a packages array")
    return [HubPackage.from_dict(item) for item in packages]


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
            t("hub.submit.maintainer"),
            f"  expando hub publish {submission.package_id} --bundle --register",
        ]
    )
    return "\n".join(lines)


def merged_registry_ids() -> set[str]:
    from .hub import fetch_registry

    ids = {package.id for package in fetch_registry()}
    try:
        ids.update(package.id for package in fetch_marketplace_packages())
    except RuntimeError:
        pass
    return ids


def local_marketplace_index_path() -> Path:
    return _local_index_path().parent / "marketplace.json"
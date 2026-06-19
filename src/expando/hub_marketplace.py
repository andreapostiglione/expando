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

import yaml

from .hub import (
    HubPackage,
    HubPublishReport,
    _local_index_path,
    _package_yaml_files,
    validate_hub_package_dir,
)
from .match_utils import extract_triggers


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


@dataclass
class ContributorSubmissionResult:
    package_id: str
    bundle_path: Path
    match_count: int
    queued: bool
    manifest: dict[str, object]


@dataclass
class SubmissionStatusReport:
    package_id: str
    found: bool
    status: str | None = None
    name: str = ""
    description: str = ""
    in_official_index: bool = False
    in_marketplace: bool = False
    submitted_at: str | None = None
    reviewed_at: str | None = None
    reviewer: str | None = None
    review_note: str | None = None


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


def init_contributor_package(
    parent_dir: Path,
    package_id: str,
    *,
    name: str,
    description: str,
    author: str = "Community",
    tags: list[str] | None = None,
    force: bool = False,
) -> Path:
    from .hub import _validate_package_id

    package_id = _validate_package_id(package_id)
    parent_dir = parent_dir.expanduser().resolve()
    parent_dir.mkdir(parents=True, exist_ok=True)
    package_dir = parent_dir / package_id
    if package_dir.exists() and any(package_dir.iterdir()) and not force:
        raise ValueError(f"Package directory already exists: {package_dir}")

    package_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": package_id,
        "name": name,
        "description": description,
        "author": author,
        "tags": tags or ["community"],
    }
    (package_dir / "hub.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    trigger = f":{package_id.replace('-', '')[:8]}"
    snippets = (
        "matches:\n"
        f"  - trigger: '{trigger}'\n"
        "    replace: |\n"
        f"      Snippet di esempio per {name}.\n"
        "      Modifica questo testo prima di inviare il package.\n"
    )
    (package_dir / "snippets.yml").write_text(snippets, encoding="utf-8")
    return package_dir


def community_packages_dir(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "packages" / "community"


def official_packages_dir(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "default_config" / "match" / "packages"


PENDING_METADATA_FIELDS = ("name", "description", "author", "tags", "status", "submitted_at")


@dataclass
class PendingMetadataDiff:
    package_id: str
    missing_local: bool
    remote_name: str
    remote_author: str
    changed_fields: list[tuple[str, str, str]]


TRIGGER_SIMILARITY_MIN_SCORE = 0.55


@dataclass
class TriggerSimilaritySuggestion:
    community_trigger: str
    official_trigger: str
    community_package: str
    official_package: str
    score: float
    reason: str


def _package_id_from_dir(package_dir: Path) -> str:
    manifest_path = package_dir / "hub.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            return str(manifest.get("id", package_dir.name))
        except json.JSONDecodeError:
            pass
    return package_dir.name


def _literal_triggers_for_package_dir(package_dir: Path) -> set[str]:
    triggers: set[str] = set()
    for yaml_path in _package_yaml_files(package_dir):
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        matches = data.get("matches", []) or []
        for raw in matches:
            if not isinstance(raw, dict) or raw.get("regex"):
                continue
            triggers.update(extract_triggers(raw))
    return triggers


def _normalize_trigger_body(trigger: str) -> str:
    return trigger.lstrip(":").casefold()


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for row_index, left_char in enumerate(left, start=1):
        current = [row_index]
        for col_index, right_char in enumerate(right, start=1):
            insert_cost = current[col_index - 1] + 1
            delete_cost = previous[col_index] + 1
            replace_cost = previous[col_index - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def _score_trigger_similarity(
    community_trigger: str,
    official_trigger: str,
) -> tuple[float, str] | None:
    if community_trigger == official_trigger:
        return None
    community_body = _normalize_trigger_body(community_trigger)
    official_body = _normalize_trigger_body(official_trigger)
    if not community_body or not official_body or community_body == official_body:
        return None

    min_len = min(len(community_body), len(official_body))
    max_len = max(len(community_body), len(official_body))
    ratio = min_len / max_len if max_len else 0.0

    if min_len >= 3:
        if community_body.startswith(official_body) or official_body.startswith(community_body):
            return round(0.82 + ratio * 0.16, 3), "prefix"
        if community_body.endswith(official_body) or official_body.endswith(community_body):
            return round(0.78 + ratio * 0.14, 3), "suffix"
        if community_body in official_body or official_body in community_body:
            return round(0.68 + ratio * 0.2, 3), "contains"

    distance = _levenshtein_distance(community_body, official_body)
    if distance <= 2 or (distance / max_len) <= 0.34:
        score = max(0.5, 1.0 - (distance / max_len))
        return round(score, 3), "levenshtein"
    return None


def _triggers_are_similar(community_trigger: str, official_trigger: str) -> bool:
    scored = _score_trigger_similarity(community_trigger, official_trigger)
    return scored is not None and scored[0] >= TRIGGER_SIMILARITY_MIN_SCORE


def _format_metadata_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def validate_community_hub_packages(root: Path | None = None) -> list[tuple[str, HubPublishReport]]:
    community_dir = community_packages_dir(root)
    if not community_dir.is_dir():
        return []
    reports: list[tuple[str, HubPublishReport]] = []
    for package_dir in sorted(community_dir.iterdir()):
        if package_dir.is_dir():
            reports.append((package_dir.name, validate_hub_package_dir(package_dir)))
    return reports


def find_cross_package_trigger_duplicates(root: Path | None = None) -> dict[str, list[str]]:
    community_dir = community_packages_dir(root)
    if not community_dir.is_dir():
        return {}

    trigger_packages: dict[str, list[str]] = {}
    for package_dir in sorted(community_dir.iterdir()):
        if not package_dir.is_dir():
            continue
        package_id = _package_id_from_dir(package_dir)
        for trigger in _literal_triggers_for_package_dir(package_dir):
            packages = trigger_packages.setdefault(trigger, [])
            if package_id not in packages:
                packages.append(package_id)

    return {
        trigger: packages
        for trigger, packages in sorted(trigger_packages.items())
        if len(packages) > 1
    }


def find_community_official_trigger_collisions(
    root: Path | None = None,
) -> dict[str, list[tuple[str, str]]]:
    from .hub import fetch_registry

    official_dir = official_packages_dir(root)
    official_triggers: dict[str, str] = {}
    for package in fetch_registry(include_marketplace=False):
        package_dir = official_dir / package.id
        if not package_dir.is_dir():
            continue
        for trigger in _literal_triggers_for_package_dir(package_dir):
            official_triggers.setdefault(trigger, package.id)

    community_dir = community_packages_dir(root)
    if not community_dir.is_dir():
        return {}

    collisions: dict[str, list[tuple[str, str]]] = {}
    for package_dir in sorted(community_dir.iterdir()):
        if not package_dir.is_dir():
            continue
        community_id = _package_id_from_dir(package_dir)
        for trigger in _literal_triggers_for_package_dir(package_dir):
            official_id = official_triggers.get(trigger)
            if official_id is None:
                continue
            pairs = collisions.setdefault(trigger, [])
            pair = (community_id, official_id)
            if pair not in pairs:
                pairs.append(pair)

    return {
        trigger: pairs
        for trigger, pairs in sorted(collisions.items())
    }


def find_community_official_trigger_similarities(
    root: Path | None = None,
) -> list[TriggerSimilaritySuggestion]:
    from .hub import fetch_registry

    official_dir = official_packages_dir(root)
    official_entries: list[tuple[str, str]] = []
    for package in fetch_registry(include_marketplace=False):
        package_dir = official_dir / package.id
        if not package_dir.is_dir():
            continue
        for trigger in _literal_triggers_for_package_dir(package_dir):
            official_entries.append((trigger, package.id))

    community_dir = community_packages_dir(root)
    if not community_dir.is_dir():
        return []

    suggestions: list[TriggerSimilaritySuggestion] = []
    seen: set[tuple[str, str, str, str]] = set()
    for package_dir in sorted(community_dir.iterdir()):
        if not package_dir.is_dir():
            continue
        community_id = _package_id_from_dir(package_dir)
        for community_trigger in _literal_triggers_for_package_dir(package_dir):
            for official_trigger, official_id in official_entries:
                if not _triggers_are_similar(community_trigger, official_trigger):
                    continue
                key = (community_trigger, official_trigger, community_id, official_id)
                if key in seen:
                    continue
                seen.add(key)
                scored = _score_trigger_similarity(community_trigger, official_trigger)
                if scored is None or scored[0] < TRIGGER_SIMILARITY_MIN_SCORE:
                    continue
                score, reason = scored
                suggestions.append(
                    TriggerSimilaritySuggestion(
                        community_trigger=community_trigger,
                        official_trigger=official_trigger,
                        community_package=community_id,
                        official_package=official_id,
                        score=score,
                        reason=reason,
                    )
                )
    suggestions.sort(
        key=lambda item: (
            -item.score,
            item.community_package,
            item.community_trigger,
            item.official_trigger,
        )
    )
    return suggestions


def trigger_similarity_suggestion_to_dict(item: TriggerSimilaritySuggestion) -> dict[str, object]:
    return {
        "community_trigger": item.community_trigger,
        "official_trigger": item.official_trigger,
        "community_package": item.community_package,
        "official_package": item.official_package,
        "score": item.score,
        "reason": item.reason,
    }


def format_marketplace_pending_diff_report() -> str:
    from .i18n import t

    diffs = marketplace_pending_metadata_diffs()
    if not diffs:
        return t("hub.portal.pending_diff.empty")
    lines = [t("hub.portal.pending_diff.title").format(count=len(diffs))]
    for diff in diffs[:20]:
        if diff.missing_local:
            lines.append(
                t("doctor.marketplace.pending_remote").format(
                    package_id=diff.package_id,
                    name=diff.remote_name,
                    author=diff.remote_author or t("benchmark.sparkle.none"),
                )
            )
            continue
        lines.append(t("doctor.marketplace.pending_changed").format(package_id=diff.package_id))
        for field, local_value, remote_value in diff.changed_fields[:3]:
            lines.append(
                t("doctor.marketplace.pending_field").format(
                    field=field,
                    local=local_value or t("benchmark.sparkle.none"),
                    remote=remote_value or t("benchmark.sparkle.none"),
                )
            )
    if len(diffs) > 20:
        lines.append(t("doctor.marketplace.pending_more").format(count=len(diffs) - 20))
    lines.append(t("doctor.marketplace.pending_hint"))
    return "\n".join(lines)


def pending_metadata_diff_to_dict(diff: PendingMetadataDiff) -> dict[str, Any]:
    return {
        "package_id": diff.package_id,
        "missing_local": diff.missing_local,
        "remote_name": diff.remote_name,
        "remote_author": diff.remote_author,
        "changed_fields": [
            {"field": field, "local": local_value, "remote": remote_value}
            for field, local_value, remote_value in diff.changed_fields
        ],
    }


def marketplace_pending_metadata_diff_document() -> dict[str, Any]:
    return {
        "version": 1,
        "generated_at": _utc_now(),
        "diffs": [pending_metadata_diff_to_dict(item) for item in marketplace_pending_metadata_diffs()],
    }


def write_marketplace_pending_diff_json(destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(marketplace_pending_metadata_diff_document(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def format_community_validation_report(
    reports: list[tuple[str, HubPublishReport]],
    *,
    trigger_duplicates: dict[str, list[str]] | None = None,
    official_collisions: dict[str, list[tuple[str, str]]] | None = None,
    trigger_suggestions: list[TriggerSimilaritySuggestion] | None = None,
) -> tuple[str, bool]:
    from .i18n import t

    if (
        not reports
        and not trigger_duplicates
        and not official_collisions
        and not trigger_suggestions
    ):
        return t("hub.validate.community.empty"), True

    lines: list[str] = []
    ok = True
    if reports:
        lines.append(t("hub.validate.community.header").format(count=len(reports)))
        for name, report in reports:
            if report.ok:
                lines.append(
                    t("hub.validate.community.ok").format(
                        package_id=report.package_id or name,
                        matches=report.match_count,
                    )
                )
                continue
            ok = False
            lines.append(t("hub.validate.community.fail").format(package_id=report.package_id or name))
            lines.extend(f"    - {error}" for error in report.errors)

    duplicates = trigger_duplicates or {}
    if duplicates:
        ok = False
        lines.append(t("hub.validate.community.duplicates.header").format(count=len(duplicates)))
        for trigger, packages in duplicates.items():
            lines.append(
                t("hub.validate.community.duplicates.item").format(
                    trigger=trigger,
                    packages=", ".join(packages),
                )
            )

    collisions = official_collisions or {}
    if collisions:
        ok = False
        lines.append(t("hub.validate.community.official.header").format(count=len(collisions)))
        for trigger, pairs in collisions.items():
            for community_id, official_id in pairs:
                lines.append(
                    t("hub.validate.community.official.item").format(
                        trigger=trigger,
                        community=community_id,
                        official=official_id,
                    )
                )

    suggestions = trigger_suggestions or []
    if suggestions:
        lines.append(t("hub.validate.community.similar.header").format(count=len(suggestions)))
        for item in suggestions:
            lines.append(
                t("hub.validate.community.similar.item").format(
                    community_trigger=item.community_trigger,
                    official_trigger=item.official_trigger,
                    community=item.community_package,
                    official=item.official_package,
                    score=f"{item.score:.2f}",
                    reason=item.reason,
                )
            )
    return "\n".join(lines), ok


def community_validation_document(root: Path | None = None) -> dict[str, Any]:
    reports = validate_community_hub_packages(root)
    trigger_duplicates = find_cross_package_trigger_duplicates(root)
    official_collisions = find_community_official_trigger_collisions(root)
    trigger_suggestions = find_community_official_trigger_similarities(root)
    validation_ok = (
        all(report.ok for _, report in reports)
        and not trigger_duplicates
        and not official_collisions
    )
    return {
        "version": 1,
        "generated_at": _utc_now(),
        "ok": validation_ok,
        "packages": [
            {
                "package_id": report.package_id or name,
                "ok": report.ok,
                "match_count": report.match_count,
                "errors": report.errors,
                "warnings": report.warnings,
            }
            for name, report in reports
        ],
        "trigger_duplicates": trigger_duplicates,
        "official_collisions": {
            trigger: [{"community": c, "official": o} for c, o in pairs]
            for trigger, pairs in official_collisions.items()
        },
        "trigger_suggestions": [
            trigger_similarity_suggestion_to_dict(item) for item in trigger_suggestions
        ],
    }


def default_trigger_suggestions_html_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "docs" / "hub-trigger-suggestions.html"


def community_validation_html_fragments(document: dict[str, Any]) -> dict[str, str]:
    packages = document.get("packages", [])
    if not isinstance(packages, list):
        packages = []
    package_rows: list[str] = []
    for item in packages:
        if not isinstance(item, dict):
            continue
        package_id = html.escape(str(item.get("package_id", "")))
        row_class = "ok" if item.get("ok") else "fail"
        match_count = int(item.get("match_count", 0))
        package_rows.append(
            f'<tr class="{row_class}"><td><code>{package_id}</code></td>'
            f"<td>{match_count}</td>"
            f'<td>{"✓" if item.get("ok") else "✗"}</td></tr>'
        )
    packages_table = (
        "\n".join(package_rows)
        if package_rows
        else '<tr><td colspan="3" class="empty">No community packages</td></tr>'
    )

    duplicates = document.get("trigger_duplicates", {})
    duplicate_rows: list[str] = []
    if isinstance(duplicates, dict):
        for trigger, packages_list in sorted(duplicates.items()):
            if not isinstance(packages_list, list):
                continue
            duplicate_rows.append(
                "<tr>"
                f"<td><code>{html.escape(str(trigger))}</code></td>"
                f"<td>{html.escape(', '.join(str(item) for item in packages_list))}</td>"
                "</tr>"
            )
    duplicates_table = (
        "\n".join(duplicate_rows)
        if duplicate_rows
        else '<tr><td colspan="2" class="empty">No cross-package duplicates</td></tr>'
    )

    collisions = document.get("official_collisions", {})
    collision_rows: list[str] = []
    if isinstance(collisions, dict):
        for trigger, pairs in sorted(collisions.items()):
            if not isinstance(pairs, list):
                continue
            for pair in pairs:
                if not isinstance(pair, dict):
                    continue
                collision_rows.append(
                    "<tr>"
                    f"<td><code>{html.escape(str(trigger))}</code></td>"
                    f"<td><code>{html.escape(str(pair.get('community', '')))}</code></td>"
                    f"<td><code>{html.escape(str(pair.get('official', '')))}</code></td>"
                    "</tr>"
                )
    collisions_table = (
        "\n".join(collision_rows)
        if collision_rows
        else '<tr><td colspan="3" class="empty">No official collisions</td></tr>'
    )

    suggestions = document.get("trigger_suggestions", [])
    suggestion_rows: list[str] = []
    if isinstance(suggestions, list):
        for item in suggestions:
            if not isinstance(item, dict):
                continue
            score = item.get("score", 0)
            score_pct = f"{float(score) * 100:.0f}%" if isinstance(score, (int, float)) else ""
            suggestion_rows.append(
                "<tr>"
                f"<td><code>{html.escape(str(item.get('community_trigger', '')))}</code></td>"
                f"<td><code>{html.escape(str(item.get('official_trigger', '')))}</code></td>"
                f"<td>{score_pct}</td>"
                f"<td>{html.escape(str(item.get('reason', '')))}</td>"
                f"<td><code>{html.escape(str(item.get('community_package', '')))}</code></td>"
                f"<td><code>{html.escape(str(item.get('official_package', '')))}</code></td>"
                "</tr>"
            )
    suggestions_table = (
        "\n".join(suggestion_rows)
        if suggestion_rows
        else '<tr><td colspan="6" class="empty">No similarity warnings</td></tr>'
    )

    return {
        "packages_table": packages_table,
        "duplicates_table": duplicates_table,
        "collisions_table": collisions_table,
        "suggestions_table": suggestions_table,
    }


def build_trigger_suggestions_html(document: dict[str, Any]) -> str:
    generated_at = html.escape(str(document.get("generated_at", "")))
    ok = bool(document.get("ok"))
    status_label = "OK" if ok else "Issues found"
    status_class = "ok" if ok else "fail"

    tables = community_validation_html_fragments(document)
    packages_table = tables["packages_table"]
    duplicates_table = tables["duplicates_table"]
    collisions_table = tables["collisions_table"]
    suggestions_table = tables["suggestions_table"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Expando Hub — Trigger Suggestions</title>
  <meta name="description" content="Community package validation and trigger similarity dashboard." />
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
    tr.ok td:last-child {{ color: var(--ok); }}
    tr.fail td:last-child {{ color: var(--fail); }}
    td.empty {{ color: var(--muted); text-align: center; }}
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
    footer {{ margin-top: 48px; color: var(--muted); font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="hub-marketplace.html">← Hub Marketplace</a></p>
    <h1>Community Trigger Dashboard</h1>
    <p class="lead">Validation status for <code>packages/community/</code> plus fuzzy similarity warnings against official hub triggers.</p>
    <p class="meta">Generated {generated_at} · <span class="badge {status_class}">{status_label}</span></p>

    <h2>Packages</h2>
    <table>
      <thead><tr><th>Package</th><th>Snippets</th><th>Status</th></tr></thead>
      <tbody>{packages_table}</tbody>
    </table>

    <h2>Cross-package duplicates (fail CI)</h2>
    <table>
      <thead><tr><th>Trigger</th><th>Packages</th></tr></thead>
      <tbody>{duplicates_table}</tbody>
    </table>

    <h2>Official collisions (fail CI)</h2>
    <table>
      <thead><tr><th>Trigger</th><th>Community</th><th>Official</th></tr></thead>
      <tbody>{collisions_table}</tbody>
    </table>

    <h2>Similarity suggestions (warning only)</h2>
    <table>
      <thead><tr><th>Community</th><th>Official</th><th>Score</th><th>Reason</th><th>Community pkg</th><th>Official pkg</th></tr></thead>
      <tbody>{suggestions_table}</tbody>
    </table>

    <h2>Regenerate</h2>
    <pre>expando hub validate-community --html
expando hub validate-community --html -o docs/hub-trigger-suggestions.html</pre>

    <footer>
      <a href="https://github.com/andreapostiglione/expando/blob/main/docs/HUB_MARKETPLACE.md">Maintainer docs</a>
    </footer>
  </div>
</body>
</html>
"""


def write_trigger_suggestions_html(destination: Path, root: Path | None = None) -> Path:
    destination = destination.expanduser().resolve()
    document = community_validation_document(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(build_trigger_suggestions_html(document), encoding="utf-8")
    return destination


def marketplace_pending_metadata_diffs() -> list[PendingMetadataDiff]:
    if not marketplace_index_url():
        return []
    try:
        remote = fetch_remote_marketplace_document()
        local = _load_marketplace_document()
    except RuntimeError:
        return []

    local_by_id = {
        str(item.get("id")): item
        for item in local.get("packages", [])
        if isinstance(item, dict) and item.get("id")
    }
    diffs: list[PendingMetadataDiff] = []
    for item in remote.get("packages", []):
        if not isinstance(item, dict) or not item.get("id"):
            continue
        package_id = str(item["id"])
        status = str(item.get("status", "approved")).lower()
        if status != "pending":
            continue

        local_item = local_by_id.get(package_id)
        if local_item is None:
            diffs.append(
                PendingMetadataDiff(
                    package_id=package_id,
                    missing_local=True,
                    remote_name=str(item.get("name", package_id)),
                    remote_author=str(item.get("author", "")),
                    changed_fields=[],
                )
            )
            continue

        changed: list[tuple[str, str, str]] = []
        for field in PENDING_METADATA_FIELDS:
            remote_value = _format_metadata_value(item.get(field))
            local_value = _format_metadata_value(local_item.get(field))
            if remote_value != local_value:
                changed.append((field, local_value, remote_value))
        if changed:
            diffs.append(
                PendingMetadataDiff(
                    package_id=package_id,
                    missing_local=False,
                    remote_name=str(item.get("name", package_id)),
                    remote_author=str(item.get("author", "")),
                    changed_fields=changed,
                )
            )
    diffs.sort(key=lambda entry: entry.package_id)
    return diffs


def marketplace_pending_sync_gaps() -> list[str]:
    if not marketplace_index_url():
        return []
    try:
        remote = fetch_remote_marketplace_document()
        local = _load_marketplace_document()
    except RuntimeError:
        return []

    local_ids = {
        str(item.get("id"))
        for item in local.get("packages", [])
        if isinstance(item, dict) and item.get("id")
    }
    gaps: list[str] = []
    for item in remote.get("packages", []):
        if not isinstance(item, dict):
            continue
        package_id = str(item.get("id", "")).strip()
        if not package_id:
            continue
        status = str(item.get("status", "approved")).lower()
        if status == "pending" and package_id not in local_ids:
            gaps.append(package_id)
    return sorted(gaps)


def marketplace_sync_preview() -> dict[str, Any] | None:
    if not marketplace_index_url():
        return None
    try:
        sync_stats = sync_remote_marketplace_index(dry_run=True)
    except RuntimeError:
        return None

    local = _load_marketplace_document()
    local_total = len(local.get("packages", []))
    local_approved = len(_approved_packages_from_document(local))
    remote_approved = len(_approved_packages_from_document(fetch_remote_marketplace_document()))
    return {
        "sync": sync_stats,
        "local_total": local_total,
        "local_approved": local_approved,
        "remote_approved": remote_approved,
    }


def doctor_marketplace_document(*, limit: int | None = None) -> dict[str, Any]:
    from .hub import fetch_registry

    remote_url = marketplace_index_url()
    document: dict[str, Any] = {
        "version": 1,
        "generated_at": _utc_now(),
        "remote_url": remote_url,
        "available": False,
        "approved_count": 0,
        "community_count": 0,
        "community_packages": [],
        "sync_preview": None,
        "pending_diffs": [],
        "pending_sync_gaps": [],
    }
    if not remote_url:
        return document

    try:
        approved = fetch_marketplace_packages()
    except RuntimeError as exc:
        document["error"] = str(exc)
        return document

    document["available"] = True
    official_ids = {item.id for item in fetch_registry(include_marketplace=False)}
    community = [item for item in approved if item.id not in official_ids]
    document["approved_count"] = len(approved)
    document["community_count"] = len(community)
    community_slice = community if limit is None else community[:limit]
    document["community_packages"] = [
        {
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "author": package.author,
            "status": package.status,
        }
        for package in community_slice
    ]
    if limit is not None and len(community) > limit:
        document["community_truncated"] = len(community) - limit

    preview = marketplace_sync_preview()
    if preview is not None:
        document["sync_preview"] = preview

    diffs = marketplace_pending_metadata_diffs()
    diff_slice = diffs if limit is None else diffs[:limit]
    document["pending_diffs"] = [pending_metadata_diff_to_dict(item) for item in diff_slice]
    if limit is not None and len(diffs) > limit:
        document["pending_diffs_truncated"] = len(diffs) - limit
    document["pending_sync_gaps"] = marketplace_pending_sync_gaps()
    return document


def doctor_marketplace_lines(*, limit: int = 5) -> list[str]:
    from .hub import fetch_registry
    from .i18n import t

    lines = [t("doctor.marketplace.title")]
    remote_url = marketplace_index_url()
    if remote_url:
        lines.append(f"  {t('doctor.marketplace.remote')}: {remote_url}")
    else:
        lines.append(f"  {t('doctor.marketplace.remote')}: {t('hub.portal.remote_none')}")

    try:
        approved = fetch_marketplace_packages()
    except RuntimeError:
        lines.append(f"  {t('doctor.marketplace.unavailable')}")
        return lines

    official_ids = {item.id for item in fetch_registry(include_marketplace=False)}
    community = [item for item in approved if item.id not in official_ids]
    lines.append(
        t("doctor.marketplace.counts").format(
            approved=len(approved),
            community=len(community),
        )
    )
    if not community:
        lines.append(f"  {t('doctor.marketplace.empty')}")
    else:
        lines.append(t("doctor.marketplace.community"))
        for package in community[:limit]:
            lines.append(
                t("doctor.marketplace.package").format(
                    package_id=package.id,
                    name=package.name,
                )
            )
        if len(community) > limit:
            lines.append(t("doctor.marketplace.more").format(count=len(community) - limit))
        lines.append(f"  {t('doctor.marketplace.hint')}")

    preview = marketplace_sync_preview()
    if preview is not None:
        sync = preview["sync"]
        lines.append(t("doctor.marketplace.sync"))
        lines.append(
            t("doctor.marketplace.sync_counts").format(
                local_total=preview["local_total"],
                local_approved=preview["local_approved"],
                remote_approved=preview["remote_approved"],
            )
        )
        lines.append(
            t("doctor.marketplace.sync_stats").format(
                added=sync["added"],
                updated=sync["updated"],
                unchanged=sync["unchanged"],
            )
        )
        if sync["added"] or sync["updated"]:
            lines.append(f"  {t('doctor.marketplace.sync_hint')}")

    pending_diffs = marketplace_pending_metadata_diffs()
    if pending_diffs:
        lines.append(t("doctor.marketplace.pending_diff"))
        for diff in pending_diffs[:limit]:
            if diff.missing_local:
                lines.append(
                    t("doctor.marketplace.pending_remote").format(
                        package_id=diff.package_id,
                        name=diff.remote_name,
                        author=diff.remote_author or t("benchmark.sparkle.none"),
                    )
                )
                continue
            lines.append(t("doctor.marketplace.pending_changed").format(package_id=diff.package_id))
            for field, local_value, remote_value in diff.changed_fields[:4]:
                lines.append(
                    t("doctor.marketplace.pending_field").format(
                        field=field,
                        local=local_value or t("benchmark.sparkle.none"),
                        remote=remote_value or t("benchmark.sparkle.none"),
                    )
                )
        if len(pending_diffs) > limit:
            lines.append(t("doctor.marketplace.pending_more").format(count=len(pending_diffs) - limit))
        lines.append(f"  {t('doctor.marketplace.pending_hint')}")

    return lines


def find_marketplace_package(package_id: str) -> HubPackage | None:
    data = _load_marketplace_document()
    for item in data.get("packages", []):
        if isinstance(item, dict) and str(item.get("id")) == package_id:
            return _entry_to_package(item)
    return None


def contributor_submission_status(package_id: str) -> SubmissionStatusReport:
    from .hub import fetch_registry

    official_ids = {item.id for item in fetch_registry(include_marketplace=False)}
    package = find_marketplace_package(package_id)
    if package is None:
        return SubmissionStatusReport(
            package_id=package_id,
            found=False,
            in_official_index=package_id in official_ids,
        )
    return SubmissionStatusReport(
        package_id=package_id,
        found=True,
        status=package.status,
        name=package.name,
        description=package.description,
        in_official_index=package_id in official_ids,
        in_marketplace=True,
        submitted_at=package.submitted_at,
        reviewed_at=package.reviewed_at,
        reviewer=package.reviewer,
        review_note=package.review_note,
    )


def contributor_submission_status_to_dict(report: SubmissionStatusReport) -> dict[str, object]:
    return {
        "package_id": report.package_id,
        "found": report.found,
        "status": report.status,
        "name": report.name,
        "description": report.description,
        "in_official_index": report.in_official_index,
        "in_marketplace": report.in_marketplace,
        "submitted_at": report.submitted_at,
        "reviewed_at": report.reviewed_at,
        "reviewer": report.reviewer,
        "review_note": report.review_note,
    }


def format_submission_status_report(report: SubmissionStatusReport) -> str:
    from .i18n import t

    if not report.found:
        if report.in_official_index:
            return t("hub.submit.status.official").format(package_id=report.package_id)
        return t("hub.submit.status.not_found").format(package_id=report.package_id)

    lines = [
        t("hub.submit.status.header").format(
            package_id=report.package_id,
            status=report.status or "unknown",
        ),
        f"  {report.name}: {report.description}",
    ]
    if report.submitted_at:
        lines.append(t("hub.submit.status.submitted").format(when=report.submitted_at))
    if report.reviewed_at:
        lines.append(t("hub.submit.status.reviewed").format(when=report.reviewed_at))
    if report.reviewer:
        lines.append(t("hub.submit.status.reviewer").format(name=report.reviewer))
    if report.review_note:
        lines.append(t("hub.submit.status.note").format(note=report.review_note))
    if report.in_official_index:
        lines.append(t("hub.submit.status.official_index"))
    return "\n".join(lines)


def run_contributor_submission_workflow(
    package_dir: Path,
    *,
    bundle_path: Path,
    queue: bool = False,
) -> ContributorSubmissionResult:
    submission = create_submission_bundle(package_dir)
    destination = publish_submission_bundle(submission, bundle_path)
    if queue:
        queue_marketplace_submission(package_dir)
    return ContributorSubmissionResult(
        package_id=submission.package_id,
        bundle_path=destination,
        match_count=submission.match_count,
        queued=queue,
        manifest=submission.manifest,
    )


def contributor_submission_to_dict(result: ContributorSubmissionResult) -> dict[str, object]:
    return {
        "package_id": result.package_id,
        "bundle_path": str(result.bundle_path),
        "match_count": result.match_count,
        "queued": result.queued,
        "manifest": result.manifest,
    }


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
            f"  expando hub submit status {submission.package_id}",
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


def build_portal_site_html(
    payload: dict[str, Any],
    *,
    validation: dict[str, Any] | None = None,
) -> str:
    packages = payload.get("packages", [])
    if not isinstance(packages, list):
        packages = []
    updated_at = str(payload.get("updated_at", ""))
    validation_doc = validation or {}
    validation_ok = bool(validation_doc.get("ok"))
    validation_label = "OK" if validation_ok else "Issues"
    validation_class = "ok" if validation_ok else "fail"
    suggestions = validation_doc.get("trigger_suggestions", [])
    suggestion_count = len(suggestions) if isinstance(suggestions, list) else 0
    duplicate_count = len(validation_doc.get("trigger_duplicates", {}) or {})
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
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 600;
      border: 1px solid var(--border);
    }}
    .badge.ok {{ color: #3ecf8e; border-color: rgba(62, 207, 142, 0.35); }}
    .badge.fail {{ color: #ff6b6b; border-color: rgba(255, 107, 107, 0.35); }}
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
    <p class="meta">Updated {updated_at} · Community validation <span class="badge {validation_class}">{validation_label}</span> · duplicates={duplicate_count} · similarity warnings={suggestion_count} · <a href="doctor-health.html">Health dashboard</a> · <a href="hub/index.json">hub index</a> · <a href="hub/marketplace.json">marketplace.json</a> · <a href="hub/community-validation.json">community-validation.json</a> · <a href="hub-maintainer.html">Maintainer portal</a> · <a href="hub-trigger-suggestions.html">Trigger dashboard</a></p>

    <div class="grid">
      {packages_html}
    </div>

    <h2>Community validation</h2>
    <p class="lead">Fuzzy trigger similarity warnings, cross-package duplicates, and official collision checks for <code>packages/community/</code>.</p>
    <p><a href="hub-trigger-suggestions.html">Open trigger dashboard →</a></p>

    <h2>Submit a package</h2>
    <pre>expando hub submit ./my-package
expando hub review approve &lt;package-id&gt;
expando hub portal publish-site</pre>

    <footer>
      <a href="hub/index.json">hub/index.json</a>
      · <a href="doctor-health.html">doctor-health.html</a>
      · <a href="hub/doctor-full.json">doctor-full.json</a>
      · <a href="hub/community-validation.json">community-validation.json</a>
      · <a href="https://github.com/andreapostiglione/expando/blob/main/docs/HUB_MARKETPLACE.md">Maintainer docs</a>
      · <a href="https://github.com/andreapostiglione/expando/issues/new?template=hub-package.yml">Submit via GitHub</a>
    </footer>
  </div>
</body>
</html>
"""


def default_maintainer_hub_html_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "docs" / "hub-maintainer.html"


def default_community_validation_json_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "docs" / "hub" / "community-validation.json"


def export_community_validation_json(destination: Path, root: Path | None = None) -> Path:
    destination = destination.expanduser().resolve()
    document = community_validation_document(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def build_maintainer_hub_html(
    *,
    updated_at: str | None = None,
    validation: dict[str, Any] | None = None,
) -> str:
    timestamp = updated_at or _utc_now()
    escaped_updated = html.escape(timestamp)
    validation_doc = validation or {}
    validation_ok = bool(validation_doc.get("ok"))
    validation_label = "OK" if validation_ok else "Issues"
    validation_class = "ok" if validation_ok else "fail"
    packages = validation_doc.get("packages", [])
    package_count = len(packages) if isinstance(packages, list) else 0
    suggestions = validation_doc.get("trigger_suggestions", [])
    suggestion_count = len(suggestions) if isinstance(suggestions, list) else 0
    duplicate_count = len(validation_doc.get("trigger_duplicates", {}) or {})
    collision_count = sum(
        len(items)
        for items in (validation_doc.get("official_collisions", {}) or {}).values()
        if isinstance(items, list)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Expando Hub — Maintainer Portal</title>
  <meta name="description" content="Maintainer tools for Expando hub marketplace and community validation." />
  <style>
    :root {{
      --bg: #0b0d12;
      --panel: #141820;
      --text: #f4f6fb;
      --muted: #9aa3b2;
      --accent: #4f8cff;
      --border: #232a36;
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
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 48px 24px 80px; }}
    h1, h2 {{ letter-spacing: -0.03em; }}
    h2 {{ margin-top: 40px; font-size: 1.2rem; }}
    .lead {{ color: var(--muted); max-width: 760px; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin: 12px 0 24px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }}
    .card {{
      background: rgba(20, 24, 32, 0.9);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
    }}
    .card h3 {{ margin: 0 0 8px; font-size: 1.05rem; }}
    .card p {{ margin: 0 0 12px; color: var(--muted); font-size: 0.95rem; }}
    pre {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.9rem;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 600;
      border: 1px solid var(--border);
    }}
    .badge.ok {{ color: #3ecf8e; border-color: rgba(62, 207, 142, 0.35); }}
    .badge.fail {{ color: #ff6b6b; border-color: rgba(255, 107, 107, 0.35); }}
    footer {{ margin-top: 56px; color: var(--muted); font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="index.html">← Expando home</a></p>
    <h1>Maintainer Portal</h1>
    <p class="lead">Tools for reviewing community packages, publishing the hub index, and monitoring release health.</p>
    <p class="meta">Updated {escaped_updated} · Community validation <span class="badge {validation_class}">{validation_label}</span> · packages={package_count} · similarity warnings={suggestion_count}</p>

    <div class="grid">
      <div class="card">
        <h3>Hub Marketplace</h3>
        <p>Approved community packages for <code>expando hub install</code>.</p>
        <p><a href="hub-marketplace.html">Open marketplace →</a></p>
      </div>
      <div class="card">
        <h3>Trigger Dashboard</h3>
        <p>Community validation, duplicate lint, and fuzzy similarity warnings.</p>
        <p>Duplicates: {duplicate_count} · official collisions: {collision_count}</p>
        <p><a href="hub-trigger-suggestions.html">Open trigger dashboard →</a></p>
      </div>
      <div class="card">
        <h3>Health Dashboard</h3>
        <p>Publish-site snapshot from <code>expando doctor --full-html</code> with embedded release trend charts.</p>
        <p><a href="doctor-health.html">Open health dashboard →</a></p>
      </div>
    </div>

    <h2>Publish GitHub Pages</h2>
    <pre>expando hub portal publish-site</pre>

    <h2>Validate community packages</h2>
    <pre>expando hub validate-community
expando hub validate-community --html
expando doctor --full-json
expando doctor --full-html</pre>

    <footer>
      <a href="hub/index.json">hub/index.json</a>
      · <a href="doctor-health.html">doctor-health.html</a>
      · <a href="hub/doctor-full.json">doctor-full.json</a>
      · <a href="hub/marketplace.json">marketplace.json</a>
      · <a href="hub/community-validation.json">community-validation.json</a>
      · <a href="https://github.com/andreapostiglione/expando/issues/new?template=hub-package.yml">Submit package</a>
    </footer>
  </div>
</body>
</html>
"""


def _publish_site_skip_health() -> bool:
    import os

    return os.environ.get("EXPANDO_PUBLISH_SITE_SKIP_HEALTH", "").lower() in {
        "1",
        "true",
        "yes",
    }


def default_hub_index_json_path(root: Path | None = None) -> Path:
    from .paths import package_root

    base = root or package_root()
    return base / "docs" / "hub" / "index.json"


def build_hub_index_document(
    *,
    marketplace_payload: dict[str, Any],
    validation_document: dict[str, Any],
    health_json_path: Path,
) -> dict[str, Any]:
    packages = marketplace_payload.get("packages", [])
    package_count = len(packages) if isinstance(packages, list) else 0
    health_meta: dict[str, Any] = {}
    if health_json_path.exists():
        try:
            health_doc = json.loads(health_json_path.read_text(encoding="utf-8"))
            if isinstance(health_doc, dict):
                doctor = health_doc.get("doctor", {})
                health_meta = {
                    "generated_at": health_doc.get("generated_at"),
                    "publish_context": health_doc.get("publish_context"),
                    "release_context": health_doc.get("release_context"),
                    "doctor_ok": doctor.get("ok") if isinstance(doctor, dict) else None,
                }
        except (OSError, json.JSONDecodeError):
            health_meta = {}

    return {
        "version": 1,
        "generated_at": _utc_now(),
        "artifacts": [
            {
                "id": "marketplace",
                "path": "hub/marketplace.json",
                "title": "Hub Marketplace",
                "updated_at": marketplace_payload.get("updated_at"),
                "package_count": package_count,
            },
            {
                "id": "community-validation",
                "path": "hub/community-validation.json",
                "title": "Community Validation",
                "updated_at": validation_document.get("generated_at"),
                "ok": validation_document.get("ok"),
            },
            {
                "id": "doctor-full",
                "path": "hub/doctor-full.json",
                "title": "Release Health",
                **health_meta,
            },
        ],
        "pages": [
            {
                "id": "doctor-health",
                "path": "doctor-health.html",
                "title": "Health Dashboard",
            },
            {
                "id": "hub-marketplace",
                "path": "hub-marketplace.html",
                "title": "Hub Marketplace",
            },
            {
                "id": "hub-maintainer",
                "path": "hub-maintainer.html",
                "title": "Maintainer Portal",
            },
            {
                "id": "hub-trigger-suggestions",
                "path": "hub-trigger-suggestions.html",
                "title": "Trigger Dashboard",
            },
        ],
    }


def export_hub_index_json(
    destination: Path,
    *,
    marketplace_payload: dict[str, Any],
    validation_document: dict[str, Any],
    health_json_path: Path,
) -> Path:
    destination = destination.expanduser().resolve()
    document = build_hub_index_document(
        marketplace_payload=marketplace_payload,
        validation_document=validation_document,
        health_json_path=health_json_path,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def publish_portal_site(
    *,
    html_path: Path | None = None,
    json_path: Path | None = None,
    suggestions_html_path: Path | None = None,
    maintainer_html_path: Path | None = None,
    validation_json_path: Path | None = None,
    health_html_path: Path | None = None,
    health_json_path: Path | None = None,
    hub_index_json_path: Path | None = None,
    root: Path | None = None,
) -> dict[str, Path]:
    default_html, default_json = default_portal_site_paths()
    html_destination = (html_path or default_html).expanduser().resolve()
    json_destination = (json_path or default_json).expanduser().resolve()
    suggestions_destination = (
        suggestions_html_path or default_trigger_suggestions_html_path()
    ).expanduser().resolve()
    maintainer_destination = (
        maintainer_html_path or default_maintainer_hub_html_path()
    ).expanduser().resolve()
    validation_destination = (
        validation_json_path or default_community_validation_json_path()
    ).expanduser().resolve()
    payload = build_publishable_portal_index()
    validation_document = community_validation_document()
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    html_destination.parent.mkdir(parents=True, exist_ok=True)
    html_destination.write_text(
        build_portal_site_html(payload, validation=validation_document),
        encoding="utf-8",
    )
    write_trigger_suggestions_html(suggestions_destination)
    maintainer_destination.parent.mkdir(parents=True, exist_ok=True)
    maintainer_destination.write_text(
        build_maintainer_hub_html(
            updated_at=str(payload.get("updated_at", "")),
            validation=validation_document,
        ),
        encoding="utf-8",
    )
    export_community_validation_json(validation_destination, root=root)
    from .doctor_checks import (
        default_publish_site_health_html_path,
        default_publish_site_health_json_path,
        export_publish_site_health,
    )

    resolved_health_html = (
        health_html_path or default_publish_site_health_html_path(root)
    ).expanduser().resolve()
    resolved_health_json = (
        health_json_path or default_publish_site_health_json_path(root)
    ).expanduser().resolve()
    if _publish_site_skip_health():
        health_paths = {
            "health_html": resolved_health_html,
            "health_json": resolved_health_json,
        }
    else:
        health_paths = export_publish_site_health(
            root,
            html_destination=resolved_health_html,
            json_destination=resolved_health_json,
        )
    hub_index_destination = (
        hub_index_json_path or default_hub_index_json_path(root)
    ).expanduser().resolve()
    export_hub_index_json(
        hub_index_destination,
        marketplace_payload=payload,
        validation_document=validation_document,
        health_json_path=health_paths["health_json"],
    )
    return {
        "html": html_destination,
        "json": json_destination,
        "suggestions_html": suggestions_destination,
        "maintainer_html": maintainer_destination,
        "validation_json": validation_destination,
        "health_html": health_paths["health_html"],
        "health_json": health_paths["health_json"],
        "hub_index_json": hub_index_destination,
    }


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
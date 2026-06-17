from __future__ import annotations

import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from . import __version__
from .i18n import t
from .notifications import notify
from .version_utils import is_newer, normalize_version, version_tuple

logger = logging.getLogger(__name__)

SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"
DEFAULT_FEED_URL = (
    "https://raw.githubusercontent.com/andreapostiglione/expando/main/appcast.xml"
)
CHECK_INTERVAL_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    download_url: str
    release_notes: str = ""
    ed_signature: str = ""


@dataclass
class UpdateCheckResult:
    current_version: str
    available: UpdateInfo | None = None
    error: str | None = None


def default_feed_url() -> str:
    return os.environ.get("EXPANDO_UPDATE_FEED_URL", DEFAULT_FEED_URL)


def _last_check_file(config_dir: Path) -> Path:
    return config_dir / ".last_update_check"


def _should_check(config_dir: Path, *, force: bool) -> bool:
    if force:
        return True
    marker = _last_check_file(config_dir)
    if not marker.exists():
        return True
    try:
        last = float(marker.read_text(encoding="utf-8").strip())
    except ValueError:
        return True
    return time.time() - last >= CHECK_INTERVAL_SECONDS


def _record_check(config_dir: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    _last_check_file(config_dir).write_text(str(time.time()), encoding="utf-8")


def fetch_appcast(feed_url: str | None = None) -> str:
    url = feed_url or default_feed_url()
    with urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8")


def parse_appcast(xml_text: str) -> list[UpdateInfo]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    ns = {"sparkle": SPARKLE_NS}
    updates: list[UpdateInfo] = []
    for item in channel.findall("item"):
        version_node = item.find("sparkle:shortVersionString", ns)
        if version_node is None or not version_node.text:
            version_node = item.find("sparkle:version", ns)
        if version_node is None or not version_node.text:
            title = item.findtext("title", default="")
            version = title.removeprefix("Version ").strip()
        else:
            version = version_node.text.strip()

        enclosure = item.find("enclosure")
        if enclosure is None:
            continue
        download_url = enclosure.attrib.get("url", "").strip()
        if not download_url:
            continue

        notes = item.findtext("description", default="").strip()
        signature = enclosure.attrib.get(f"{{{SPARKLE_NS}}}edSignature", "").strip()
        updates.append(
            UpdateInfo(
                version=normalize_version(version),
                download_url=download_url,
                release_notes=notes,
                ed_signature=signature,
            )
        )
    return updates


def latest_update(updates: list[UpdateInfo]) -> UpdateInfo | None:
    if not updates:
        return None
    return max(updates, key=lambda item: version_tuple(item.version))


def check_for_updates(
    config_dir: Path,
    *,
    current_version: str | None = None,
    feed_url: str | None = None,
    force: bool = False,
    notify_user: bool = False,
    open_download_page: bool = False,
) -> UpdateCheckResult:
    current = normalize_version(current_version or __version__)
    if not _should_check(config_dir, force=force):
        return UpdateCheckResult(current_version=current)

    url = feed_url or default_feed_url()
    try:
        updates = parse_appcast(fetch_appcast(url))
    except (URLError, ET.ParseError, TimeoutError, ValueError) as exc:
        logger.warning("Update check failed: %s", exc)
        return UpdateCheckResult(current_version=current, error=str(exc))

    _record_check(config_dir)
    latest = latest_update(updates)
    if latest is None or not is_newer(latest.version, current):
        return UpdateCheckResult(current_version=current)

    if notify_user:
        _notify_update_available(latest, open_download=open_download_page)
    return UpdateCheckResult(current_version=current, available=latest)


def check_for_updates_silent(config_dir: Path) -> None:
    from .config import load_config

    try:
        config = load_config(config_dir)
        if not config.app.check_updates:
            return
        feed = config.app.update_feed_url or None
        check_for_updates(
            config_dir,
            feed_url=feed,
            notify_user=True,
            open_download_page=False,
        )
    except Exception:
        logger.exception("Silent update check failed")


def _notify_update_available(info: UpdateInfo, *, open_download: bool = False) -> None:
    message = t("update.available").format(version=info.version)
    notify(t("update.title"), message)
    if open_download:
        open_download_url(info.download_url)


def open_download_url(url: str) -> None:
    import platform
    import subprocess

    if platform.system() != "Darwin":
        return
    subprocess.run(["open", url], check=False)
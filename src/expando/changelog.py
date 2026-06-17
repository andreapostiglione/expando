from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from . import __version__
from .i18n import t
from .notifications import notify
from .version_utils import is_newer, normalize_version

logger = logging.getLogger(__name__)


def _marker_file(config_dir: Path) -> Path:
    return config_dir / ".last_seen_version"


def maybe_show_whats_new(config_dir: Path, *, current_version: str | None = None) -> None:
    current = normalize_version(current_version or __version__)
    marker = _marker_file(config_dir)
    previous = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""

    if previous and not is_newer(current, previous):
        return
    if previous and normalize_version(previous) == current:
        return
    if not previous:
        config_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text(current, encoding="utf-8")
        return

    message = t("changelog.new_version").format(version=current)
    notify(t("changelog.title"), message)
    _open_release_page(current)

    config_dir.mkdir(parents=True, exist_ok=True)
    marker.write_text(current, encoding="utf-8")


def _open_release_page(version: str) -> None:
    import platform

    if platform.system() != "Darwin":
        return
    url = f"https://github.com/andreapostiglione/expando/releases/tag/v{version}"
    subprocess.run(["open", url], check=False)
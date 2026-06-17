from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path

from .paths import app_bundle_path, package_root

logger = logging.getLogger(__name__)

SPARKLE_HELPER_NAME = "expando-sparkle"


def resolve_distribution_app_bundle() -> Path | None:
    override = os.environ.get("EXPANDO_APP_BUNDLE", "").strip()
    if override:
        path = Path(override).expanduser()
        return path if path.exists() else None

    bundle = app_bundle_path(package_root())
    if sparkle_helper_path(bundle) is not None:
        return bundle

    app_path = Path("/Applications/Expando.app")
    if sparkle_helper_path(app_path) is not None:
        return app_path
    return None


def sparkle_framework_path(app_bundle: Path) -> Path | None:
    framework = app_bundle / "Contents" / "Frameworks" / "Sparkle.framework"
    return framework if framework.exists() else None


def sparkle_helper_path(app_bundle: Path) -> Path | None:
    helper = app_bundle / "Contents" / "MacOS" / SPARKLE_HELPER_NAME
    return helper if helper.is_file() and os.access(helper, os.X_OK) else None


def sparkle_available() -> bool:
    if platform.system() != "Darwin":
        return False
    bundle = resolve_distribution_app_bundle()
    return bundle is not None and sparkle_helper_path(bundle) is not None


def check_for_updates_via_sparkle(*, background: bool = True) -> bool:
    bundle = resolve_distribution_app_bundle()
    if bundle is None:
        return False
    helper = sparkle_helper_path(bundle)
    if helper is None:
        return False

    args = [str(helper), "background" if background else "interactive"]
    try:
        subprocess.run(args, check=False, timeout=120)
        return True
    except Exception:
        logger.exception("Sparkle helper failed")
        return False
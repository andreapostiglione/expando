from __future__ import annotations

import logging
import os
import platform
import subprocess
from dataclasses import dataclass
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


@dataclass
class SparkleSmokeReport:
    ok: bool
    app_bundle: str | None
    helper_path: str | None
    framework_present: bool
    errors: list[str]


def smoke_test_sparkle_embed(app_bundle: Path) -> SparkleSmokeReport:
    errors: list[str] = []
    helper = sparkle_helper_path(app_bundle)
    framework_present = sparkle_framework_path(app_bundle) is not None

    if helper is None:
        errors.append("expando-sparkle helper missing or not executable")
    else:
        try:
            result = subprocess.run(
                ["codesign", "--verify", "--verbose=2", str(helper)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except Exception as exc:
            errors.append(f"codesign verify failed: {exc}")
        else:
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "codesign verify failed").strip()
                errors.append(detail.splitlines()[-1] if detail else "codesign verify failed")

    if not framework_present:
        errors.append("Sparkle.framework missing")

    return SparkleSmokeReport(
        ok=not errors,
        app_bundle=str(app_bundle),
        helper_path=str(helper) if helper is not None else None,
        framework_present=framework_present,
        errors=errors,
    )


def format_sparkle_smoke_report(report: SparkleSmokeReport) -> str:
    from .i18n import t

    lines = [
        t("sparkle.smoke.title"),
        f"  {t('sparkle.smoke.bundle')}: {report.app_bundle or t('benchmark.sparkle.none')}",
        f"  {t('sparkle.smoke.helper')}: {report.helper_path or t('benchmark.sparkle.none')}",
        f"  {t('sparkle.smoke.framework')}: "
        f"{t('doctor.yes') if report.framework_present else t('doctor.no')}",
    ]
    if report.ok:
        lines.append(f"  {t('sparkle.smoke.ok')}")
    else:
        lines.append(f"  {t('sparkle.smoke.fail')}:")
        lines.extend(f"    - {item}" for item in report.errors)
    return "\n".join(lines)


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
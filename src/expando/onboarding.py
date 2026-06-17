from __future__ import annotations

import platform
from pathlib import Path

from .permissions import check_permissions, permissions_ready


def onboarding_flag(config_dir: Path) -> Path:
    return config_dir / ".onboarding_complete"


def is_onboarding_complete(config_dir: Path) -> bool:
    return onboarding_flag(config_dir).exists()


def mark_onboarding_complete(config_dir: Path) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    onboarding_flag(config_dir).write_text("1\n", encoding="utf-8")


def should_show_onboarding(config_dir: Path, *, force: bool = False) -> bool:
    if platform.system() != "Darwin":
        return False
    if force:
        return True
    if is_onboarding_complete(config_dir):
        return False
    status = check_permissions()
    return not permissions_ready(status)


def run_onboarding(config_dir: Path, *, force: bool = False) -> None:
    if not should_show_onboarding(config_dir, force=force):
        return
    if platform.system() != "Darwin":
        return
    try:
        from .onboarding_ui import run_permission_wizard
    except Exception:
        _run_cli_onboarding(config_dir)
        return
    completed = run_permission_wizard(config_dir)
    if completed:
        mark_onboarding_complete(config_dir)


def maybe_run_onboarding(config_dir: Path) -> None:
    run_onboarding(config_dir, force=False)


def _run_cli_onboarding(config_dir: Path) -> None:
    from .i18n import t
    from .permissions import open_accessibility_settings, open_input_monitoring_settings

    status = check_permissions()
    runtime = status.runtime
    label = runtime.grant_label if runtime else "Expando"
    print(t("wizard.title"))
    print(t("wizard.welcome"))
    print(f"{t('doctor.grant_target')}: {label}")
    open_accessibility_settings()
    input(f"{t('wizard.accessibility.title')} — premi Invio quando fatto...")
    open_input_monitoring_settings()
    input(f"{t('wizard.input.title')} — premi Invio quando fatto...")
    mark_onboarding_complete(config_dir)
    print(t("wizard.done"))
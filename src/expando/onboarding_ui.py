from __future__ import annotations

from pathlib import Path

from .i18n import t
from .permissions import (
    check_permissions,
    open_accessibility_settings,
    open_input_monitoring_settings,
    permissions_ready,
)


def run_permission_wizard(config_dir: Path) -> bool:
    from AppKit import (
        NSAlert,
        NSAlertFirstButtonReturn,
        NSAlertSecondButtonReturn,
        NSAlertThirdButtonReturn,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSMakeRect,
        NSTextField,
    )

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    app.activateIgnoringOtherApps_(True)

    step_index = 0
    steps = ["welcome", "accessibility", "input", "done"]

    while step_index < len(steps):
        step_id = steps[step_index]
        status = check_permissions()
        runtime = status.runtime

        if step_id == "welcome":
            title = t("wizard.title")
            body = t("wizard.welcome")
        elif step_id == "accessibility":
            title = t("wizard.accessibility.title")
            body = t("wizard.accessibility.body")
        elif step_id == "input":
            title = t("wizard.input.title")
            body = t("wizard.input.body")
        else:
            title = t("wizard.title")
            body = t("wizard.done")

        if runtime and step_id != "done":
            body = (
                f"{body}\n\n{t('doctor.grant_target')}: {runtime.grant_label}\n"
                f"{runtime.grant_hint}"
            )

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(body)

        if step_id == "accessibility":
            alert.addButtonWithTitle_(t("wizard.open_settings"))
            alert.addButtonWithTitle_(t("wizard.recheck"))
            alert.addButtonWithTitle_(t("wizard.skip"))
        elif step_id == "input":
            alert.addButtonWithTitle_(t("wizard.open_settings"))
            alert.addButtonWithTitle_(t("wizard.continue"))
            alert.addButtonWithTitle_(t("wizard.skip"))
        elif step_id == "done":
            alert.addButtonWithTitle_(t("wizard.finish"))
            if runtime and runtime.mode == "app":
                alert.addButtonWithTitle_(t("wizard.install_launch_agent"))
        else:
            alert.addButtonWithTitle_(t("wizard.continue"))
            alert.addButtonWithTitle_(t("wizard.skip"))

        if step_id == "accessibility":
            perm = t("doctor.perm.granted") if permissions_ready(status) else t("doctor.perm.missing")
            badge = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 360, 22))
            badge.setStringValue_(f"{t('doctor.accessibility')}: {perm}")
            badge.setEditable_(False)
            badge.setBezeled_(False)
            badge.setDrawsBackground_(False)
            alert.setAccessoryView_(badge)

        response = alert.runModal()

        if step_id == "welcome":
            if response == NSAlertSecondButtonReturn:
                return False
            step_index += 1
            continue

        if step_id == "accessibility":
            if response == NSAlertThirdButtonReturn:
                return False
            if response == NSAlertFirstButtonReturn:
                open_accessibility_settings()
                continue
            if permissions_ready(check_permissions()):
                step_index += 1
            continue

        if step_id == "input":
            if response == NSAlertThirdButtonReturn:
                return False
            if response == NSAlertFirstButtonReturn:
                open_input_monitoring_settings()
                continue
            step_index += 1
            continue

        if step_id == "done":
            if response == NSAlertSecondButtonReturn and runtime and runtime.mode == "app":
                _offer_launch_agent_install(config_dir)
            return True
        return True

    return True


def _offer_launch_agent_install(config_dir: Path) -> None:
    import subprocess

    from .paths import package_root

    script = package_root() / "scripts" / "install-launch-agent.sh"
    if not script.exists():
        return
    try:
        subprocess.run(["bash", str(script)], check=False, timeout=120)
    except Exception:
        return
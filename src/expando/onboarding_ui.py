from __future__ import annotations

from pathlib import Path

from .i18n import t
from .permissions import (
    PermissionStatus,
    check_permissions,
    open_accessibility_settings,
    open_input_monitoring_settings,
    permissions_ready,
)


def _permission_badge_text(status: PermissionStatus) -> str:
    accessibility = status.accessibility
    if accessibility is True:
        accessibility_label = t("doctor.perm.granted")
    elif accessibility is False:
        accessibility_label = t("doctor.perm.missing")
    else:
        accessibility_label = t("doctor.perm.unknown")

    input_monitoring = status.input_monitoring
    if input_monitoring is True:
        input_label = t("doctor.perm.granted")
    elif input_monitoring is False:
        input_label = t("doctor.perm.missing")
    else:
        input_label = t("doctor.perm.unknown")

    return (
        f"{t('doctor.accessibility')}: {accessibility_label}\n"
        f"{t('doctor.input_monitoring')}: {input_label}"
    )


def _make_badge(text: str):
    from AppKit import NSMakeRect, NSTextField

    badge = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 420, 44))
    badge.setStringValue_(text)
    badge.setEditable_(False)
    badge.setBezeled_(False)
    badge.setDrawsBackground_(False)
    return badge


def run_permission_wizard(config_dir: Path) -> bool:
    from AppKit import (
        NSAlert,
        NSAlertFirstButtonReturn,
        NSAlertSecondButtonReturn,
        NSAlertThirdButtonReturn,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
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
            body = f"{body}\n\n{t('doctor.grant_target')}: {runtime.grant_label}"
            if runtime.mode != "app":
                body = f"{body}\n{runtime.grant_hint}"
        if step_id in {"welcome", "done"}:
            body = f"{body}\n\n{_permission_badge_text(status)}"

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(body)

        if step_id == "accessibility":
            alert.addButtonWithTitle_(t("wizard.open_settings"))
            alert.addButtonWithTitle_(t("wizard.recheck"))
            alert.addButtonWithTitle_(t("wizard.skip"))
            alert.setAccessoryView_(_make_badge(_permission_badge_text(status)))
        elif step_id == "input":
            alert.addButtonWithTitle_(t("wizard.open_settings"))
            alert.addButtonWithTitle_(t("wizard.recheck"))
            alert.addButtonWithTitle_(t("wizard.continue"))
            alert.setAccessoryView_(_make_badge(_permission_badge_text(status)))
        elif step_id == "done":
            alert.addButtonWithTitle_(t("wizard.finish"))
            if runtime and runtime.mode == "app":
                alert.addButtonWithTitle_(t("wizard.install_launch_agent"))
            if not permissions_ready(status):
                alert.addButtonWithTitle_(t("wizard.open_permissions"))
        else:
            alert.addButtonWithTitle_(t("wizard.continue"))
            alert.addButtonWithTitle_(t("wizard.skip"))

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
            if check_permissions().accessibility is True:
                step_index += 1
            continue

        if step_id == "input":
            if response == NSAlertFirstButtonReturn:
                open_input_monitoring_settings()
                continue
            if response == NSAlertSecondButtonReturn:
                current_status = check_permissions()
                if current_status.input_monitoring is not False:
                    step_index += 1
                continue
            step_index += 1
            continue

        if step_id == "done":
            has_launch_agent = bool(runtime and runtime.mode == "app")
            has_open_permissions = not permissions_ready(status)
            if response == NSAlertFirstButtonReturn:
                return True
            if response == NSAlertSecondButtonReturn:
                if has_launch_agent:
                    _offer_launch_agent_install(config_dir)
                    return True
                if has_open_permissions:
                    open_accessibility_settings()
                    open_input_monitoring_settings()
                    continue
                return True
            if response == NSAlertThirdButtonReturn and has_launch_agent and has_open_permissions:
                open_accessibility_settings()
                open_input_monitoring_settings()
                continue
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

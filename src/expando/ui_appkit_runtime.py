from __future__ import annotations

from AppKit import NSApplication, NSApplicationActivationPolicyAccessory


def run_appkit_session(builder) -> object | None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = builder()
    window = controller.window
    app.activateIgnoringOtherApps_(True)
    window.makeKeyAndOrderFront_(None)

    if app.isRunning():
        app.runModalForWindow_(window)
    else:
        app.run()
    return controller.result


def close_appkit_session(controller) -> None:
    window = getattr(controller, "window", None)
    app = NSApplication.sharedApplication()
    if window is not None:
        window.orderOut_(None)
    if app.isRunning():
        app.stopModal()
    else:
        app.terminate_(None)
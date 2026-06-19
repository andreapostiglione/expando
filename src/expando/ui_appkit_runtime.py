from __future__ import annotations

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSRunContinuesResponse,
)
from Foundation import NSIndexSet


def select_first_table_row(table) -> None:
    if table.numberOfRows() > 0:
        table.selectRowIndexes_byExtendingSelection_(
            NSIndexSet.indexSetWithIndex_(0),
            False,
        )


def set_text_view_string(text_view, value: str) -> None:
    text_view.setEditable_(True)
    text_view.setString_(value)
    text_view.setEditable_(False)


def run_appkit_session(builder) -> object | None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = builder()
    window = controller.window
    app.activateIgnoringOtherApps_(True)
    window.makeKeyAndOrderFront_(None)

    if app.isRunning():
        session = app.beginModalSessionForWindow_(window)
        try:
            while app.runModalSession_(session) == NSRunContinuesResponse:
                pass
        finally:
            app.endModalSession_(session)
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
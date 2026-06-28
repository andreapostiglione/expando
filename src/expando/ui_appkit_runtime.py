from __future__ import annotations

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSColor,
    NSFont,
    NSRunContinuesResponse,
    NSTableColumn,
    NSTableViewLastColumnOnlyAutoresizingStyle,
)
from Foundation import NSIndexSet

_restore_pid: int | None = None


def configure_single_column_table(table) -> None:
    """NSTableView needs at least one column or rows render invisible."""
    column = NSTableColumn.alloc().initWithIdentifier_("label")
    column.setTitle_("")
    column.setMinWidth_(80.0)
    table.addTableColumn_(column)
    table.setHeaderView_(None)
    table.setColumnAutoresizingStyle_(NSTableViewLastColumnOnlyAutoresizingStyle)
    table.setRowHeight_(24.0)
    table.setUsesAlternatingRowBackgroundColors_(True)


def style_readonly_text_view(text_view) -> None:
    text_view.setEditable_(False)
    text_view.setDrawsBackground_(True)
    text_view.setBackgroundColor_(NSColor.textBackgroundColor())
    text_view.setTextColor_(NSColor.labelColor())
    text_view.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12.0, 0.0))


def select_first_table_row(table) -> None:
    if table.numberOfRows() > 0:
        table.selectRowIndexes_byExtendingSelection_(
            NSIndexSet.indexSetWithIndex_(0),
            False,
        )


def set_text_view_string(text_view, value: str) -> None:
    editable = bool(text_view.isEditable())
    text_view.setEditable_(True)
    text_view.setString_(value)
    text_view.setEditable_(editable)


def run_appkit_session(builder) -> object | None:
    global _restore_pid
    from .app_context import capture_frontmost_application_pid

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    captured = capture_frontmost_application_pid()
    if captured is not None:
        _restore_pid = captured
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
    global _restore_pid
    from .app_context import restore_frontmost_application
    from .ui_state import clear_ui_active

    window = getattr(controller, "window", None)
    app = NSApplication.sharedApplication()
    if window is not None:
        window.orderOut_(None)
    if app.isRunning():
        app.stopModal()
    else:
        app.terminate_(None)
    if _restore_pid is not None:
        restore_frontmost_application(_restore_pid)
        _restore_pid = None
    clear_ui_active()

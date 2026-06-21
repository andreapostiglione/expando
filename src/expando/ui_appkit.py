from __future__ import annotations

import objc
from Foundation import NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSButton,
    NSControlTextDidChangeNotification,
    NSMakeRect,
    NSScrollView,
    NSSearchField,
    NSTableView,
    NSTableViewSolidHorizontalGridLineMask,
    NSTextField,
    NSTextView,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)

from .i18n import t
from .ui_appkit_runtime import (
    close_appkit_session,
    configure_single_column_table,
    run_appkit_session,
    select_first_table_row,
    set_text_view_string,
    style_readonly_text_view,
)


class _SearchController(NSObject):
    def initWithItems_(self, items):
        self = objc.super(_SearchController, self).init()
        if self is None:
            return None
        self.items = items
        self.visible = list(items)
        self.result = None
        self.window = None
        self._focused_item = items[0] if items else None
        return self

    def numberOfRowsInTableView_(self, _table_view):
        return len(self.visible)

    def tableView_objectValueForTableColumn_row_(self, _table_view, _column, row):
        item = self.visible[row]
        return item.get("label", item.get("trigger", ""))

    def tableViewSelectionDidChange_(self, _notification):
        self._remember_selection()
        self._update_preview()

    def searchChanged_(self, notification):
        sender = notification.object()
        query = str(sender.stringValue()).strip()
        from .fuzzy import fuzzy_filter_search_items

        self.visible = fuzzy_filter_search_items(query, self.items)
        self.table_view.reloadData()
        select_first_table_row(self.table_view)
        self._remember_selection()
        self._update_preview()

    def _item_at_row(self, row: int):
        if row < 0 or row >= len(self.visible):
            return None
        return self.visible[row]

    def _remember_selection(self) -> None:
        item = self._item_at_row(self.table_view.selectedRow())
        if item is not None:
            self._focused_item = item

    def _selected_item(self):
        item = self._item_at_row(self.table_view.selectedRow())
        if item is not None:
            return item
        return self._focused_item

    def _update_preview(self):
        item = self._selected_item()
        preview = item.get("preview", "") if item else ""
        set_text_view_string(self.preview_view, preview)

    def accept_(self, _sender):
        item = self._selected_item()
        if item:
            self.result = {
                "id": item["id"],
                "trigger": item.get("trigger", ""),
            }
            if "package_id" in item:
                self.result["package_id"] = item["package_id"]
            if "archive_path" in item:
                self.result["archive_path"] = item["archive_path"]
            if "installed" in item:
                self.result["installed"] = item["installed"]
        close_appkit_session(self)

    def cancel_(self, _sender):
        self.result = None
        close_appkit_session(self)

    def windowShouldClose_(self, _sender):
        self.cancel_(None)
        return True


def _build_search_controller(items: list[dict[str, str]]) -> _SearchController:
    controller = _SearchController.alloc().initWithItems_(items)
    controller.visible = list(items)

    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, 720, 420),
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered,
        False,
    )
    window.setTitle_("Expando")
    window.setDelegate_(controller)
    controller.window = window

    content = window.contentView()
    search = NSSearchField.alloc().initWithFrame_(NSMakeRect(16, 372, 688, 28))
    search.setPlaceholderString_(t("menubar.search"))
    NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
        controller,
        "searchChanged:",
        NSControlTextDidChangeNotification,
        search,
    )
    controller.search_field = search
    content.addSubview_(search)

    table_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(16, 56, 300, 304))
    table_scroll.setBorderType_(NSBezelBorder)
    table_scroll.setHasVerticalScroller_(True)
    table = NSTableView.alloc().initWithFrame_(table_scroll.bounds())
    configure_single_column_table(table)
    table.setDelegate_(controller)
    table.setDataSource_(controller)
    table.setGridStyleMask_(NSTableViewSolidHorizontalGridLineMask)
    table.setDoubleAction_("accept:")
    table.setTarget_(controller)
    controller.table_view = table
    table_scroll.setDocumentView_(table)
    content.addSubview_(table_scroll)

    preview_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(332, 56, 372, 304))
    preview_scroll.setBorderType_(NSBezelBorder)
    preview_scroll.setHasVerticalScroller_(True)
    preview = NSTextView.alloc().initWithFrame_(preview_scroll.bounds())
    style_readonly_text_view(preview)
    controller.preview_view = preview
    preview_scroll.setDocumentView_(preview)
    content.addSubview_(preview_scroll)

    cancel_button = NSButton.alloc().initWithFrame_(NSMakeRect(548, 16, 80, 28))
    cancel_button.setTitle_(t("ui.cancel"))
    cancel_button.setTarget_(controller)
    cancel_button.setAction_("cancel:")
    content.addSubview_(cancel_button)

    insert_button = NSButton.alloc().initWithFrame_(NSMakeRect(636, 16, 68, 28))
    insert_button.setTitle_(t("ui.insert"))
    insert_button.setTarget_(controller)
    insert_button.setAction_("accept:")
    content.addSubview_(insert_button)

    table.reloadData()
    select_first_table_row(table)
    controller._remember_selection()
    controller._update_preview()
    return controller


def run_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    return run_appkit_session(lambda: _build_search_controller(items))


def run_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    alert = NSAlert.alloc().init()
    alert.setMessageText_(t("ui.form.title"))
    alert.addButtonWithTitle_(t("ui.ok"))
    alert.addButtonWithTitle_(t("ui.cancel"))

    stack = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 360, max(24 * len(fields), 24)))
    entries: dict[str, NSTextField] = {}
    y = max(24 * len(fields), 24) - 24
    for field in fields:
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y, 120, 22))
        label.setStringValue_(field.get("label") or field["name"])
        label.setEditable_(False)
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        stack.addSubview_(label)

        entry = NSTextField.alloc().initWithFrame_(NSMakeRect(128, y, 232, 22))
        default = field.get("default", "")
        if default:
            entry.setStringValue_(default)
        stack.addSubview_(entry)
        entries[field["name"]] = entry
        y -= 28

    alert.setAccessoryView_(stack)
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    app.activateIgnoringOtherApps_(True)
    response = alert.runModal()
    if response != NSAlertFirstButtonReturn:
        return None
    return {name: str(entry.stringValue()) for name, entry in entries.items()}
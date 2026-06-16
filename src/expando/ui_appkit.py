from __future__ import annotations

import objc
from Foundation import NSControlTextDidChangeNotification, NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSAlertSecondButtonReturn,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSButton,
    NSMakeRect,
    NSScrollView,
    NSSearchField,
    NSTableView,
    NSTableViewSolidHorizontalGridLineMask,
    NSTextField,
    NSTextView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)


def _run_appkit_app(builder) -> dict[str, str] | None:
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = builder()
    app.activateIgnoringOtherApps_(True)
    app.run()
    return controller.result


class _SearchController(NSObject):
    def initWithItems_(self, items):
        self = objc.super(_SearchController, self).init()
        if self is None:
            return None
        self.items = items
        self.visible = list(items)
        self.result = None
        return self

    def numberOfRowsInTableView_(self, _table_view):
        return len(self.visible)

    def tableView_objectValueForTableColumn_row_(self, _table_view, _column, row):
        item = self.visible[row]
        return item.get("label", item.get("trigger", ""))

    def searchChanged_(self, notification):
        sender = notification.object()
        query = str(sender.stringValue()).strip()
        from .fuzzy import fuzzy_filter_search_items

        self.visible = fuzzy_filter_search_items(query, self.items)
        self.table_view.reloadData()
        if self.visible:
            self.table_view.selectRowIndexes_byExtendingSelection_(0, False)
        self._update_preview()

    def tableSelectionChanged_(self, _notification):
        self._update_preview()

    def _selected_item(self):
        row = self.table_view.selectedRow()
        if row < 0 or row >= len(self.visible):
            return None
        return self.visible[row]

    def _update_preview(self):
        item = self._selected_item()
        preview = item.get("preview", "") if item else ""
        self.preview_view.setString_(preview)

    def accept_(self, _sender):
        item = self._selected_item()
        if item:
            self.result = {
                "id": item["id"],
                "trigger": item.get("trigger", ""),
            }
            if "package_id" in item:
                self.result["package_id"] = item["package_id"]
            if "installed" in item:
                self.result["installed"] = item["installed"]
        NSApplication.sharedApplication().terminate_(None)

    def cancel_(self, _sender):
        self.result = None
        NSApplication.sharedApplication().terminate_(None)

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

    content = window.contentView()
    search = NSSearchField.alloc().initWithFrame_(NSMakeRect(16, 372, 688, 28))
    search.setPlaceholderString_("Search snippets")
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
    preview.setEditable_(False)
    preview.setDrawsBackground_(True)
    controller.preview_view = preview
    preview_scroll.setDocumentView_(preview)
    content.addSubview_(preview_scroll)

    cancel_button = NSButton.alloc().initWithFrame_(NSMakeRect(548, 16, 80, 28))
    cancel_button.setTitle_("Cancel")
    cancel_button.setTarget_(controller)
    cancel_button.setAction_("cancel:")
    content.addSubview_(cancel_button)

    insert_button = NSButton.alloc().initWithFrame_(NSMakeRect(636, 16, 68, 28))
    insert_button.setTitle_("Insert")
    insert_button.setTarget_(controller)
    insert_button.setAction_("accept:")
    content.addSubview_(insert_button)

    window.center()
    window.makeKeyAndOrderFront_(None)
    if controller.visible:
        table.selectRowIndexes_byExtendingSelection_(0, False)
    controller._update_preview()
    return controller


def run_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    return _run_appkit_app(lambda: _build_search_controller(items))


def run_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    alert = NSAlert.alloc().init()
    alert.setMessageText_("Fill in the snippet fields")
    alert.addButtonWithTitle_("OK")
    alert.addButtonWithTitle_("Cancel")

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
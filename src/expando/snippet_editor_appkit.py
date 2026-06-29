from __future__ import annotations

import objc
from Foundation import NSIndexSet, NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSButton,
    NSControlTextDidChangeNotification,
    NSMakeRect,
    NSSearchField,
    NSScrollView,
    NSTableView,
    NSTextField,
    NSTextView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)
from pathlib import Path
from typing import Callable

from .i18n import t
from .ui_appkit_runtime import (
    close_appkit_session,
    configure_single_column_table,
    install_liquid_glass_background,
    run_appkit_session,
    select_first_table_row,
    set_text_view_string,
    style_readonly_text_view,
)
from .ui_file_picker import pick_list_item


def _set_field(field: NSTextField, value: str) -> None:
    field.setStringValue_(value)


def _set_view(view: NSTextView, value: str) -> None:
    set_text_view_string(view, value)


class _SnippetEditorController(NSObject):
    def initWithHandlers_items_reload_(
        self,
        handlers: dict,
        items: list[dict[str, str]],
        reload_items: Callable[[], list[dict[str, str]]],
    ):
        self = objc.super(_SnippetEditorController, self).init()
        if self is None:
            return None
        self.handlers = handlers
        self.items = list(items)
        self.reload_items = reload_items
        self.visible = list(items)
        self.result = None
        self.current_id = None
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
            select_first_table_row(self.table_view)
            self._load_selection()

    def tableViewSelectionDidChange_(self, _notification):
        self._load_selection()

    def tableSelectionChanged_(self, _notification):
        self._load_selection()

    def _selected_item(self):
        row = self.table_view.selectedRow()
        if row < 0 or row >= len(self.visible):
            return None
        return self.visible[row]

    def _load_selection(self) -> None:
        item = self._selected_item()
        if not item:
            self.current_id = None
            _set_field(self.trigger_field, "")
            _set_field(self.if_app_field, "")
            if hasattr(self, "unless_app_field"):
                _set_field(self.unless_app_field, "")
                _set_field(self.if_bundle_field, "")
                _set_field(self.unless_bundle_field, "")
                _set_field(self.if_title_field, "")
                _set_field(self.unless_title_field, "")
                _set_field(self.regex_field, "")
                _set_view(self.when_view, "")
                _set_field(self.image_field, "")
                _set_field(self.priority_field, "")
                _set_field(self.force_clipboard_field, "")
                _set_field(self.target_file_field, "")
            _set_view(self.form_view, "")
            _set_view(self.vars_view, "")
            _set_view(self.replace_view, "")
            self.replace_view.setEditable_(True)
            self.form_view.setEditable_(True)
            self.vars_view.setEditable_(True)
            if hasattr(self, "when_view"):
                self.when_view.setEditable_(True)
            self._update_preview()
            return
        self.current_id = item.get("id")
        _set_field(self.trigger_field, item.get("trigger", ""))
        _set_field(self.if_app_field, item.get("if_app", ""))
        if hasattr(self, "unless_app_field"):
            _set_field(self.unless_app_field, item.get("unless_app", ""))
            _set_field(self.if_bundle_field, item.get("if_bundle", ""))
            _set_field(self.unless_bundle_field, item.get("unless_bundle", ""))
            _set_field(self.if_title_field, item.get("if_title", ""))
            _set_field(self.unless_title_field, item.get("unless_title", ""))
            _set_field(self.regex_field, item.get("regex", ""))
            _set_view(self.when_view, item.get("when", ""))
            _set_field(self.image_field, item.get("image", ""))
            _set_field(self.priority_field, item.get("priority", ""))
            _set_field(self.force_clipboard_field, item.get("force_clipboard", ""))
            _set_field(
                self.target_file_field,
                item.get("target_file", item.get("source_file", "dev.yml")),
            )
        _set_view(self.form_view, item.get("form", ""))
        _set_view(self.vars_view, item.get("vars", ""))
        _set_view(self.replace_view, item.get("replace", ""))
        editable = item.get("editable", "1") == "1"
        self.replace_view.setEditable_(editable)
        self.form_view.setEditable_(editable)
        self.vars_view.setEditable_(editable)
        if hasattr(self, "when_view"):
            self.when_view.setEditable_(editable)
        self._update_preview()

    def replaceChanged_(self, _notification):
        self._update_preview()

    def _update_preview(self) -> None:
        replace_text = str(self.replace_view.string())
        config_dir = getattr(self, "config_dir", None)
        if config_dir is not None:
            from .config import Match
            from .snippet_editor_data import preview_snippet_text

            match = Match(triggers=[":preview"], replace=replace_text)
            preview = preview_snippet_text(match, config_dir, replace_text=replace_text)
            _set_view(self.preview_view, preview)
            return
        _set_view(self.preview_view, replace_text)

    def new_(self, _sender):
        self.current_id = None
        _set_field(self.trigger_field, ":nuovo")
        _set_field(self.if_app_field, "")
        if hasattr(self, "unless_app_field"):
            _set_field(self.unless_app_field, "")
            _set_field(self.if_bundle_field, "")
            _set_field(self.unless_bundle_field, "")
            _set_field(self.if_title_field, "")
            _set_field(self.unless_title_field, "")
            _set_field(self.regex_field, "")
            _set_view(self.when_view, "")
            _set_field(self.image_field, "")
            _set_field(self.priority_field, "")
            _set_field(self.force_clipboard_field, "")
            target = (getattr(self, "match_files", None) or ["dev.yml"])[0]
            _set_field(self.target_file_field, target)
            self.when_view.setEditable_(True)
        self.form_view.setEditable_(True)
        self.vars_view.setEditable_(True)
        _set_view(self.form_view, "")
        _set_view(self.vars_view, "")
        self.replace_view.setEditable_(True)
        _set_view(self.replace_view, "")
        self._update_preview()

    def save_(self, _sender):
        payload = self._payload()
        if not payload["trigger"]:
            self.showAlertMessage_("Il trigger non può essere vuoto.")
            return
        item = self._selected_item()
        if self.current_id and item and item.get("editable", "1") != "1":
            self.showAlertMessage_("Questo snippet non è modificabile dall'editor.")
            return
        handler = self.handlers["save"] if self.current_id else self.handlers["create"]
        error = handler(payload)
        if error:
            self.showAlertMessage_(error)
            return
        self.result = {"saved": "1"}
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()

    def delete_(self, _sender):
        if not self.current_id:
            self.showAlertMessage_("Seleziona uno snippet da eliminare.")
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self.showAlertMessage_("I package hub non possono essere eliminati da qui.")
            return
        error = self.handlers["delete"](self.current_id)
        if error:
            self.showAlertMessage_(error)
            return
        self.result = {"deleted": "1"}
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()

    def duplicate_(self, _sender):
        if not self.current_id:
            self.showAlertMessage_(t("editor.duplicate.select"))
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self.showAlertMessage_(t("editor.duplicate.readonly"))
            return
        target = item.get("source_file") or item.get("target_file") or "dev.yml"
        if not target:
            return
        handler = self.handlers.get("duplicate")
        if handler is None:
            return
        error = handler(self.current_id, target)
        if error:
            self.showAlertMessage_(error)
            return
        self.result = {"duplicated": "1"}
        self._refresh_list(select_trigger=f"{item.get('trigger', '')}-copy" if item else "")

    def move_(self, _sender):
        if not self.current_id:
            self.showAlertMessage_(t("editor.move.select"))
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self.showAlertMessage_(t("editor.move.readonly"))
            return
        source_file = item.get("source_file", "") if item else ""
        candidates = [
            name for name in getattr(self, "match_files", []) if name and name != source_file
        ]
        if not candidates:
            self.showAlertMessage_(t("editor.move.no_targets"))
            return
        target = pick_list_item(
            candidates,
            title=t("editor.move.title"),
            message=t("editor.move.body"),
            confirm_label=t("ui.confirm"),
            cancel_label=t("ui.cancel"),
        )
        if not target:
            return
        handler = self.handlers.get("move")
        if handler is None:
            return
        error = handler(self.current_id, target)
        if error:
            self.showAlertMessage_(error)
            return
        self.result = {"moved": "1"}
        self._refresh_list()

    def _pick_target_file(self, title: str, message: str) -> str | None:
        files = list(getattr(self, "match_files", []) or ["dev.yml"])
        return pick_list_item(
            files,
            title=title,
            message=message,
            confirm_label=t("ui.confirm"),
            cancel_label=t("ui.cancel"),
        )

    def _refresh_list(self, *, select_trigger: str = "") -> None:
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()
        if select_trigger:
            for row, item in enumerate(self.visible):
                if item.get("trigger") == select_trigger:
                    self.table_view.selectRowIndexes_byExtendingSelection_(
                        NSIndexSet.indexSetWithIndex_(row),
                        False,
                    )
                    self._load_selection()
                    return
        if self.visible:
            select_first_table_row(self.table_view)
            self._load_selection()

    def close_(self, _sender):
        close_appkit_session(self)

    def windowShouldClose_(self, _sender):
        self.close_(None)
        return True

    def _payload(self) -> dict[str, str]:
        return {
            "id": self.current_id or "",
            "trigger": str(self.trigger_field.stringValue()).strip(),
            "replace": str(self.replace_view.string()).strip(),
            "if_app": str(self.if_app_field.stringValue()).strip(),
            "unless_app": str(getattr(self, "unless_app_field", self.if_app_field).stringValue()).strip(),
            "if_bundle": str(getattr(self, "if_bundle_field", self.if_app_field).stringValue()).strip(),
            "unless_bundle": str(getattr(self, "unless_bundle_field", self.if_app_field).stringValue()).strip(),
            "if_title": str(getattr(self, "if_title_field", self.if_app_field).stringValue()).strip(),
            "unless_title": str(getattr(self, "unless_title_field", self.if_app_field).stringValue()).strip(),
            "regex": str(getattr(self, "regex_field", self.if_app_field).stringValue()).strip(),
            "when": str(getattr(self, "when_view", self.form_view).string()).strip(),
            "image": str(getattr(self, "image_field", self.if_app_field).stringValue()).strip(),
            "priority": str(getattr(self, "priority_field", self.if_app_field).stringValue()).strip(),
            "force_clipboard": str(getattr(self, "force_clipboard_field", self.if_app_field).stringValue()).strip(),
            "target_file": str(getattr(self, "target_file_field", self.if_app_field).stringValue()).strip(),
            "form": str(self.form_view.string()).strip(),
            "vars": str(self.vars_view.string()).strip(),
        }

    def showAlertMessage_(self, message) -> None:
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Expando")
        alert.setInformativeText_(str(message))
        alert.addButtonWithTitle_("OK")
        alert.runModal()


def run_snippet_editor(
    items: list[dict[str, str]],
    *,
    on_save: Callable[[dict[str, str]], str | None],
    on_create: Callable[[dict[str, str]], str | None],
    on_delete: Callable[[str], str | None],
    on_duplicate: Callable[[str, str], str | None] | None = None,
    on_move: Callable[[str, str], str | None] | None = None,
    reload_items: Callable[[], list[dict[str, str]]],
    match_files: list[str] | None = None,
    config_dir: Path | None = None,
    initial_new: bool = False,
) -> dict[str, str] | None:
    handlers = {
        "save": on_save,
        "create": on_create,
        "delete": on_delete,
        "duplicate": on_duplicate,
        "move": on_move,
    }

    def builder():
        controller = _SnippetEditorController.alloc().initWithHandlers_items_reload_(
            handlers,
            items,
            reload_items,
        )
        controller.config_dir = config_dir
        controller.match_files = list(match_files or ["dev.yml"])
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 960, 660),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_(t("editor.window_title"))
        window.setDelegate_(controller)
        controller.window = window

        content = install_liquid_glass_background(window)
        controller.editor_content_view = content
        left_x = 24
        left_w = 292
        right_x = 340
        right_edge = 936
        label_w = 110
        field_x = right_x + label_w + 10
        field_w = right_edge - field_x

        def _label(text: str, x: int, y: int, width: int = label_w) -> NSTextField:
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, 22))
            label.setStringValue_(text)
            label.setEditable_(False)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            content.addSubview_(label)
            return label

        def _field(x: int, y: int, width: int) -> NSTextField:
            field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y - 2, width, 24))
            content.addSubview_(field)
            return field

        def _hidden_field(value: str = "") -> NSTextField:
            field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))
            if value:
                field.setStringValue_(value)
            return field

        def _text_area(x: int, y: int, width: int, height: int, *, editable: bool) -> NSTextView:
            scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
            scroll.setBorderType_(NSBezelBorder)
            scroll.setHasVerticalScroller_(True)
            view = NSTextView.alloc().initWithFrame_(scroll.bounds())
            view.setEditable_(editable)
            if not editable:
                style_readonly_text_view(view)
            scroll.setDocumentView_(view)
            content.addSubview_(scroll)
            return view

        def _hidden_text_view() -> NSTextView:
            view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))
            view.setEditable_(True)
            return view

        search = NSSearchField.alloc().initWithFrame_(NSMakeRect(left_x, 604, left_w, 28))
        search.setPlaceholderString_(t("editor.search_placeholder"))
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "searchChanged:",
            NSControlTextDidChangeNotification,
            search,
        )
        controller.search_field = search
        content.addSubview_(search)

        table_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(left_x, 76, left_w, 510))
        table_scroll.setBorderType_(NSBezelBorder)
        table_scroll.setHasVerticalScroller_(True)
        table = NSTableView.alloc().initWithFrame_(table_scroll.bounds())
        configure_single_column_table(table)
        table.setDelegate_(controller)
        table.setDataSource_(controller)
        controller.table_view = table
        table_scroll.setDocumentView_(table)
        content.addSubview_(table_scroll)

        _label(t("editor.trigger_label"), right_x, 606)
        controller.trigger_field = _field(field_x, 606, field_w)

        _label(t("editor.app_label"), right_x, 566)
        controller.if_app_field = _field(field_x, 566, field_w)

        controller.target_file_field = _hidden_field()
        controller.target_file_field.setStringValue_((match_files or ["dev.yml"])[0])

        controller.unless_app_field = _hidden_field()
        controller.if_bundle_field = _hidden_field()
        controller.unless_bundle_field = _hidden_field()
        controller.if_title_field = _hidden_field()
        controller.unless_title_field = _hidden_field()
        controller.image_field = _hidden_field()
        controller.regex_field = _hidden_field()
        controller.priority_field = _hidden_field()
        controller.force_clipboard_field = _hidden_field()
        controller.when_view = _hidden_text_view()
        controller.form_view = _hidden_text_view()
        controller.vars_view = _hidden_text_view()

        _label(t("editor.text_label"), right_x, 518)
        replace_view = _text_area(right_x, 182, right_edge - right_x, 324, editable=True)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "replaceChanged:",
            NSControlTextDidChangeNotification,
            replace_view,
        )
        controller.replace_view = replace_view

        _label(t("editor.preview_label"), right_x, 144)
        controller.preview_view = _text_area(right_x, 76, right_edge - right_x, 62, editable=False)

        new_button = NSButton.alloc().initWithFrame_(NSMakeRect(left_x, 20, 84, 28))
        new_button.setTitle_(t("editor.new_button"))
        new_button.setTarget_(controller)
        new_button.setAction_("new:")
        content.addSubview_(new_button)

        save_button = NSButton.alloc().initWithFrame_(NSMakeRect(116, 20, 84, 28))
        save_button.setTitle_(t("editor.save_button"))
        save_button.setTarget_(controller)
        save_button.setAction_("save:")
        content.addSubview_(save_button)

        delete_button = NSButton.alloc().initWithFrame_(NSMakeRect(208, 20, 84, 28))
        delete_button.setTitle_(t("editor.delete_button"))
        delete_button.setTarget_(controller)
        delete_button.setAction_("delete:")
        content.addSubview_(delete_button)

        duplicate_button = NSButton.alloc().initWithFrame_(NSMakeRect(300, 20, 96, 28))
        duplicate_button.setTitle_(t("editor.duplicate.button"))
        duplicate_button.setTarget_(controller)
        duplicate_button.setAction_("duplicate:")
        content.addSubview_(duplicate_button)

        close_button = NSButton.alloc().initWithFrame_(NSMakeRect(852, 20, 84, 28))
        close_button.setTitle_(t("editor.close_button"))
        close_button.setTarget_(controller)
        close_button.setAction_("close:")
        content.addSubview_(close_button)

        window.center()
        window.makeKeyAndOrderFront_(None)
        if initial_new:
            controller.new_(None)
        elif controller.visible:
            select_first_table_row(table)
            controller._load_selection()
        return controller

    return run_appkit_session(builder)

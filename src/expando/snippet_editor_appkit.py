from __future__ import annotations

import objc
from Foundation import NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSButton,
    NSControlTextDidChangeNotification,
    NSMakeRect,
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

from .ui_appkit_runtime import close_appkit_session, run_appkit_session


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
            self.table_view.selectRowIndexes_byExtendingSelection_(0, False)
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
            self.trigger_field.setString_("")
            self.if_app_field.setString_("")
            self.form_view.setString_("")
            self.vars_view.setString_("")
            self.replace_view.setString_("")
            self._update_preview()
            return
        self.current_id = item.get("id")
        self.trigger_field.setString_(item.get("trigger", ""))
        self.if_app_field.setString_(item.get("if_app", ""))
        if hasattr(self, "unless_app_field"):
            self.unless_app_field.setString_(item.get("unless_app", ""))
            self.if_bundle_field.setString_(item.get("if_bundle", ""))
            self.unless_bundle_field.setString_(item.get("unless_bundle", ""))
            self.if_title_field.setString_(item.get("if_title", ""))
            self.unless_title_field.setString_(item.get("unless_title", ""))
            self.regex_field.setString_(item.get("regex", ""))
            self.when_view.setString_(item.get("when", ""))
            self.image_field.setString_(item.get("image", ""))
            self.priority_field.setString_(item.get("priority", ""))
            self.force_clipboard_field.setString_(item.get("force_clipboard", ""))
            self.target_file_field.setString_(item.get("target_file", item.get("source_file", "dev.yml")))
        self.form_view.setString_(item.get("form", ""))
        self.vars_view.setString_(item.get("vars", ""))
        self.replace_view.setString_(item.get("replace", ""))
        editable = item.get("editable", "1") == "1"
        self.replace_view.setEditable_(editable)
        self.form_view.setEditable_(editable)
        self.vars_view.setEditable_(editable)
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
            self.preview_view.setString_(preview)
            return
        self.preview_view.setString_(replace_text)

    def new_(self, _sender):
        self.current_id = None
        self.trigger_field.setString_(":nuovo")
        self.if_app_field.setString_("")
        self.form_view.setEditable_(True)
        self.vars_view.setEditable_(True)
        self.form_view.setString_("")
        self.vars_view.setString_("")
        self.replace_view.setEditable_(True)
        self.replace_view.setString_("")
        self._update_preview()

    def save_(self, _sender):
        payload = self._payload()
        if not payload["trigger"]:
            self._alert("Il trigger non può essere vuoto.")
            return
        item = self._selected_item()
        if self.current_id and item and item.get("editable", "1") != "1":
            self._alert("Questo snippet non è modificabile dall'editor.")
            return
        handler = self.handlers["save"] if self.current_id else self.handlers["create"]
        error = handler(payload)
        if error:
            self._alert(error)
            return
        self.result = {"saved": "1"}
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()

    def delete_(self, _sender):
        if not self.current_id:
            self._alert("Seleziona uno snippet da eliminare.")
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self._alert("I package hub non possono essere eliminati da qui.")
            return
        error = self.handlers["delete"](self.current_id)
        if error:
            self._alert(error)
            return
        self.result = {"deleted": "1"}
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()

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

    def _alert(self, message: str) -> None:
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Expando")
        alert.setInformativeText_(message)
        alert.addButtonWithTitle_("OK")
        alert.runModal()


def run_snippet_editor(
    items: list[dict[str, str]],
    *,
    on_save: Callable[[dict[str, str]], str | None],
    on_create: Callable[[dict[str, str]], str | None],
    on_delete: Callable[[str], str | None],
    reload_items: Callable[[], list[dict[str, str]]],
    match_files: list[str] | None = None,
    config_dir: Path | None = None,
) -> dict[str, str] | None:
    handlers = {"save": on_save, "create": on_create, "delete": on_delete}

    def builder():
        controller = _SnippetEditorController.alloc().initWithHandlers_items_reload_(
            handlers,
            items,
            reload_items,
        )
        controller.config_dir = config_dir
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 920, 820),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_("Expando — Snippet editor")
        window.setDelegate_(controller)
        controller.window = window

        content = window.contentView()
        search = NSTextField.alloc().initWithFrame_(NSMakeRect(16, 672, 888, 28))
        search.setPlaceholderString_("Cerca snippet")
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "searchChanged:",
            NSControlTextDidChangeNotification,
            search,
        )
        controller.search_field = search
        content.addSubview_(search)

        table_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(16, 180, 280, 480))
        table_scroll.setBorderType_(NSBezelBorder)
        table_scroll.setHasVerticalScroller_(True)
        table = NSTableView.alloc().initWithFrame_(table_scroll.bounds())
        table.setDelegate_(controller)
        table.setDataSource_(controller)
        controller.table_view = table
        table_scroll.setDocumentView_(table)
        content.addSubview_(table_scroll)

        trigger_label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, 672, 80, 22))
        trigger_label.setStringValue_("Trigger")
        trigger_label.setEditable_(False)
        trigger_label.setBezeled_(False)
        trigger_label.setDrawsBackground_(False)
        content.addSubview_(trigger_label)

        trigger_field = NSTextField.alloc().initWithFrame_(NSMakeRect(392, 670, 512, 24))
        controller.trigger_field = trigger_field
        content.addSubview_(trigger_field)

        if_app_label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, 638, 80, 22))
        if_app_label.setStringValue_("Solo in app")
        if_app_label.setEditable_(False)
        if_app_label.setBezeled_(False)
        if_app_label.setDrawsBackground_(False)
        content.addSubview_(if_app_label)

        if_app_field = NSTextField.alloc().initWithFrame_(NSMakeRect(392, 636, 512, 24))
        controller.if_app_field = if_app_field
        content.addSubview_(if_app_field)

        def _adv_label(text: str, y: int) -> None:
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, y, 120, 22))
            label.setStringValue_(text)
            label.setEditable_(False)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            content.addSubview_(label)

        def _adv_field(y: int) -> NSTextField:
            field = NSTextField.alloc().initWithFrame_(NSMakeRect(440, y - 2, 464, 24))
            content.addSubview_(field)
            return field

        _adv_label("unless_app", 606)
        controller.unless_app_field = _adv_field(606)
        _adv_label("if_bundle", 574)
        controller.if_bundle_field = _adv_field(574)
        _adv_label("unless_bundle", 542)
        controller.unless_bundle_field = _adv_field(542)
        _adv_label("if_title", 510)
        controller.if_title_field = _adv_field(510)
        _adv_label("unless_title", 478)
        controller.unless_title_field = _adv_field(478)
        _adv_label("regex (1/0)", 446)
        controller.regex_field = _adv_field(446)
        _adv_label("image", 414)
        controller.image_field = _adv_field(414)
        _adv_label("priority", 382)
        controller.priority_field = _adv_field(382)
        _adv_label("force_clipboard", 350)
        controller.force_clipboard_field = _adv_field(350)
        _adv_label("target_file", 318)
        controller.target_file_field = _adv_field(318)
        controller.target_file_field.setStringValue_((match_files or ["dev.yml"])[0])

        when_label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, 286, 80, 22))
        when_label.setStringValue_("when")
        when_label.setEditable_(False)
        when_label.setBezeled_(False)
        when_label.setDrawsBackground_(False)
        content.addSubview_(when_label)
        when_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(392, 254, 512, 56))
        when_scroll.setBorderType_(NSBezelBorder)
        when_scroll.setHasVerticalScroller_(True)
        when_view = NSTextView.alloc().initWithFrame_(when_scroll.bounds())
        controller.when_view = when_view
        when_scroll.setDocumentView_(when_view)
        content.addSubview_(when_scroll)

        form_label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, 224, 80, 22))
        form_label.setStringValue_("Form")
        form_label.setEditable_(False)
        form_label.setBezeled_(False)
        form_label.setDrawsBackground_(False)
        content.addSubview_(form_label)

        form_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(392, 574, 512, 56))
        form_scroll.setBorderType_(NSBezelBorder)
        form_scroll.setHasVerticalScroller_(True)
        form_view = NSTextView.alloc().initWithFrame_(form_scroll.bounds())
        form_view.setEditable_(True)
        controller.form_view = form_view
        form_scroll.setDocumentView_(form_view)
        content.addSubview_(form_scroll)

        vars_label = NSTextField.alloc().initWithFrame_(NSMakeRect(312, 544, 80, 22))
        vars_label.setStringValue_("Variabili")
        vars_label.setEditable_(False)
        vars_label.setBezeled_(False)
        vars_label.setDrawsBackground_(False)
        content.addSubview_(vars_label)

        vars_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(392, 468, 512, 72))
        vars_scroll.setBorderType_(NSBezelBorder)
        vars_scroll.setHasVerticalScroller_(True)
        vars_view = NSTextView.alloc().initWithFrame_(vars_scroll.bounds())
        vars_view.setEditable_(True)
        controller.vars_view = vars_view
        vars_scroll.setDocumentView_(vars_view)
        content.addSubview_(vars_scroll)

        replace_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(312, 300, 592, 160))
        replace_scroll.setBorderType_(NSBezelBorder)
        replace_scroll.setHasVerticalScroller_(True)
        replace_view = NSTextView.alloc().initWithFrame_(replace_scroll.bounds())
        replace_view.setEditable_(True)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "replaceChanged:",
            NSControlTextDidChangeNotification,
            replace_view,
        )
        controller.replace_view = replace_view
        replace_scroll.setDocumentView_(replace_view)
        content.addSubview_(replace_scroll)

        preview_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(312, 180, 592, 108))
        preview_scroll.setBorderType_(NSBezelBorder)
        preview_scroll.setHasVerticalScroller_(True)
        preview = NSTextView.alloc().initWithFrame_(preview_scroll.bounds())
        preview.setEditable_(False)
        controller.preview_view = preview
        preview_scroll.setDocumentView_(preview)
        content.addSubview_(preview_scroll)

        new_button = NSButton.alloc().initWithFrame_(NSMakeRect(16, 16, 80, 28))
        new_button.setTitle_("Nuovo")
        new_button.setTarget_(controller)
        new_button.setAction_("new:")
        content.addSubview_(new_button)

        save_button = NSButton.alloc().initWithFrame_(NSMakeRect(104, 16, 80, 28))
        save_button.setTitle_("Salva")
        save_button.setTarget_(controller)
        save_button.setAction_("save:")
        content.addSubview_(save_button)

        delete_button = NSButton.alloc().initWithFrame_(NSMakeRect(192, 16, 80, 28))
        delete_button.setTitle_("Elimina")
        delete_button.setTarget_(controller)
        delete_button.setAction_("delete:")
        content.addSubview_(delete_button)

        close_button = NSButton.alloc().initWithFrame_(NSMakeRect(804, 16, 80, 28))
        close_button.setTitle_("Chiudi")
        close_button.setTarget_(controller)
        close_button.setAction_("close:")
        content.addSubview_(close_button)

        window.center()
        window.makeKeyAndOrderFront_(None)
        if controller.visible:
            table.selectRowIndexes_byExtendingSelection_(0, False)
            controller._load_selection()
        return controller

    return run_appkit_session(builder)
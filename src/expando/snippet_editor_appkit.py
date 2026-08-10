from __future__ import annotations

import objc
from Foundation import NSIndexSet, NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSBackingStoreBuffered,
    NSBezelBorder,
    NSControlTextDidChangeNotification,
    NSMakeRect,
    NSScrollView,
    NSSearchField,
    NSTableView,
    NSTextField,
    NSTextView,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskFullSizeContentView,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
    NSColor,
)
from pathlib import Path
from typing import Callable

from .i18n import t
from .snippet_editor_data import DEFAULT_SNIPPET_FILE
from .ui_appkit_runtime import (
    close_appkit_session,
    configure_single_column_table,
    run_appkit_session,
    select_first_table_row,
    set_text_view_string,
)
from .ui_file_picker import pick_list_item
from .ui_theme import (
    SIDEBAR_WIDTH,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    TOOLBAR_HEIGHT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    color_control_bg,
    color_field_bg,
    color_label,
    color_secondary,
    color_separator,
    font_body,
    font_caption,
    font_mono,
    font_section,
    font_title,
    make_button,
    make_content_effect,
    make_label,
    make_panel_view,
    make_sidebar_effect,
    make_text_field,
    style_editor_text_view,
    style_sidebar_table,
)


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
        trigger = item.get("trigger", "")
        source = item.get("label", trigger)
        # Compact list: trigger primary; collection hint already in label from data layer.
        return source

    def searchChanged_(self, notification):
        sender = notification.object()
        query = str(sender.stringValue()).strip()
        from .fuzzy import fuzzy_filter_search_items

        self.visible = fuzzy_filter_search_items(query, self.items)
        self.table_view.reloadData()
        self._update_count_label()
        if self.visible:
            select_first_table_row(self.table_view)
            self._load_selection()
        else:
            self._show_empty_state()

    def tableViewSelectionDidChange_(self, _notification):
        self._load_selection()

    def tableSelectionChanged_(self, _notification):
        self._load_selection()

    def _selected_item(self):
        row = self.table_view.selectedRow()
        if row < 0 or row >= len(self.visible):
            return None
        return self.visible[row]

    def _show_empty_state(self) -> None:
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
        if hasattr(self, "empty_hint"):
            self.empty_hint.setHidden_(False)
        self._update_preview()

    def _load_selection(self) -> None:
        item = self._selected_item()
        if not item:
            self._show_empty_state()
            return
        if hasattr(self, "empty_hint"):
            self.empty_hint.setHidden_(True)
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
                item.get("target_file", item.get("source_file", DEFAULT_SNIPPET_FILE)),
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

    def _update_count_label(self) -> None:
        if not hasattr(self, "count_label"):
            return
        total = len(self.items)
        shown = len(self.visible)
        if shown == total:
            self.count_label.setStringValue_(f"{total} snippet")
        else:
            self.count_label.setStringValue_(f"{shown} / {total}")

    def new_(self, _sender):
        self.current_id = None
        if hasattr(self, "empty_hint"):
            self.empty_hint.setHidden_(True)
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
            target = (getattr(self, "match_files", None) or [DEFAULT_SNIPPET_FILE])[0]
            _set_field(self.target_file_field, target)
            self.when_view.setEditable_(True)
        self.form_view.setEditable_(True)
        self.vars_view.setEditable_(True)
        _set_view(self.form_view, "")
        _set_view(self.vars_view, "")
        self.replace_view.setEditable_(True)
        _set_view(self.replace_view, "")
        self._update_preview()
        try:
            self.window.makeFirstResponder_(self.trigger_field)
        except Exception:
            pass

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
        self._update_count_label()

    def delete_(self, _sender):
        if not self.current_id:
            self.showAlertMessage_("Seleziona uno snippet da eliminare.")
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self.showAlertMessage_("Le raccolte installate non possono essere eliminate da qui.")
            return
        error = self.handlers["delete"](self.current_id)
        if error:
            self.showAlertMessage_(error)
            return
        self.result = {"deleted": "1"}
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()
        self._update_count_label()
        if self.visible:
            select_first_table_row(self.table_view)
            self._load_selection()
        else:
            self._show_empty_state()

    def duplicate_(self, _sender):
        if not self.current_id:
            self.showAlertMessage_(t("editor.duplicate.select"))
            return
        item = self._selected_item()
        if item and item.get("editable", "1") != "1":
            self.showAlertMessage_(t("editor.duplicate.readonly"))
            return
        target = item.get("source_file") or item.get("target_file") or DEFAULT_SNIPPET_FILE
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

    def _refresh_list(self, *, select_trigger: str = "") -> None:
        self.items[:] = self.reload_items()
        self.visible = list(self.items)
        self.table_view.reloadData()
        self._update_count_label()
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
        controller.match_files = list(match_files or [DEFAULT_SNIPPET_FILE])

        win_w = WINDOW_WIDTH
        win_h = WINDOW_HEIGHT
        style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskResizable
            | NSWindowStyleMaskFullSizeContentView
        )
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, win_w, win_h),
            style,
            NSBackingStoreBuffered,
            False,
        )
        window.setTitle_(t("editor.window_title"))
        window.setMinSize_((900, 560))
        window.setTitlebarAppearsTransparent_(True)
        try:
            # Unified titlebar + content for a modern macOS tool look.
            from AppKit import NSWindowTitleVisible

            window.setTitleVisibility_(NSWindowTitleVisible)
        except Exception:
            pass
        window.setDelegate_(controller)
        controller.window = window

        root = window.contentView()
        root.setWantsLayer_(True)

        # Three non-overlapping top-level regions for layout tests:
        # toolbar (bottom full width), sidebar (left), main (right).
        toolbar_h = TOOLBAR_HEIGHT
        sidebar_w = SIDEBAR_WIDTH
        content_h = win_h - toolbar_h
        content_y = toolbar_h
        main_x = sidebar_w
        main_w = win_w - sidebar_w

        # --- Toolbar (y=0) ---
        toolbar = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, win_w, toolbar_h))
        toolbar.setAutoresizingMask_(NSViewWidthSizable)
        toolbar.setWantsLayer_(True)
        if toolbar.layer() is not None:
            try:
                toolbar.layer().setBackgroundColor_(color_control_bg().CGColor())
            except Exception:
                pass
        root.addSubview_(toolbar)

        # --- Sidebar (left, above toolbar) ---
        sidebar = make_sidebar_effect(NSMakeRect(0, content_y, sidebar_w, content_h))
        root.addSubview_(sidebar)

        # --- Main content (right, above toolbar) ---
        main = make_content_effect(NSMakeRect(main_x, content_y, main_w, content_h))
        root.addSubview_(main)

        controller.editor_content_view = root

        # Sidebar chrome
        side_pad = SPACE_MD
        title = make_label(
            "Snippet",
            x=side_pad,
            y=content_h - 44,
            width=sidebar_w - side_pad * 2,
            height=24,
        )
        title.setFont_(font_title())
        title.setTextColor_(color_label())
        sidebar.addSubview_(title)

        count = make_label(
            f"{len(items)} snippet",
            x=side_pad,
            y=content_h - 62,
            width=sidebar_w - side_pad * 2,
            height=16,
            secondary=True,
        )
        controller.count_label = count
        sidebar.addSubview_(count)

        search = NSSearchField.alloc().initWithFrame_(
            NSMakeRect(side_pad, content_h - 100, sidebar_w - side_pad * 2, 30)
        )
        search.setPlaceholderString_(t("editor.search_placeholder"))
        search.setFont_(font_body())
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "searchChanged:",
            NSControlTextDidChangeNotification,
            search,
        )
        controller.search_field = search
        sidebar.addSubview_(search)

        table_top = content_h - 116
        table_h = table_top - SPACE_MD
        table_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(side_pad, SPACE_MD, sidebar_w - side_pad * 2, table_h)
        )
        table_scroll.setBorderType_(NSBezelBorder)
        table_scroll.setHasVerticalScroller_(True)
        table_scroll.setDrawsBackground_(False)
        try:
            table_scroll.setBorderType_(0)  # no border — cleaner sidebar
        except Exception:
            pass
        table = NSTableView.alloc().initWithFrame_(table_scroll.bounds())
        configure_single_column_table(table)
        style_sidebar_table(table)
        table.setDelegate_(controller)
        table.setDataSource_(controller)
        controller.table_view = table
        table_scroll.setDocumentView_(table)
        sidebar.addSubview_(table_scroll)

        # Main form layout (coordinates relative to main view)
        pad = SPACE_LG
        form_w = main_w - pad * 2
        label_w = 120.0
        field_x = pad + label_w + SPACE_SM
        field_w = form_w - label_w - SPACE_SM

        heading = make_label(
            "Dettaglio",
            x=pad,
            y=content_h - 44,
            width=form_w,
            height=24,
        )
        heading.setFont_(font_title())
        main.addSubview_(heading)

        empty_hint = make_label(
            "Seleziona uno snippet a sinistra, oppure crea un nuovo abbreviazione.",
            x=pad,
            y=content_h - 72,
            width=form_w,
            height=18,
            secondary=True,
        )
        empty_hint.setHidden_(True)
        controller.empty_hint = empty_hint
        main.addSubview_(empty_hint)

        # Trigger
        y = content_h - 110
        main.addSubview_(
            make_label(t("editor.trigger_label"), x=pad, y=y + 4, width=label_w, secondary=True)
        )
        controller.trigger_field = make_text_field(
            x=field_x,
            y=y,
            width=field_w,
            mono=True,
            placeholder=":email  oppure  //email",
        )
        main.addSubview_(controller.trigger_field)

        # App filter
        y = content_h - 150
        main.addSubview_(
            make_label(t("editor.app_label"), x=pad, y=y + 4, width=label_w, secondary=True)
        )
        controller.if_app_field = make_text_field(
            x=field_x,
            y=y,
            width=field_w,
            placeholder="es. Mail, Slack (vuoto = ovunque)",
        )
        main.addSubview_(controller.if_app_field)

        # Hidden advanced fields (preserved for data model / advanced edits)
        def _hidden_field(value: str = "") -> NSTextField:
            field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))
            if value:
                field.setStringValue_(value)
            return field

        def _hidden_text_view() -> NSTextView:
            view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))
            view.setEditable_(True)
            return view

        controller.target_file_field = _hidden_field()
        controller.target_file_field.setStringValue_((match_files or [DEFAULT_SNIPPET_FILE])[0])
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

        # Expansion body
        y = content_h - 186
        section = make_label(
            t("editor.text_label").upper() if False else t("editor.text_label"),
            x=pad,
            y=y,
            width=form_w,
            section=True,
        )
        section.setFont_(font_section())
        main.addSubview_(section)

        replace_h = 280.0
        replace_y = y - 12 - replace_h
        replace_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(pad, replace_y, form_w, replace_h)
        )
        replace_scroll.setBorderType_(NSBezelBorder)
        replace_scroll.setHasVerticalScroller_(True)
        replace_scroll.setDrawsBackground_(True)
        replace_scroll.setBackgroundColor_(color_field_bg())
        replace_view = NSTextView.alloc().initWithFrame_(replace_scroll.bounds())
        style_editor_text_view(replace_view, editable=True, mono=False)
        replace_scroll.setDocumentView_(replace_view)
        main.addSubview_(replace_scroll)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller,
            "replaceChanged:",
            NSControlTextDidChangeNotification,
            replace_view,
        )
        controller.replace_view = replace_view

        # Preview card
        prev_label_y = replace_y - 28
        main.addSubview_(
            make_label(t("editor.preview_label"), x=pad, y=prev_label_y, width=form_w, section=True)
        )
        prev_h = 72.0
        prev_y = prev_label_y - 8 - prev_h
        if prev_y < SPACE_MD:
            prev_y = SPACE_MD
            prev_h = max(48.0, prev_label_y - 8 - prev_y)
        preview_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(pad, prev_y, form_w, prev_h)
        )
        preview_scroll.setBorderType_(NSBezelBorder)
        preview_scroll.setHasVerticalScroller_(True)
        preview_scroll.setDrawsBackground_(True)
        try:
            preview_scroll.setBackgroundColor_(NSColor.underPageBackgroundColor())
        except Exception:
            preview_scroll.setBackgroundColor_(color_control_bg())
        preview_view = NSTextView.alloc().initWithFrame_(preview_scroll.bounds())
        style_editor_text_view(preview_view, editable=False, mono=True)
        preview_view.setTextColor_(color_secondary())
        preview_scroll.setDocumentView_(preview_view)
        main.addSubview_(preview_scroll)
        controller.preview_view = preview_view

        # Toolbar buttons (relative to toolbar view, y≈12)
        btn_y = 12.0
        new_button = make_button(t("editor.new_button"), x=SPACE_MD, y=btn_y, width=92)
        new_button.setTarget_(controller)
        new_button.setAction_("new:")
        toolbar.addSubview_(new_button)

        save_button = make_button(
            t("editor.save_button"),
            x=SPACE_MD + 100,
            y=btn_y,
            width=100,
            primary=True,
        )
        save_button.setTarget_(controller)
        save_button.setAction_("save:")
        toolbar.addSubview_(save_button)

        delete_button = make_button(
            t("editor.delete_button"),
            x=SPACE_MD + 212,
            y=btn_y,
            width=92,
            destructive=True,
        )
        delete_button.setTarget_(controller)
        delete_button.setAction_("delete:")
        toolbar.addSubview_(delete_button)

        duplicate_button = make_button(
            t("editor.duplicate.button"),
            x=SPACE_MD + 316,
            y=btn_y,
            width=100,
        )
        duplicate_button.setTarget_(controller)
        duplicate_button.setAction_("duplicate:")
        toolbar.addSubview_(duplicate_button)

        close_button = make_button(
            t("editor.close_button"),
            x=win_w - SPACE_MD - 100,
            y=btn_y,
            width=100,
        )
        close_button.setTarget_(controller)
        close_button.setAction_("close:")
        toolbar.addSubview_(close_button)

        # Hairline above toolbar (as part of toolbar, not overlapping siblings)
        hairline = NSView.alloc().initWithFrame_(NSMakeRect(0, toolbar_h - 1, win_w, 1))
        hairline.setWantsLayer_(True)
        if hairline.layer() is not None:
            try:
                hairline.layer().setBackgroundColor_(color_separator().CGColor())
            except Exception:
                pass
        toolbar.addSubview_(hairline)

        # Vertical divider between sidebar and main (drawn on main left edge via border)
        divider = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 1, content_h))
        divider.setWantsLayer_(True)
        if divider.layer() is not None:
            try:
                divider.layer().setBackgroundColor_(color_separator().CGColor())
            except Exception:
                pass
        main.addSubview_(divider)

        window.center()
        window.makeKeyAndOrderFront_(None)
        controller._update_count_label()
        if initial_new:
            controller.new_(None)
        elif controller.visible:
            select_first_table_row(table)
            controller._load_selection()
        return controller

    return run_appkit_session(builder)

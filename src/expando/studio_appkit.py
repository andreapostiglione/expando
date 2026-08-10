"""Unified Expando Studio — snippets + collections in one native macOS window.

Liquid Glass layout (macOS 26 Tahoe + fallback):

  [●●●  Snippet | Raccolte          Nuovo  Salva  Elimina  Duplica  Chiudi]
  ┌──────────────────┐  ┌────────────────────────────────────────────────┐
  │ glass sidebar    │  │ glass detail card                              │
  │ search + list    │  │ form / collection                              │
  └──────────────────┘  └────────────────────────────────────────────────┘

One menubar entry → one window. Section switch is a segmented control.
"""

from __future__ import annotations

import objc
from Foundation import NSNotificationCenter, NSObject
from AppKit import (
    NSAlert,
    NSBackingStoreBuffered,
    NSControlTextDidChangeNotification,
    NSMakeRect,
    NSScrollView,
    NSSearchField,
    NSSegmentedControl,
    NSTableView,
    NSTextField,
    NSTextView,
    NSView,
    NSViewHeightSizable,
    NSViewMaxXMargin,
    NSViewMinYMargin,
    NSViewWidthSizable,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskFullSizeContentView,
    NSWindowStyleMaskResizable,
    NSWindowStyleMaskTitled,
    NSWindowTitleHidden,
    NSColor,
    NSEventModifierFlagCommand,
)
from pathlib import Path
from typing import Callable

from .i18n import t, tf
from .snippet_editor_data import DEFAULT_SNIPPET_FILE
from .ui_appkit_runtime import (
    close_appkit_session,
    configure_single_column_table,
    run_appkit_session,
    select_first_table_row,
    set_text_view_string,
)
from .ui_theme import (
    RADIUS_CARD,
    RADIUS_SIDEBAR,
    SPACE_LG,
    SPACE_MD,
    SPACE_SM,
    color_secondary,
    font_body,
    font_title,
    make_button,
    make_glass_container,
    make_glass_panel,
    make_label,
    make_text_field,
    make_window_backdrop,
    style_editor_text_view,
    style_scroll_field,
    style_sidebar_table,
)

# Traffic-light safe inset + action bar (full-size content view).
TOP_BAR_H = 56.0
TRAFFIC_LIGHT_PAD = 82.0
LIST_WIDTH = 288.0
WINDOW_W = 1120.0
WINDOW_H = 720.0
EDGE = 14.0
GAP = 12.0

SECTION_SNIPPETS = "snippets"
SECTION_COLLECTIONS = "collections"


def _set_field(field: NSTextField, value: str) -> None:
    field.setStringValue_(value)


def _set_view(view: NSTextView, value: str) -> None:
    set_text_view_string(view, value)


class _StudioController(NSObject):
    def initWithContext_(self, context: dict):
        self = objc.super(_StudioController, self).init()
        if self is None:
            return None
        self.context = context
        self.handlers = context["handlers"]
        self.snippet_items = list(context["snippet_items"])
        self.snippet_visible = list(self.snippet_items)
        self.collection_items = list(context.get("collection_items") or [])
        self.reload_snippets = context["reload_snippets"]
        self.reload_collections = context.get("reload_collections")
        self.section = context.get("initial_section") or SECTION_SNIPPETS
        self.result = None
        self.current_id = None
        self.selected_package_id = None
        return self

    # --- Table data source ---
    def numberOfRowsInTableView_(self, table_view):
        if table_view != getattr(self, "list_table", None):
            return 0
        if self.section == SECTION_COLLECTIONS:
            return len(self.collection_items)
        return len(self.snippet_visible)

    def tableView_objectValueForTableColumn_row_(self, table_view, _column, row):
        if table_view != getattr(self, "list_table", None):
            return ""
        if self.section == SECTION_COLLECTIONS:
            item = self.collection_items[row]
            return item.get("label", item.get("package_id", ""))
        item = self.snippet_visible[row]
        return item.get("label", item.get("trigger", ""))

    def tableViewSelectionDidChange_(self, notification):
        if notification.object() == getattr(self, "list_table", None):
            self._load_list_selection()

    def searchChanged_(self, notification):
        if self.section != SECTION_SNIPPETS:
            return
        sender = notification.object()
        query = str(sender.stringValue()).strip()
        from .fuzzy import fuzzy_filter_search_items

        self.snippet_visible = fuzzy_filter_search_items(query, self.snippet_items)
        self.list_table.reloadData()
        self._update_count()
        if self.snippet_visible:
            select_first_table_row(self.list_table)
            self._load_list_selection()
        else:
            self._clear_snippet_form()

    def sectionChanged_(self, sender):
        idx = int(sender.selectedSegment())
        self._switch_section(SECTION_SNIPPETS if idx == 0 else SECTION_COLLECTIONS)

    def _switch_section(self, section: str) -> None:
        self.section = section
        is_snippets = section == SECTION_SNIPPETS
        self.search_field.setHidden_(not is_snippets)
        self.detail_snippets.setHidden_(not is_snippets)
        self.detail_collections.setHidden_(is_snippets)
        for btn in (self.btn_new, self.btn_save, self.btn_delete, self.btn_duplicate):
            btn.setHidden_(not is_snippets)
        self.btn_install.setHidden_(is_snippets)

        if section == SECTION_COLLECTIONS and self.reload_collections:
            self.collection_items = list(self.reload_collections())
        self.list_table.reloadData()
        self._update_count()
        if self.list_table.numberOfRows() > 0:
            select_first_table_row(self.list_table)
            self._load_list_selection()
        elif is_snippets:
            self._clear_snippet_form()
        else:
            self._clear_collection_detail()

    def _load_list_selection(self) -> None:
        row = self.list_table.selectedRow()
        if row < 0:
            return
        if self.section == SECTION_COLLECTIONS:
            if row >= len(self.collection_items):
                return
            self._load_collection(self.collection_items[row])
            return
        if row >= len(self.snippet_visible):
            return
        self._load_snippet(self.snippet_visible[row])

    def _load_snippet(self, item: dict) -> None:
        self.current_id = item.get("id")
        self.selected_package_id = None
        self.empty_hint.setHidden_(True)
        _set_field(self.trigger_field, item.get("trigger", ""))
        _set_field(self.if_app_field, item.get("if_app", ""))
        _set_field(
            self.target_file_field,
            item.get("target_file", item.get("source_file", DEFAULT_SNIPPET_FILE)),
        )
        for name, key in (
            ("unless_app_field", "unless_app"),
            ("if_bundle_field", "if_bundle"),
            ("unless_bundle_field", "unless_bundle"),
            ("if_title_field", "if_title"),
            ("unless_title_field", "unless_title"),
            ("regex_field", "regex"),
            ("image_field", "image"),
            ("priority_field", "priority"),
            ("force_clipboard_field", "force_clipboard"),
        ):
            field = getattr(self, name, None)
            if field is not None:
                _set_field(field, item.get(key, ""))
        _set_view(self.when_view, item.get("when", ""))
        _set_view(self.form_view, item.get("form", ""))
        _set_view(self.vars_view, item.get("vars", ""))
        _set_view(self.replace_view, item.get("replace", ""))
        editable = item.get("editable", "1") == "1"
        self.replace_view.setEditable_(editable)
        self.form_view.setEditable_(editable)
        self.vars_view.setEditable_(editable)
        self.when_view.setEditable_(editable)
        self._update_preview()

    def _clear_snippet_form(self) -> None:
        self.current_id = None
        self.empty_hint.setHidden_(False)
        _set_field(self.trigger_field, "")
        _set_field(self.if_app_field, "")
        _set_view(self.replace_view, "")
        _set_view(self.preview_view, "")
        _set_view(self.form_view, "")
        _set_view(self.vars_view, "")
        _set_view(self.when_view, "")

    def _load_collection(self, item: dict) -> None:
        self.selected_package_id = item.get("package_id") or item.get("trigger")
        self.current_id = None
        name = item.get("label") or self.selected_package_id or ""
        _set_field(self.collection_title, name)
        _set_view(self.collection_body, item.get("preview", ""))
        installed = item.get("installed") == "1"
        self.btn_install.setTitle_(
            t("studio.collections.installed") if installed else t("studio.collections.install")
        )
        self.btn_install.setEnabled_(not installed)

    def _clear_collection_detail(self) -> None:
        self.selected_package_id = None
        _set_field(self.collection_title, "")
        _set_view(self.collection_body, t("studio.collections.empty"))
        self.btn_install.setEnabled_(False)

    def replaceChanged_(self, _notification):
        self._update_preview()

    def _update_preview(self) -> None:
        replace_text = str(self.replace_view.string())
        config_dir = self.context.get("config_dir")
        if config_dir is not None:
            from .config import Match
            from .snippet_editor_data import preview_snippet_text

            match = Match(triggers=[":preview"], replace=replace_text)
            preview = preview_snippet_text(match, config_dir, replace_text=replace_text)
            _set_view(self.preview_view, preview)
            return
        _set_view(self.preview_view, replace_text)

    def _update_count(self) -> None:
        if self.section == SECTION_COLLECTIONS:
            n = len(self.collection_items)
            self.count_label.setStringValue_(tf("studio.count.collections", count=n))
        else:
            total = len(self.snippet_items)
            shown = len(self.snippet_visible)
            if shown == total:
                self.count_label.setStringValue_(tf("studio.count.snippets", count=total))
            else:
                self.count_label.setStringValue_(f"{shown} / {total}")

    def new_(self, _sender):
        self._ensure_snippets_section()
        self.current_id = None
        self.empty_hint.setHidden_(True)
        _set_field(self.trigger_field, ":nuovo")
        _set_field(self.if_app_field, "")
        _set_view(self.replace_view, "")
        _set_view(self.form_view, "")
        _set_view(self.vars_view, "")
        _set_view(self.when_view, "")
        self.replace_view.setEditable_(True)
        self._update_preview()
        try:
            self.window.makeFirstResponder_(self.trigger_field)
        except Exception:
            pass

    def save_(self, _sender):
        if self.section != SECTION_SNIPPETS:
            return
        payload = self._payload()
        if not payload["trigger"]:
            self.showStudioAlert_(t("studio.alert.trigger_empty"))
            return
        item = self._selected_snippet()
        if self.current_id and item and item.get("editable", "1") != "1":
            self.showStudioAlert_(t("studio.alert.readonly"))
            return
        handler = self.handlers["save"] if self.current_id else self.handlers["create"]
        error = handler(payload)
        if error:
            self.showStudioAlert_(error)
            return
        self.result = {"saved": "1"}
        self._refresh_snippets()

    def delete_(self, _sender):
        if self.section != SECTION_SNIPPETS or not self.current_id:
            self.showStudioAlert_(t("studio.alert.select_delete"))
            return
        item = self._selected_snippet()
        if item and item.get("editable", "1") != "1":
            self.showStudioAlert_(t("studio.alert.collection_locked"))
            return
        error = self.handlers["delete"](self.current_id)
        if error:
            self.showStudioAlert_(error)
            return
        self.result = {"deleted": "1"}
        self._refresh_snippets()

    def duplicate_(self, _sender):
        if self.section != SECTION_SNIPPETS or not self.current_id:
            self.showStudioAlert_(t("editor.duplicate.select"))
            return
        item = self._selected_snippet()
        if item and item.get("editable", "1") != "1":
            self.showStudioAlert_(t("editor.duplicate.readonly"))
            return
        target = item.get("source_file") or item.get("target_file") or DEFAULT_SNIPPET_FILE
        handler = self.handlers.get("duplicate")
        if not handler:
            return
        error = handler(self.current_id, target)
        if error:
            self.showStudioAlert_(error)
            return
        self.result = {"duplicated": "1"}
        self._refresh_snippets()

    def install_(self, _sender):
        if self.section != SECTION_COLLECTIONS or not self.selected_package_id:
            return
        handler = self.handlers.get("install_package")
        if not handler:
            return
        error = handler(str(self.selected_package_id))
        if error:
            self.showStudioAlert_(error)
            return
        self.result = {"installed": str(self.selected_package_id)}
        if self.reload_collections:
            self.collection_items = list(self.reload_collections())
            self.list_table.reloadData()
            self._update_count()
            self.btn_install.setTitle_(t("studio.collections.installed"))
            self.btn_install.setEnabled_(False)

    def close_(self, _sender):
        close_appkit_session(self)

    def windowShouldClose_(self, _sender):
        self.close_(None)
        return True

    def _ensure_snippets_section(self) -> None:
        if self.section != SECTION_SNIPPETS:
            try:
                self.segment.setSelectedSegment_(0)
            except Exception:
                pass
            self._switch_section(SECTION_SNIPPETS)

    def _selected_snippet(self):
        row = self.list_table.selectedRow()
        if row < 0 or row >= len(self.snippet_visible):
            return None
        return self.snippet_visible[row]

    def _refresh_snippets(self) -> None:
        self.snippet_items = list(self.reload_snippets())
        query = str(self.search_field.stringValue()).strip()
        if query:
            from .fuzzy import fuzzy_filter_search_items

            self.snippet_visible = fuzzy_filter_search_items(query, self.snippet_items)
        else:
            self.snippet_visible = list(self.snippet_items)
        self.list_table.reloadData()
        self._update_count()
        if self.snippet_visible:
            select_first_table_row(self.list_table)
            self._load_list_selection()
        else:
            self._clear_snippet_form()

    def _payload(self) -> dict[str, str]:
        return {
            "id": self.current_id or "",
            "trigger": str(self.trigger_field.stringValue()).strip(),
            "replace": str(self.replace_view.string()).strip(),
            "if_app": str(self.if_app_field.stringValue()).strip(),
            "unless_app": str(self.unless_app_field.stringValue()).strip(),
            "if_bundle": str(self.if_bundle_field.stringValue()).strip(),
            "unless_bundle": str(self.unless_bundle_field.stringValue()).strip(),
            "if_title": str(self.if_title_field.stringValue()).strip(),
            "unless_title": str(self.unless_title_field.stringValue()).strip(),
            "regex": str(self.regex_field.stringValue()).strip(),
            "when": str(self.when_view.string()).strip(),
            "image": str(self.image_field.stringValue()).strip(),
            "priority": str(self.priority_field.stringValue()).strip(),
            "force_clipboard": str(self.force_clipboard_field.stringValue()).strip(),
            "target_file": str(self.target_file_field.stringValue()).strip(),
            "form": str(self.form_view.string()).strip(),
            "vars": str(self.vars_view.string()).strip(),
        }

    def showStudioAlert_(self, message) -> None:
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Expando")
        alert.setInformativeText_(str(message))
        alert.addButtonWithTitle_(t("ui.ok"))
        alert.runModal()


def run_expando_studio(
    snippet_items: list[dict[str, str]],
    *,
    on_save: Callable[[dict[str, str]], str | None],
    on_create: Callable[[dict[str, str]], str | None],
    on_delete: Callable[[str], str | None],
    on_duplicate: Callable[[str, str], str | None] | None = None,
    on_move: Callable[[str, str], str | None] | None = None,
    reload_snippets: Callable[[], list[dict[str, str]]],
    collection_items: list[dict[str, str]] | None = None,
    reload_collections: Callable[[], list[dict[str, str]]] | None = None,
    on_install_package: Callable[[str], str | None] | None = None,
    match_files: list[str] | None = None,
    config_dir: Path | None = None,
    initial_new: bool = False,
    initial_section: str = SECTION_SNIPPETS,
) -> dict[str, str] | None:
    handlers = {
        "save": on_save,
        "create": on_create,
        "delete": on_delete,
        "duplicate": on_duplicate,
        "move": on_move,
        "install_package": on_install_package,
    }
    context = {
        "handlers": handlers,
        "snippet_items": snippet_items,
        "reload_snippets": reload_snippets,
        "collection_items": collection_items or [],
        "reload_collections": reload_collections,
        "config_dir": config_dir,
        "match_files": match_files or [DEFAULT_SNIPPET_FILE],
        "initial_section": initial_section,
    }

    def builder():
        controller = _StudioController.alloc().initWithContext_(context)
        win_w, win_h = WINDOW_W, WINDOW_H
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
        window.setTitle_(t("studio.window_title"))
        window.setMinSize_((940, 580))
        window.setTitlebarAppearsTransparent_(True)
        window.setTitleVisibility_(NSWindowTitleHidden)
        try:
            window.setBackgroundColor_(NSColor.clearColor())
        except Exception:
            pass
        window.setDelegate_(controller)
        controller.window = window
        root = window.contentView()
        controller.editor_content_view = root

        # Soft ambient backdrop — Liquid Glass samples light from surroundings
        backdrop = make_window_backdrop(NSMakeRect(0, 0, win_w, win_h))
        root.addSubview_(backdrop)

        top_h = TOP_BAR_H
        # Floating panels sit below the titlebar chrome with edge insets
        body_bottom = EDGE
        body_h = win_h - top_h - body_bottom
        body_y = body_bottom

        # --- Top bar (draggable, transparent; controls use glass bezels) ---
        top = NSView.alloc().initWithFrame_(NSMakeRect(0, win_h - top_h, win_w, top_h))
        top.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        root.addSubview_(top)

        segment = NSSegmentedControl.alloc().initWithFrame_(
            NSMakeRect(TRAFFIC_LIGHT_PAD, 14, 268, 28)
        )
        segment.setSegmentCount_(2)
        segment.setLabel_forSegment_(t("studio.nav.snippets"), 0)
        segment.setLabel_forSegment_(t("studio.nav.collections"), 1)
        try:
            from AppKit import NSSegmentStyleCapsule

            segment.setSegmentStyle_(NSSegmentStyleCapsule)
        except Exception:
            pass
        try:
            segment.setWidth_forSegment_(124, 0)
            segment.setWidth_forSegment_(124, 1)
        except Exception:
            pass
        segment.setTarget_(controller)
        segment.setAction_("sectionChanged:")
        controller.segment = segment
        top.addSubview_(segment)

        btn_y = 12.0
        close_btn = make_button(
            t("editor.close_button"), x=win_w - EDGE - 88, y=btn_y, width=88
        )
        close_btn.setTarget_(controller)
        close_btn.setAction_("close:")
        top.addSubview_(close_btn)

        controller.btn_install = make_button(
            t("studio.collections.install"),
            x=win_w - EDGE - 88 - 12 - 140,
            y=btn_y,
            width=140,
            primary=True,
        )
        controller.btn_install.setTarget_(controller)
        controller.btn_install.setAction_("install:")
        controller.btn_install.setHidden_(True)
        top.addSubview_(controller.btn_install)

        ax = win_w - EDGE - 88 - 12
        specs = [
            ("btn_duplicate", t("editor.duplicate.button"), 100, "duplicate:", False, False),
            ("btn_delete", t("editor.delete_button"), 90, "delete:", False, True),
            ("btn_save", t("editor.save_button"), 96, "save:", True, False),
            ("btn_new", t("editor.new_button"), 90, "new:", False, False),
        ]
        for attr, title, width, action, primary, destructive in specs:
            ax -= width + 8
            btn = make_button(
                title, x=ax, y=btn_y, width=width, primary=primary, destructive=destructive
            )
            btn.setTarget_(controller)
            btn.setAction_(action)
            setattr(controller, attr, btn)
            top.addSubview_(btn)

        try:
            controller.btn_new.setKeyEquivalent_("n")
            controller.btn_new.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
            controller.btn_save.setKeyEquivalent_("s")
            controller.btn_save.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
            controller.btn_duplicate.setKeyEquivalent_("d")
            controller.btn_duplicate.setKeyEquivalentModifierMask_(NSEventModifierFlagCommand)
        except Exception:
            pass

        # --- Glass body: floating sidebar + detail (merge when close on Tahoe) ---
        glass_host, glass_body = make_glass_container(
            NSMakeRect(0, 0, win_w, win_h - top_h),
            spacing=GAP + 8,
        )
        glass_host.setFrame_(NSMakeRect(0, 0, win_w, win_h - top_h))
        glass_host.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        root.addSubview_(glass_host)

        list_x = EDGE
        list_frame = NSMakeRect(list_x, body_y, LIST_WIDTH, body_h)
        list_shell, list_panel = make_glass_panel(
            list_frame,
            corner_radius=RADIUS_SIDEBAR,
            clear=False,
            tint=True,
            autoresizing=NSViewHeightSizable | NSViewMaxXMargin,
        )
        glass_body.addSubview_(list_shell)

        count = make_label(
            "",
            x=SPACE_MD,
            y=body_h - 30,
            width=LIST_WIDTH - SPACE_MD * 2,
            height=16,
            secondary=True,
        )
        controller.count_label = count
        list_panel.addSubview_(count)

        search = NSSearchField.alloc().initWithFrame_(
            NSMakeRect(12, body_h - 64, LIST_WIDTH - 24, 30)
        )
        search.setPlaceholderString_(t("editor.search_placeholder"))
        search.setFont_(font_body())
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller, "searchChanged:", NSControlTextDidChangeNotification, search
        )
        controller.search_field = search
        list_panel.addSubview_(search)

        list_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(10, 12, LIST_WIDTH - 20, body_h - 84)
        )
        list_scroll.setDrawsBackground_(False)
        list_scroll.setBorderType_(0)
        list_scroll.setHasVerticalScroller_(True)
        list_scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        list_table = NSTableView.alloc().initWithFrame_(list_scroll.bounds())
        configure_single_column_table(list_table)
        style_sidebar_table(list_table)
        list_table.setDelegate_(controller)
        list_table.setDataSource_(controller)
        controller.list_table = list_table
        list_scroll.setDocumentView_(list_table)
        list_panel.addSubview_(list_scroll)

        # Detail glass card
        main_x = EDGE + LIST_WIDTH + GAP
        main_w = win_w - main_x - EDGE
        main_frame = NSMakeRect(main_x, body_y, main_w, body_h)
        main_shell, main = make_glass_panel(
            main_frame,
            corner_radius=RADIUS_CARD,
            clear=False,
            tint=False,
            autoresizing=NSViewWidthSizable | NSViewHeightSizable,
        )
        glass_body.addSubview_(main_shell)

        pad = SPACE_LG
        form_w = main_w - pad * 2
        label_w = 104.0
        field_x = pad + label_w + SPACE_SM
        field_w = form_w - label_w - SPACE_SM

        detail_snippets = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, main_w, body_h))
        detail_snippets.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        controller.detail_snippets = detail_snippets
        main.addSubview_(detail_snippets)

        heading = make_label(
            t("studio.detail.snippet"), x=pad, y=body_h - 38, width=form_w, height=24
        )
        heading.setFont_(font_title())
        detail_snippets.addSubview_(heading)

        empty_hint = make_label(
            t("studio.snippets.empty"),
            x=pad,
            y=body_h - 62,
            width=form_w,
            height=18,
            secondary=True,
        )
        controller.empty_hint = empty_hint
        detail_snippets.addSubview_(empty_hint)

        y = body_h - 104
        detail_snippets.addSubview_(
            make_label(t("editor.trigger_label"), x=pad, y=y + 6, width=label_w, secondary=True)
        )
        controller.trigger_field = make_text_field(
            x=field_x, y=y, width=field_w, mono=True, placeholder=":email  ·  //email"
        )
        detail_snippets.addSubview_(controller.trigger_field)

        y = body_h - 148
        detail_snippets.addSubview_(
            make_label(t("editor.app_label"), x=pad, y=y + 6, width=label_w, secondary=True)
        )
        controller.if_app_field = make_text_field(
            x=field_x, y=y, width=field_w, placeholder="Mail, Slack… (vuoto = ovunque)"
        )
        detail_snippets.addSubview_(controller.if_app_field)

        def _hidden_field() -> NSTextField:
            return NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))

        def _hidden_tv() -> NSTextView:
            v = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 1, 1))
            v.setEditable_(True)
            return v

        controller.target_file_field = _hidden_field()
        controller.target_file_field.setStringValue_(
            (match_files or [DEFAULT_SNIPPET_FILE])[0]
        )
        controller.unless_app_field = _hidden_field()
        controller.if_bundle_field = _hidden_field()
        controller.unless_bundle_field = _hidden_field()
        controller.if_title_field = _hidden_field()
        controller.unless_title_field = _hidden_field()
        controller.image_field = _hidden_field()
        controller.regex_field = _hidden_field()
        controller.priority_field = _hidden_field()
        controller.force_clipboard_field = _hidden_field()
        controller.when_view = _hidden_tv()
        controller.form_view = _hidden_tv()
        controller.vars_view = _hidden_tv()

        y = body_h - 186
        detail_snippets.addSubview_(
            make_label(t("editor.text_label"), x=pad, y=y, width=form_w, section=True)
        )
        replace_h = 248.0
        replace_y = y - 12 - replace_h
        replace_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(pad, replace_y, form_w, replace_h)
        )
        replace_scroll.setHasVerticalScroller_(True)
        replace_scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        style_scroll_field(replace_scroll)
        replace_view = NSTextView.alloc().initWithFrame_(replace_scroll.bounds())
        style_editor_text_view(replace_view, editable=True)
        replace_scroll.setDocumentView_(replace_view)
        detail_snippets.addSubview_(replace_scroll)
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            controller, "replaceChanged:", NSControlTextDidChangeNotification, replace_view
        )
        controller.replace_view = replace_view

        prev_label_y = replace_y - 28
        detail_snippets.addSubview_(
            make_label(t("editor.preview_label"), x=pad, y=prev_label_y, width=form_w, section=True)
        )
        prev_h = 76.0
        prev_y = max(16.0, prev_label_y - 10 - prev_h)
        preview_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(pad, prev_y, form_w, prev_h)
        )
        preview_scroll.setHasVerticalScroller_(True)
        preview_scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        style_scroll_field(preview_scroll)
        try:
            preview_scroll.setBackgroundColor_(
                NSColor.underPageBackgroundColor().colorWithAlphaComponent_(0.55)
            )
        except Exception:
            pass
        preview_view = NSTextView.alloc().initWithFrame_(preview_scroll.bounds())
        style_editor_text_view(preview_view, editable=False, mono=True)
        preview_view.setTextColor_(color_secondary())
        preview_scroll.setDocumentView_(preview_view)
        detail_snippets.addSubview_(preview_scroll)
        controller.preview_view = preview_view

        # Collections detail
        detail_collections = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, main_w, body_h))
        detail_collections.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        controller.detail_collections = detail_collections
        detail_collections.setHidden_(True)
        main.addSubview_(detail_collections)

        col_heading = make_label(
            t("studio.detail.collection"), x=pad, y=body_h - 38, width=form_w, height=24
        )
        col_heading.setFont_(font_title())
        detail_collections.addSubview_(col_heading)

        controller.collection_title = make_text_field(x=pad, y=body_h - 84, width=form_w)
        controller.collection_title.setEditable_(False)
        controller.collection_title.setBezeled_(False)
        controller.collection_title.setDrawsBackground_(False)
        controller.collection_title.setFont_(font_title())
        detail_collections.addSubview_(controller.collection_title)

        body_scroll = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(pad, 20, form_w, body_h - 120)
        )
        body_scroll.setHasVerticalScroller_(True)
        body_scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        style_scroll_field(body_scroll)
        body_view = NSTextView.alloc().initWithFrame_(body_scroll.bounds())
        style_editor_text_view(body_view, editable=False)
        body_scroll.setDocumentView_(body_view)
        detail_collections.addSubview_(body_scroll)
        controller.collection_body = body_view

        window.center()

        section = (
            initial_section
            if initial_section in {SECTION_SNIPPETS, SECTION_COLLECTIONS}
            else SECTION_SNIPPETS
        )
        seg_idx = 0 if section == SECTION_SNIPPETS else 1
        segment.setSelectedSegment_(seg_idx)
        controller._switch_section(section)
        if initial_new and section == SECTION_SNIPPETS:
            controller.new_(None)
        return controller

    return run_appkit_session(builder)


def run_snippet_editor(
    items: list[dict[str, str]] | None = None,
    *args,
    **kwargs,
):
    """Backward-compatible alias used by tests and older imports."""
    if "reload_items" in kwargs and "reload_snippets" not in kwargs:
        kwargs["reload_snippets"] = kwargs.pop("reload_items")
    if items is not None:
        return run_expando_studio(items, *args, **kwargs)
    return run_expando_studio(*args, **kwargs)

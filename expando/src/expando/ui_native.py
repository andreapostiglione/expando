from __future__ import annotations

from .fuzzy import fuzzy_filter_search_items
from .ui_bridge import _use_appkit

# Tkinter-based search picker and form dialog.
# Used ONLY as fallback:
#   - when EXPANDO_UI=tk
#   - on non-Darwin
#   - when AppKit/PyObjC unavailable
# Preferred path on macOS (default) is ui_appkit.py selected by _use_appkit().


def _import_tk():
    import tkinter as tk
    from tkinter import ttk

    return tk, ttk


def _configure_style(root) -> None:
    root.option_add("*Font", "SF Pro Text 13")
    root.option_add("*Background", "#f5f5f7")
    root.option_add("*Foreground", "#1d1d1f")


class SearchPicker:
    def __init__(self, items: list[dict[str, str]]) -> None:
        tk, _ttk = _import_tk()
        self._tk = tk

        self.items = items
        self.result: dict[str, str] | None = None
        self.root = tk.Tk()
        _configure_style(self.root)
        self.root.title("Expando")
        self.root.geometry("720x420")
        self.root.minsize(560, 320)
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._cancel)
        self.root.bind("<Escape>", lambda _event: self._cancel())

    def _build(self) -> None:
        tk = self._tk
        _, ttk = _import_tk()

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        search_row = ttk.Frame(container)
        search_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_row, text="Search").pack(side=tk.LEFT)
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", lambda *_args: self._refresh_list())
        entry = ttk.Entry(search_row, textvariable=self.query_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        entry.focus_set()

        panes = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(panes)
        self.listbox = tk.Listbox(list_frame, activestyle="dotbox", exportselection=False)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self._update_preview())
        self.listbox.bind("<Double-Button-1>", lambda _event: self._accept())
        self.listbox.bind("<Return>", lambda _event: self._accept())
        panes.add(list_frame, weight=2)

        preview_frame = ttk.Frame(panes, padding=(8, 0, 0, 0))
        ttk.Label(preview_frame, text="Preview").pack(anchor=tk.W)
        self.preview = tk.Text(preview_frame, wrap=tk.WORD, height=12, relief=tk.FLAT, padx=8, pady=8)
        self.preview.configure(state=tk.DISABLED, background="#ffffff", foreground="#1d1d1f")
        self.preview.pack(fill=tk.BOTH, expand=True)
        panes.add(preview_frame, weight=3)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Cancel", command=self._cancel).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Insert", command=self._accept).pack(side=tk.RIGHT, padx=(0, 8))

        self._refresh_list()

    def _filtered_items(self) -> list[dict[str, str]]:
        query = self.query_var.get().strip()
        return fuzzy_filter_search_items(query, self.items)

    def _refresh_list(self) -> None:
        tk = self._tk
        self.listbox.delete(0, tk.END)
        self._visible = self._filtered_items()
        for item in self._visible:
            self.listbox.insert(tk.END, item.get("label", item["trigger"]))
        if self._visible:
            self.listbox.selection_set(0)
            self.listbox.activate(0)
        self._update_preview()

    def _selected_item(self) -> dict[str, str] | None:
        if not getattr(self, "_visible", None):
            return None
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self._visible[selection[0]]

    def _update_preview(self) -> None:
        tk = self._tk
        item = self._selected_item()
        preview_text = item.get("preview", "") if item else ""
        self.preview.configure(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        self.preview.insert(tk.END, preview_text)
        self.preview.configure(state=tk.DISABLED)

    def _accept(self) -> None:
        item = self._selected_item()
        if not item:
            return
        self.result = {"id": item["id"], "trigger": item["trigger"]}
        self.root.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.root.destroy()

    def run(self) -> dict[str, str] | None:
        self.root.mainloop()
        return self.result


class FormDialog:
    def __init__(self, fields: list[dict[str, str]]) -> None:
        tk, _ttk = _import_tk()
        self._tk = tk

        self.fields = fields
        self.result: dict[str, str] | None = None
        self.entries: dict[str, object] = {}
        self.root = tk.Tk()
        _configure_style(self.root)
        self.root.title("Expando")
        self.root.geometry("480x360")
        self.root.minsize(400, 240)
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._cancel)
        self.root.bind("<Escape>", lambda _event: self._cancel())

    def _build(self) -> None:
        tk = self._tk
        _, ttk = _import_tk()

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Fill in the snippet fields").pack(anchor=tk.W, pady=(0, 12))

        form = ttk.Frame(container)
        form.pack(fill=tk.BOTH, expand=True)
        form.columnconfigure(1, weight=1)

        for row_index, field in enumerate(self.fields):
            label = field.get("label") or field["name"]
            ttk.Label(form, text=label).grid(row=row_index, column=0, sticky=tk.W, pady=6, padx=(0, 10))
            entry = ttk.Entry(form)
            default = field.get("default", "")
            if default:
                entry.insert(0, default)
            entry.grid(row=row_index, column=1, sticky=tk.EW, pady=6)
            self.entries[field["name"]] = entry

        if self.entries:
            first = next(iter(self.entries.values()))
            first.focus_set()

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(14, 0))
        ttk.Button(actions, text="Cancel", command=self._cancel).pack(side=tk.RIGHT)
        ttk.Button(actions, text="OK", command=self._accept).pack(side=tk.RIGHT, padx=(0, 8))
        self.root.bind("<Return>", lambda _event: self._accept())

    def _accept(self) -> None:
        self.result = {name: entry.get() for name, entry in self.entries.items()}
        self.root.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.root.destroy()

    def run(self) -> dict[str, str] | None:
        self.root.mainloop()
        return self.result


def run_search_picker(items: list[dict[str, str]]) -> dict[str, str] | None:
    if _use_appkit():
        # Preferred native path (AppKit)
        from .ui_appkit import run_search_picker as appkit_search

        return appkit_search(items)
    # Tk fallback
    return SearchPicker(items).run()


def run_form_dialog(fields: list[dict[str, str]]) -> dict[str, str] | None:
    if _use_appkit():
        from .ui_appkit import run_form_dialog as appkit_form

        return appkit_form(fields)
    return FormDialog(fields).run()
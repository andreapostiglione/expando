from __future__ import annotations

from pathlib import Path
from typing import Callable

from .fuzzy import fuzzy_filter_search_items
from .ui_bridge import _use_appkit

# Tkinter-based full snippet editor (search + edit + forms).
# Retained strictly as fallback when _use_appkit() returns False
# (EXPANDO_UI=tk, non-Darwin, or missing AppKit). The AppKit
# implementation lives in snippet_editor_appkit.py.


def _import_tk():
    import tkinter as tk
    from tkinter import messagebox, ttk

    return tk, ttk, messagebox


class SnippetEditor:
    def __init__(
        self,
        items: list[dict[str, str]],
        *,
        on_save: Callable[[dict[str, str]], str | None],
        on_create: Callable[[dict[str, str]], str | None],
        on_delete: Callable[[str], str | None],
    ) -> None:
        self.items = items
        self.on_save = on_save
        self.on_create = on_create
        self.on_delete = on_delete
        self.result: dict[str, str] | None = None
        self._visible: list[dict[str, str]] = []
        tk, ttk, messagebox = _import_tk()
        self._tk = tk
        self._ttk = ttk
        self._messagebox = messagebox

        self.root = tk.Tk()
        self._configure_style()
        self.root.title("Expando — Snippet editor")
        self.root.geometry("920x720")
        self.root.minsize(760, 600)
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.bind("<Escape>", lambda _event: self._close())

    def _configure_style(self) -> None:
        self.root.option_add("*Font", "SF Pro Text 13")
        self.root.option_add("*Background", "#f5f5f7")
        self.root.option_add("*Foreground", "#1d1d1f")

    def _build(self) -> None:
        tk = self._tk
        ttk = self._ttk

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        search_row = ttk.Frame(container)
        search_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_row, text="Cerca").pack(side=tk.LEFT)
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", lambda *_args: self._refresh_list())
        ttk.Entry(search_row, textvariable=self.query_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0)
        )

        panes = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.Frame(panes)
        self.listbox = tk.Listbox(list_frame, activestyle="dotbox", exportselection=False)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self._load_selection())
        panes.add(list_frame, weight=2)

        editor_frame = ttk.Frame(panes, padding=(8, 0, 0, 0))
        editor_frame.columnconfigure(1, weight=1)
        editor_frame.rowconfigure(6, weight=1)

        ttk.Label(editor_frame, text="Trigger").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.trigger_var = tk.StringVar()
        self.trigger_var.trace_add("write", lambda *_args: self._update_preview())
        ttk.Entry(editor_frame, textvariable=self.trigger_var).grid(
            row=0, column=1, sticky=tk.EW, pady=4
        )

        ttk.Label(editor_frame, text="Solo in app").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.if_app_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.if_app_var).grid(
            row=1, column=1, sticky=tk.EW, pady=4
        )
        ttk.Label(
            editor_frame,
            text="Virgola per più app (es. Terminal, Cursor). Vuoto = tutte le app.",
            font=("SF Pro Text", 11),
        ).grid(row=1, column=2, sticky=tk.W, padx=(8, 0))

        ttk.Label(editor_frame, text="Form").grid(row=2, column=0, sticky=tk.NW, pady=4)
        self.form_text = tk.Text(editor_frame, wrap=tk.NONE, height=3, relief=tk.FLAT, padx=8, pady=6)
        self.form_text.configure(background="#ffffff", foreground="#1d1d1f")
        self.form_text.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=(4, 0))
        ttk.Label(
            editor_frame,
            text="Una riga per campo: nome|etichetta|default",
            font=("SF Pro Text", 11),
        ).grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(0, 4))

        ttk.Label(editor_frame, text="Variabili").grid(row=4, column=0, sticky=tk.NW, pady=4)
        self.vars_text = tk.Text(editor_frame, wrap=tk.NONE, height=5, relief=tk.FLAT, padx=8, pady=6)
        self.vars_text.configure(background="#ffffff", foreground="#1d1d1f")
        self.vars_text.grid(row=4, column=1, columnspan=2, sticky=tk.EW, pady=(4, 0))
        ttk.Label(
            editor_frame,
            text="Lista YAML (come in match YAML: vars:)",
            font=("SF Pro Text", 11),
        ).grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=(0, 4))

        ttk.Label(editor_frame, text="Testo").grid(row=6, column=0, sticky=tk.NW, pady=4)
        self.replace_text = tk.Text(editor_frame, wrap=tk.WORD, height=8, relief=tk.FLAT, padx=8, pady=8)
        self.replace_text.configure(background="#ffffff", foreground="#1d1d1f")
        self.replace_text.grid(row=6, column=1, columnspan=2, sticky=tk.NSEW, pady=4)
        self.replace_text.bind("<<Modified>>", self._on_replace_modified)

        ttk.Label(editor_frame, text="Anteprima").grid(row=7, column=0, sticky=tk.NW, pady=4)
        self.preview_text = tk.Text(
            editor_frame,
            wrap=tk.WORD,
            height=4,
            relief=tk.FLAT,
            padx=8,
            pady=8,
            state=tk.DISABLED,
            background="#f0f0f2",
            foreground="#1d1d1f",
        )
        self.preview_text.grid(row=7, column=1, columnspan=2, sticky=tk.NSEW, pady=4)
        panes.add(editor_frame, weight=3)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Nuovo", command=self._new_snippet).pack(side=tk.LEFT)
        ttk.Button(actions, text="Salva", command=self._save_snippet).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Elimina", command=self._delete_snippet).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Chiudi", command=self._close).pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="Seleziona uno snippet o creane uno nuovo.")
        ttk.Label(container, textvariable=self.status_var).pack(anchor=tk.W, pady=(8, 0))

        self._current_id: str | None = None
        self._refresh_list()

    def _on_replace_modified(self, _event=None) -> None:
        self.replace_text.edit_modified(False)
        self._update_preview()

    def _filtered_items(self) -> list[dict[str, str]]:
        query = self.query_var.get().strip()
        return fuzzy_filter_search_items(query, self.items)

    def _refresh_list(self) -> None:
        tk = self._tk
        self.listbox.delete(0, tk.END)
        self._visible = self._filtered_items()
        for item in self._visible:
            self.listbox.insert(tk.END, item.get("label", item.get("trigger", "")))
        if self._visible:
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self._load_selection()
        else:
            self._clear_form()

    def _selected_item(self) -> dict[str, str] | None:
        if not self._visible:
            return None
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self._visible[selection[0]]

    def _clear_form(self) -> None:
        tk = self._tk
        self._current_id = None
        self.trigger_var.set("")
        self.if_app_var.set("")
        self.form_text.delete("1.0", tk.END)
        self.vars_text.delete("1.0", tk.END)
        self.replace_text.delete("1.0", tk.END)
        self._update_preview()

    def _load_selection(self) -> None:
        tk = self._tk
        item = self._selected_item()
        if not item:
            self._clear_form()
            return
        self._current_id = item.get("id")
        self.trigger_var.set(item.get("trigger", ""))
        self.if_app_var.set(item.get("if_app", ""))
        self.form_text.delete("1.0", tk.END)
        self.form_text.insert(tk.END, item.get("form", ""))
        self.vars_text.delete("1.0", tk.END)
        self.vars_text.insert(tk.END, item.get("vars", ""))
        self.replace_text.delete("1.0", tk.END)
        self.replace_text.insert(tk.END, item.get("replace", ""))
        editable = item.get("editable", "1") == "1"
        state = tk.NORMAL if editable else tk.DISABLED
        self.replace_text.configure(state=state)
        self.form_text.configure(state=state)
        self.vars_text.configure(state=state)
        self.status_var.set(
            "Modifica lo snippet selezionato."
            if editable
            else "I package hub sono in sola lettura. Installa in match/ per modificarli."
        )
        self._update_preview()

    def _update_preview(self) -> None:
        tk = self._tk
        preview = self.replace_text.get("1.0", tk.END).strip()
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, preview or "(vuoto)")
        self.preview_text.configure(state=tk.DISABLED)

    def _payload(self) -> dict[str, str]:
        tk = self._tk
        return {
            "id": self._current_id or "",
            "trigger": self.trigger_var.get().strip(),
            "replace": self.replace_text.get("1.0", tk.END).strip(),
            "if_app": self.if_app_var.get().strip(),
            "form": self.form_text.get("1.0", tk.END).strip(),
            "vars": self.vars_text.get("1.0", tk.END).strip(),
        }

    def _new_snippet(self) -> None:
        tk = self._tk
        self._current_id = None
        self.trigger_var.set(":nuovo")
        self.if_app_var.set("")
        self.form_text.configure(state=tk.NORMAL)
        self.vars_text.configure(state=tk.NORMAL)
        self.form_text.delete("1.0", tk.END)
        self.vars_text.delete("1.0", tk.END)
        self.replace_text.configure(state=tk.NORMAL)
        self.replace_text.delete("1.0", tk.END)
        self.status_var.set("Nuovo snippet — salva per aggiungerlo a dev.yml.")
        self._update_preview()

    def _save_snippet(self) -> None:
        messagebox = self._messagebox
        payload = self._payload()
        if not payload["trigger"]:
            messagebox.showerror("Expando", "Il trigger non può essere vuoto.")
            return
        if self._current_id and self._selected_item() and self._selected_item().get("editable", "1") != "1":
            messagebox.showerror("Expando", "Questo snippet non è modificabile dall'editor.")
            return
        handler = self.on_save if self._current_id else self.on_create
        error = handler(payload)
        if error:
            messagebox.showerror("Expando", error)
            return
        self.result = {"saved": "1"}
        self.status_var.set("Salvato. Ricarico la lista…")
        self.items[:] = self._reload_items()
        self._refresh_list()

    def _delete_snippet(self) -> None:
        messagebox = self._messagebox
        if not self._current_id:
            messagebox.showinfo("Expando", "Seleziona uno snippet da eliminare.")
            return
        if self._selected_item() and self._selected_item().get("editable", "1") != "1":
            messagebox.showerror("Expando", "I package hub non possono essere eliminati da qui.")
            return
        if not messagebox.askyesno("Expando", "Eliminare questo snippet?"):
            return
        error = self.on_delete(self._current_id)
        if error:
            messagebox.showerror("Expando", error)
            return
        self.result = {"deleted": "1"}
        self.items[:] = self._reload_items()
        self._refresh_list()

    def _reload_items(self) -> list[dict[str, str]]:
        return self.items

    def set_reload(self, loader: Callable[[], list[dict[str, str]]]) -> None:
        self._reload_items = loader

    def _close(self) -> None:
        self.root.destroy()

    def run(self) -> dict[str, str] | None:
        self.root.mainloop()
        return self.result


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
) -> dict[str, str] | None:
    if _use_appkit():
        # AppKit native editor (preferred on Darwin unless EXPANDO_UI=tk)
        from .snippet_editor_appkit import run_snippet_editor as appkit_editor

        return appkit_editor(
            items,
            on_save=on_save,
            on_create=on_create,
            on_delete=on_delete,
            on_duplicate=on_duplicate,
            on_move=on_move,
            reload_items=reload_items,
            match_files=match_files,
            config_dir=config_dir,
        )
    editor = SnippetEditor(
        items,
        on_save=on_save,
        on_create=on_create,
        on_delete=on_delete,
    )
    editor.set_reload(reload_items)
    return editor.run()
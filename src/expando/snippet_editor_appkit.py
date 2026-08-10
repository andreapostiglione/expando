"""Snippet editor entry — opens the unified Expando Studio.

Kept as module name for backward compatibility with tests and imports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .studio_appkit import SECTION_COLLECTIONS, SECTION_SNIPPETS, run_expando_studio


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
    initial_section: str = SECTION_SNIPPETS,
    collection_items: list[dict[str, str]] | None = None,
    reload_collections: Callable[[], list[dict[str, str]]] | None = None,
    on_install_package: Callable[[str], str | None] | None = None,
) -> dict[str, str] | None:
    """Open the unified Studio window (snippets + collections)."""
    return run_expando_studio(
        items,
        on_save=on_save,
        on_create=on_create,
        on_delete=on_delete,
        on_duplicate=on_duplicate,
        on_move=on_move,
        reload_snippets=reload_items,
        match_files=match_files,
        config_dir=config_dir,
        initial_new=initial_new,
        initial_section=initial_section,
        collection_items=collection_items,
        reload_collections=reload_collections,
        on_install_package=on_install_package,
    )

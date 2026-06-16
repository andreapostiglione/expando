from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .listener import KeyboardService

try:
    import rumps
except ImportError:  # pragma: no cover - optional on non-macOS dev envs
    rumps = None


def menubar_available() -> bool:
    return rumps is not None


def run_with_menubar(config_dir: Path, service: KeyboardService) -> None:
    if rumps is None:
        raise RuntimeError("rumps is not installed")

    class ExpandoMenuBar(rumps.App):
        def __init__(self) -> None:
            super().__init__("Expando", quit_button=None)
            self.config_dir = config_dir
            self.service = service
            self.enabled_item = rumps.MenuItem("Disable", callback=self.toggle_enabled)
            self.menu = [
                self.enabled_item,
                rumps.MenuItem("Search snippets", callback=self.search_snippets),
                rumps.MenuItem("Edit snippets", callback=self.edit_snippets),
                rumps.MenuItem("Restart", callback=self.restart_service),
                None,
                rumps.MenuItem("Quit", callback=self.quit_app),
            ]
            self._sync_enabled_label()
            service.on_toggle = self._sync_enabled_label
            service.start()

        def _sync_enabled_label(self, *_args) -> None:
            enabled = self.service.engine.enabled
            self.enabled_item.title = "Disable" if enabled else "Enable"
            self.title = "Expando ●" if enabled else "Expando ○"

        def toggle_enabled(self, _sender) -> None:
            self.service.engine.toggle_enabled()
            self.service.notify_toggle()
            self._sync_enabled_label()

        def search_snippets(self, _sender) -> None:
            threading.Thread(target=self.service.open_search, daemon=True).start()

        def edit_snippets(self, _sender) -> None:
            target = self.config_dir / "match" / "base.yml"
            editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
            subprocess.Popen([editor, str(target)])

        def restart_service(self, _sender) -> None:
            self.service.apply_config_reload()
            rumps.notification("Expando", "", "Service restarted")

        def quit_app(self, _sender) -> None:
            self.service.stop()
            rumps.quit_application()

    ExpandoMenuBar().run()
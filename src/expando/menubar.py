from __future__ import annotations

import os
import subprocess
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
            self.enabled_item = rumps.MenuItem("Disattiva", callback=self.toggle_enabled)
            self.menu = [
                self.enabled_item,
                rumps.MenuItem("Modifica snippet", callback=self.edit_snippets),
                rumps.MenuItem("Riavvia", callback=self.restart_service),
                None,
                rumps.MenuItem("Esci", callback=self.quit_app),
            ]
            self._sync_enabled_label()
            service.on_toggle = self._sync_enabled_label
            service.start()

        def _sync_enabled_label(self, *_args) -> None:
            enabled = self.service.engine.enabled
            self.enabled_item.title = "Disattiva" if enabled else "Attiva"
            self.title = "Expando ●" if enabled else "Expando ○"

        def toggle_enabled(self, _sender) -> None:
            self.service.engine.toggle_enabled()
            self.service.notify_toggle()
            self._sync_enabled_label()

        def edit_snippets(self, _sender) -> None:
            target = self.config_dir / "match" / "base.yml"
            editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
            subprocess.Popen([editor, str(target)])

        def restart_service(self, _sender) -> None:
            from .config import load_config

            self.service.stop()
            self.service.engine.reload(load_config(self.config_dir))
            self.service.start()
            rumps.notification("Expando", "", "Servizio riavviato")

        def quit_app(self, _sender) -> None:
            self.service.stop()
            rumps.quit_application()

    ExpandoMenuBar().run()
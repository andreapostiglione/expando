from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from .i18n import t, tf

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
            self.enabled_item = rumps.MenuItem(t("menubar.disable"), callback=self.toggle_enabled)
            self.menu = [
                self.enabled_item,
                rumps.MenuItem(t("menubar.search"), callback=self.search_snippets),
                rumps.MenuItem(t("menubar.hub"), callback=self.browse_packages),
                rumps.MenuItem(t("menubar.editor"), callback=self.edit_snippets),
                rumps.MenuItem(t("menubar.restart"), callback=self.restart_service),
                rumps.MenuItem(t("menubar.updates"), callback=self.check_updates),
                None,
                rumps.MenuItem(t("menubar.quit"), callback=self.quit_app),
            ]
            self._sync_enabled_label()
            service.on_toggle = self._sync_enabled_label
            service.start()
            threading.Thread(target=self._startup_tasks, daemon=True).start()

        def _sync_enabled_label(self, *_args) -> None:
            enabled = self.service.engine.enabled
            self.enabled_item.title = t("menubar.disable") if enabled else t("menubar.enable")
            self.title = "Expando ●" if enabled else "Expando ○"

        def toggle_enabled(self, _sender) -> None:
            self.service.engine.toggle_enabled()
            self.service.notify_toggle()
            self._sync_enabled_label()

        def search_snippets(self, _sender) -> None:
            threading.Thread(target=self.service.open_search, daemon=True).start()

        def browse_packages(self, _sender) -> None:
            threading.Thread(target=self._browse_packages, daemon=True).start()

        def _browse_packages(self) -> None:
            from .hub import hub_packages_for_picker, install_hub_package
            from .ui_bridge import show_search_picker

            picked = show_search_picker(hub_packages_for_picker(self.config_dir))
            if not picked or picked.get("installed") == "1":
                return
            package_id = picked.get("package_id") or picked.get("trigger")
            if not package_id:
                return
            try:
                install_hub_package(self.config_dir, str(package_id))
                rumps.notification(
                    "Expando",
                    "",
                    tf("menubar.installed", package=package_id),
                )
            except Exception as exc:
                rumps.notification(
                    "Expando",
                    "",
                    tf("menubar.install_failed", error=exc),
                )

        def edit_snippets(self, _sender) -> None:
            threading.Thread(target=self._open_snippet_editor, daemon=True).start()

        def _open_snippet_editor(self) -> None:
            from .ui_bridge import show_snippet_editor

            show_snippet_editor(str(self.config_dir))
            self.service.apply_config_reload()

        def restart_service(self, _sender) -> None:
            self.service.apply_config_reload()
            rumps.notification("Expando", "", t("menubar.restarted"))

        def _startup_tasks(self) -> None:
            from .changelog import maybe_show_whats_new
            from .updater import check_for_updates_silent

            maybe_show_whats_new(self.config_dir)
            check_for_updates_silent(self.config_dir)

        def check_updates(self, _sender) -> None:
            threading.Thread(target=self._check_updates, daemon=True).start()

        def _check_updates(self) -> None:
            from .config import load_config
            from .updater import _notify_update_available, check_for_updates

            config = load_config(self.config_dir)
            result = check_for_updates(
                self.config_dir,
                feed_url=config.app.update_feed_url or None,
                force=True,
                notify_user=False,
            )
            if result.error:
                rumps.notification(
                    "Expando",
                    "",
                    tf("menubar.update_failed", error=result.error),
                )
            elif result.available:
                _notify_update_available(result.available, open_download=True)
            else:
                rumps.notification("Expando", "", t("menubar.up_to_date"))

        def quit_app(self, _sender) -> None:
            self.service.stop()
            rumps.quit_application()

    ExpandoMenuBar().run()
from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from .brand_assets import brand_asset_path
from .i18n import t, tf
from .ui_state import set_ui_active

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
            icon = brand_asset_path("menubar-icon.png")
            super().__init__(
                "Expando",
                icon=str(icon) if icon else None,
                quit_button=None,
            )
            self.config_dir = config_dir
            self.service = service
            self.enabled_item = rumps.MenuItem(t("menubar.disable"), callback=self.toggle_enabled)
            self.menu = [
                self.enabled_item,
                rumps.MenuItem(t("menubar.search"), callback=self.search_snippets),
                rumps.MenuItem(t("menubar.hub"), callback=self.browse_packages),
                rumps.MenuItem(t("menubar.editor"), callback=self.edit_snippets),
                rumps.MenuItem(t("menubar.backup"), callback=self.backup_config),
                rumps.MenuItem(t("menubar.restore"), callback=self.restore_config),
                rumps.MenuItem(t("menubar.restart"), callback=self.restart_service),
                rumps.MenuItem(t("menubar.updates"), callback=self.check_updates),
                None,
                rumps.MenuItem(t("menubar.quit"), callback=self.quit_app),
            ]
            self._sync_enabled_label()
            service.on_toggle = self._sync_enabled_label
            service.on_listener_dead = self._on_listener_dead
            service.on_listener_recovered = self._sync_enabled_label
            service.start()
            threading.Thread(target=self._startup_tasks, daemon=True).start()

        def _hub_updates(self) -> int:
            try:
                from .hub import hub_update_count

                return hub_update_count(self.config_dir)
            except Exception:
                return 0

        def _sync_enabled_label(self, *_args) -> None:
            enabled = self.service.engine.enabled
            self.enabled_item.title = t("menubar.disable") if enabled else t("menubar.enable")
            hub_updates = self._hub_updates()
            if self.service.listener_dead():
                self.title = t("menubar.title_listener_dead")
            elif hub_updates > 0:
                self.title = tf("menubar.title_hub_updates", count=hub_updates)
            elif enabled:
                self.title = t("menubar.title_enabled")
            else:
                self.title = t("menubar.title_disabled")

        def _on_listener_dead(self) -> None:
            self._sync_enabled_label()
            rumps.notification("Expando", "", t("menubar.listener_dead"))

        def toggle_enabled(self, _sender) -> None:
            self.service.engine.toggle_enabled()
            self.service.notify_toggle()
            self._sync_enabled_label()

        def search_snippets(self, _sender) -> None:
            try:
                self.service.open_search()
            except Exception as exc:
                self._notify_action_failed("search", exc)
            finally:
                set_ui_active(False)

        def browse_packages(self, _sender) -> None:
            try:
                self._browse_packages()
            except Exception as exc:
                self._notify_action_failed("hub", exc)
            finally:
                set_ui_active(False)

        def _browse_packages(self) -> None:
            from .hub import hub_packages_for_picker, install_hub_package
            from .ui_bridge import show_search_picker

            picked = show_search_picker(hub_packages_for_picker(self.config_dir))
            if not picked:
                return
            if picked.get("installed") == "1":
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
                self._sync_enabled_label()
            except Exception as exc:
                rumps.notification(
                    "Expando",
                    "",
                    tf("menubar.install_failed", error=exc),
                )

        def edit_snippets(self, _sender) -> None:
            try:
                self._open_snippet_editor()
            except Exception as exc:
                self._notify_action_failed("editor", exc)
            finally:
                set_ui_active(False)

        def _open_snippet_editor(self) -> None:
            from .ui_bridge import show_snippet_editor

            result = show_snippet_editor(str(self.config_dir))
            if result is None:
                rumps.notification("Expando", "", t("menubar.ui_failed"))
                return
            self.service.apply_config_reload()

        def _notify_action_failed(self, action: str, exc: Exception) -> None:
            rumps.notification(
                "Expando",
                "",
                tf("menubar.action_failed", action=action, error=exc),
            )

        def backup_config(self, _sender) -> None:
            threading.Thread(target=self._backup_config, daemon=True).start()

        def _backup_config(self) -> None:
            from .backup import backup_config

            try:
                archive = backup_config(self.config_dir)
                rumps.notification("Expando", "", tf("menubar.backup_created", path=archive))
            except Exception as exc:
                rumps.notification("Expando", "", tf("menubar.backup_failed", error=exc))

        def restore_config(self, _sender) -> None:
            threading.Thread(target=self._restore_config, daemon=True).start()

        def _restore_config(self) -> None:
            from .backup import restore_config

            backups = sorted(
                self.config_dir.parent.glob("expando-backup-*.tar.gz"),
                reverse=True,
            )
            if not backups:
                rumps.notification("Expando", "", t("menubar.no_backups"))
                return
            latest = backups[0]
            try:
                restore_config(self.config_dir, latest)
                self.service.apply_config_reload()
                rumps.notification("Expando", "", tf("menubar.restored", path=latest))
            except Exception as exc:
                rumps.notification("Expando", "", tf("menubar.restore_failed", error=exc))

        def restart_service(self, _sender) -> None:
            threading.Thread(target=self._restart_service, daemon=True).start()

        def _restart_service(self) -> None:
            from .daemon import restart_foreground_daemon

            try:
                restart_foreground_daemon(self.config_dir)
            except Exception as exc:
                rumps.notification("Expando", "", tf("menubar.restart_failed", error=exc))

        def _startup_tasks(self) -> None:
            from .changelog import maybe_show_whats_new
            from .updater import check_for_updates_silent

            maybe_show_whats_new(self.config_dir)
            check_for_updates_silent(self.config_dir)
            self._sync_enabled_label()

        def check_updates(self, _sender) -> None:
            threading.Thread(target=self._check_updates, daemon=True).start()

        def _check_updates(self) -> None:
            from .config import load_config
            from .sparkle_native import (
                check_for_updates_via_sparkle,
                sparkle_update_mode,
            )
            from .updater import _notify_update_available, check_for_updates

            mode = sparkle_update_mode()
            if mode == "native":
                check_for_updates_via_sparkle(background=False)
                return

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
            elif mode == "manual_required":
                rumps.notification("Expando", "", t("menubar.update_manual_required"))
            else:
                rumps.notification("Expando", "", t("menubar.up_to_date"))

        def quit_app(self, _sender) -> None:
            self.service.stop()
            rumps.quit_application()

    ExpandoMenuBar().run()
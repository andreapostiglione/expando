from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from .brand_assets import load_menubar_nsimage, menubar_template_icon
from .i18n import t, tf
from .menubar_feedback import backup_label, user_confirm, user_error, user_info, user_success
from .ui_state import set_ui_active

logger = logging.getLogger(__name__)

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
            icon = menubar_template_icon()
            super().__init__(
                "Expando",
                icon=str(icon) if icon else None,
                template=True if icon else None,
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
            set_ui_active(False)
            threading.Thread(target=self._startup_tasks, daemon=True).start()

        def run(self, **options):
            image = load_menubar_nsimage()
            if image is not None:
                self._icon_nsimage = image
            super().run(**options)

        def _hub_updates(self) -> int:
            try:
                from .hub import hub_update_count

                return hub_update_count(self.config_dir)
            except Exception:
                return 0

        def _sync_enabled_label(self, *_args) -> None:
            def _apply() -> None:
                enabled = self.service.engine.enabled
                self.enabled_item.title = t("menubar.disable") if enabled else t("menubar.enable")
                hub_updates = self._hub_updates()
                if self.service.listener_dead():
                    self.title = "⚠"
                elif hub_updates > 0:
                    self.title = f"↑{hub_updates}"
                elif not enabled:
                    self.title = "○"
                else:
                    self.title = None

            try:
                from .ui_main_thread import call_on_main_thread

                call_on_main_thread(_apply, wait=False)
            except Exception:
                logger.debug("Menubar label sync skipped", exc_info=True)

        def _on_listener_dead(self) -> None:
            self._sync_enabled_label()
            user_info(t("menubar.listener_dead"))

        def toggle_enabled(self, _sender) -> None:
            self.service.engine.toggle_enabled()
            self.service.notify_toggle()
            self._sync_enabled_label()

        def search_snippets(self, _sender) -> None:
            try:
                self.service.open_search()
            except Exception as exc:
                self._notify_action_failed(exc)
            finally:
                set_ui_active(False)

        def browse_packages(self, _sender) -> None:
            try:
                self._browse_packages()
            except Exception as exc:
                self._notify_action_failed(exc)
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
                user_success(tf("menubar.installed", package=package_id))
                self._sync_enabled_label()
            except Exception as exc:
                user_error(tf("menubar.install_failed", error=exc))

        def edit_snippets(self, _sender) -> None:
            try:
                self._open_snippet_editor()
            except Exception as exc:
                self._notify_action_failed(exc)
            finally:
                set_ui_active(False)

        def _open_snippet_editor(self) -> None:
            from .config_reload_gate import ConfigReloadError
            from .ui_bridge import show_snippet_editor

            result = show_snippet_editor(str(self.config_dir))
            if result is None:
                user_error(t("menubar.ui_failed"))
                return
            try:
                self.service.apply_config_reload()
            except ConfigReloadError as exc:
                if exc.rolled_back:
                    user_error(t("menubar.restore_invalid_rolled_back"))
                    return
                raise

        def _notify_action_failed(self, exc: Exception) -> None:
            logger.exception("Menubar action failed")
            user_error(tf("menubar.action_failed", error=exc))

        def backup_config(self, _sender) -> None:
            from .backup import backup_config

            try:
                archive = backup_config(self.config_dir)
                logger.info("Manual backup created: %s", archive)
                user_success(
                    tf("menubar.backup_saved", label=backup_label(archive)),
                    reveal=archive,
                )
            except Exception as exc:
                logger.exception("Backup failed")
                user_error(tf("menubar.backup_failed", error=exc))

        def restore_config(self, _sender) -> None:
            from .backup import backups_for_picker, restore_config
            from .config_reload_gate import ConfigReloadError
            from .ui_bridge import show_search_picker

            items = backups_for_picker(self.config_dir)
            if not items:
                user_info(t("menubar.no_backups"))
                return

            picked = show_search_picker(items)
            if not picked:
                return

            archive = Path(picked.get("archive_path", ""))
            if not archive.is_file():
                user_error(t("menubar.no_backups"))
                return

            label = backup_label(archive)
            if not user_confirm(
                t("menubar.restore_confirm_title"),
                tf("menubar.restore_confirm_body", label=label),
            ):
                return

            try:
                restore_config(self.config_dir, archive)
                try:
                    self.service.apply_config_reload()
                except ConfigReloadError as exc:
                    if exc.rolled_back:
                        user_error(t("menubar.restore_invalid_rolled_back"))
                        return
                    raise
                logger.info("Restored config from %s", archive)
                user_success(tf("menubar.restored_ok", label=label))
            except ConfigReloadError:
                raise
            except Exception as exc:
                logger.exception("Restore failed")
                user_error(tf("menubar.restore_failed", error=exc))
            finally:
                set_ui_active(False)

        def restart_service(self, _sender) -> None:
            try:
                self._restart_service()
            except Exception as exc:
                user_error(tf("menubar.restart_failed", error=exc))

        def _restart_service(self) -> None:
            import os

            from .daemon import restart_foreground_daemon

            logger.info("Menu bar restart requested")
            self.service.stop()
            try:
                restart_foreground_daemon(self.config_dir, wait_for_pid=os.getpid())
            except Exception:
                self.service.start()
                raise
            rumps.quit_application()

        def _startup_tasks(self) -> None:
            from .changelog import maybe_show_whats_new
            from .updater import check_for_updates_silent

            maybe_show_whats_new(self.config_dir)
            check_for_updates_silent(self.config_dir)
            self._sync_enabled_label()

        def check_updates(self, _sender) -> None:
            try:
                self._check_updates()
            except Exception as exc:
                self._notify_action_failed(exc)

        def _check_updates(self) -> None:
            from .config import load_config
            from .sparkle_native import (
                check_for_updates_via_sparkle,
                sparkle_update_mode,
            )
            from .updater import check_for_updates, open_download_url

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
                user_error(tf("menubar.update_failed", error=result.error))
            elif result.available:
                message = t("update.available").format(version=result.available.version)
                user_info(message)
                open_download_url(result.available.download_url)
            elif mode == "manual_required":
                user_info(t("menubar.update_manual_required"))
            else:
                user_info(t("menubar.up_to_date"))

        def quit_app(self, _sender) -> None:
            self.service.stop()
            rumps.quit_application()

    ExpandoMenuBar().run()
from pathlib import Path
from unittest.mock import MagicMock, patch

from expando.notifications import notify_toggle, reveal_in_finder, show_info_alert


def test_notify_toggle_enabled():
    with patch("expando.notifications.subprocess.run") as run:
        with patch("expando.i18n.t", return_value="Text expansion enabled"):
            notify_toggle(True)
        run.assert_called_once()
        assert "enabled" in run.call_args.args[0][2]


def test_show_info_alert_schedules_on_main_thread():
    with patch("expando.notifications.platform.system", return_value="Darwin"):
        with patch("expando.ui_main_thread.call_on_main_thread") as call:
            show_info_alert("Expando", "Backup creato")

    call.assert_called_once()
    assert call.call_args.args[0].__name__ == "_show"


def test_reveal_in_finder_opens_path():
    path = Path("/tmp/expando-backup.tar.gz")
    with patch("expando.notifications.platform.system", return_value="Darwin"):
        with patch("expando.notifications.subprocess.run") as run:
            reveal_in_finder(path)
    run.assert_called_once_with(["open", "-R", str(path)], check=False)
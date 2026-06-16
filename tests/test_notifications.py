from unittest.mock import patch

from expando.notifications import notify_toggle


def test_notify_toggle_enabled():
    with patch("expando.notifications.subprocess.run") as run:
        notify_toggle(True)
        run.assert_called_once()
        assert "enabled" in run.call_args.args[0][2]
from __future__ import annotations

from unittest.mock import MagicMock, patch

from expando.app_context import capture_frontmost_application_pid, restore_frontmost_application


def test_capture_frontmost_application_pid_skips_self(monkeypatch) -> None:
    monkeypatch.setattr("expando.app_context.platform.system", lambda: "Darwin")
    monkeypatch.setattr("os.getpid", lambda: 42)

    front_app = MagicMock()
    front_app.processIdentifier.return_value = 42

    workspace = MagicMock()
    workspace.frontmostApplication.return_value = front_app

    with patch("AppKit.NSWorkspace", create=True) as ns_workspace:
        ns_workspace.sharedWorkspace.return_value = workspace
        assert capture_frontmost_application_pid() is None


def test_restore_frontmost_application_noop_without_pid() -> None:
    assert restore_frontmost_application(None) is False
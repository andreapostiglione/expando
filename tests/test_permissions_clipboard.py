from __future__ import annotations

from unittest.mock import call, patch


def test_check_clipboard_restores_previous_contents() -> None:
    from expando.permissions import _check_clipboard_macos

    with patch("expando.permissions.subprocess.run") as run:
        run.side_effect = [
            type("R", (), {"stdout": "user clipboard text", "returncode": 0})(),
            None,
            type("R", (), {"stdout": "expando-clipboard-probe", "returncode": 0})(),
            None,
        ]

        assert _check_clipboard_macos() is True

        assert run.call_args_list[0] == call(
            ["pbpaste"], capture_output=True, text=True, timeout=2, check=True
        )
        assert run.call_args_list[1] == call(
            ["pbcopy"], input="expando-clipboard-probe", text=True, check=True, timeout=2
        )
        assert run.call_args_list[-1] == call(
            ["pbcopy"], input="user clipboard text", text=True, check=True, timeout=2
        )


def test_check_permissions_skips_clipboard_probe_by_default() -> None:
    from expando.permissions import check_permissions

    with patch("expando.permissions._check_clipboard_macos") as clipboard_check:
        with patch("expando.permissions.platform.system", return_value="Darwin"):
            check_permissions()

    clipboard_check.assert_not_called()


def test_check_permissions_runs_clipboard_probe_for_doctor() -> None:
    from expando.permissions import check_permissions

    with patch("expando.permissions._check_clipboard_macos", return_value=True) as clipboard_check:
        with patch("expando.permissions.platform.system", return_value="Darwin"):
            status = check_permissions(include_clipboard=True)

    clipboard_check.assert_called_once()
    assert status.clipboard is True


def test_packaged_runtime_notes_only_when_permissions_need_attention() -> None:
    from expando.permissions import check_permissions
    from expando.runtime_info import RuntimeInfo

    runtime = RuntimeInfo(
        mode="packaged",
        executable="/opt/homebrew/bin/python3.12",
        grant_label="python3.12",
        grant_hint="/Applications/Expando.app",
    )

    with patch("expando.permissions.platform.system", return_value="Darwin"):
        with patch("expando.permissions.detect_runtime", return_value=runtime):
            with patch("expando.permissions._check_accessibility_macos", return_value=True):
                with patch("expando.permissions._check_input_monitoring_macos", return_value=True):
                    ready = check_permissions()
                with patch("expando.permissions._check_input_monitoring_macos", return_value=False):
                    needs_attention = check_permissions()

    assert not any("Installazione legacy" in note for note in ready.notes)
    assert any("Installazione legacy" in note for note in needs_attention.notes)

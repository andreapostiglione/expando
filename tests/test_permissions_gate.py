from __future__ import annotations

from expando.permissions import PermissionStatus, _injection_ready, permissions_ready


def test_permissions_ready_requires_accessibility():
    status = PermissionStatus(
        accessibility=False,
        input_monitoring=True,
        notes=[],
        injection_ready=False,
    )
    assert permissions_ready(status) is False

    status.accessibility = True
    assert permissions_ready(status) is True


def test_permissions_ready_blocks_false_input_monitoring():
    status = PermissionStatus(
        accessibility=True,
        input_monitoring=False,
        notes=[],
        injection_ready=False,
    )
    assert permissions_ready(status) is False


def test_permissions_ready_allows_unknown_input_monitoring():
    status = PermissionStatus(
        accessibility=True,
        input_monitoring=None,
        notes=[],
        injection_ready=True,
    )
    assert permissions_ready(status) is True


def test_injection_ready_considers_accessibility_and_input_monitoring():
    assert _injection_ready(True, True) is True
    assert _injection_ready(True, None) is True
    assert _injection_ready(True, False) is False
    assert _injection_ready(False, True) is False
    assert _injection_ready(None, None) is None
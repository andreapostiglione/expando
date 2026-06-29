from __future__ import annotations

from unittest.mock import patch

from expando.permissions import (
    PermissionStatus,
    _TCCRow,
    _check_accessibility_macos,
    _check_input_monitoring_macos,
    _client_matches_runtime,
    _injection_ready,
    permissions_ready,
)
from expando.runtime_info import RuntimeInfo


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


def test_tcc_runtime_matching_does_not_cross_python_versions():
    runtime = RuntimeInfo(
        mode="packaged",
        executable=(
            "/opt/homebrew/Cellar/python@3.12/3.12.13_4/Frameworks/"
            "Python.framework/Versions/3.12/bin/python3.12"
        ),
        grant_label="python3.12",
        grant_hint="/Applications/Expando.app",
    )

    assert _client_matches_runtime(runtime.executable, runtime) is True
    assert _client_matches_runtime(
        "/opt/homebrew/Cellar/python@3.14/3.14.5/Frameworks/"
        "Python.framework/Versions/3.14/bin/python3.14",
        runtime,
    ) is False
    assert _client_matches_runtime("python3.14", runtime) is False


def test_input_monitoring_rejects_permission_for_other_python_version():
    runtime = RuntimeInfo(
        mode="packaged",
        executable=(
            "/opt/homebrew/Cellar/python@3.12/3.12.13_4/Frameworks/"
            "Python.framework/Versions/3.12/bin/python3.12"
        ),
        grant_label="python3.12",
        grant_hint="/Applications/Expando.app",
    )
    rows = [
        _TCCRow(
            client=(
                "/opt/homebrew/Cellar/python@3.14/3.14.5/Frameworks/"
                "Python.framework/Versions/3.14/bin/python3.14"
            ),
            client_type=1,
            auth_value=2,
            last_modified=1,
        )
    ]

    with patch("expando.permissions.platform.system", return_value="Darwin"):
        with patch("expando.permissions._query_tcc", return_value=rows):
            assert _check_input_monitoring_macos(runtime) is False


def test_accessibility_prefers_tcc_deny_for_current_runtime():
    runtime = RuntimeInfo(
        mode="packaged",
        executable=(
            "/opt/homebrew/Cellar/python@3.12/3.12.13_4/Frameworks/"
            "Python.framework/Versions/3.12/bin/python3.12"
        ),
        grant_label="python3.12",
        grant_hint="/Applications/Expando.app",
    )
    rows = [
        _TCCRow(
            client=runtime.executable,
            client_type=1,
            auth_value=0,
            last_modified=1,
        )
    ]

    with patch("expando.permissions.platform.system", return_value="Darwin"):
        with patch("expando.permissions._query_tcc", return_value=rows):
            with patch(
                "expando.permissions._check_accessibility_pyobjc",
                return_value=True,
            ):
                assert _check_accessibility_macos(runtime=runtime) is False

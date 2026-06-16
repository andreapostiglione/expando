from unittest.mock import patch

from expando.secure_input import is_secure_input_active


def test_secure_input_detects_password_field():
    with patch("expando.secure_input.platform.system", return_value="Darwin"), patch(
        "expando.secure_input.subprocess.run",
        return_value=type(
            "Result",
            (),
            {"returncode": 0, "stdout": "AXTextField\nAXSecureTextField"},
        )(),
    ):
        assert is_secure_input_active() is True


def test_secure_input_non_macos():
    with patch("expando.secure_input.platform.system", return_value="Linux"):
        assert is_secure_input_active() is False
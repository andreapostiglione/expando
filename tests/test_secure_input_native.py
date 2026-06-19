from unittest.mock import patch

from expando.secure_input import _probe_secure_input_active, is_secure_input_active


def test_secure_input_combines_native_and_ax():
    with patch("expando.secure_input._probe_secure_input_native", return_value=True):
        assert _probe_secure_input_active() is True
    with patch("expando.secure_input._probe_secure_input_native", return_value=False):
        with patch("expando.secure_input._probe_secure_input_ax", return_value=True):
            assert _probe_secure_input_active() is True
    with patch("expando.secure_input._probe_secure_input_native", return_value=None):
        with patch("expando.secure_input._probe_secure_input_ax", return_value=False):
            assert _probe_secure_input_active() is False


def test_is_secure_input_non_darwin(monkeypatch):
    monkeypatch.setattr("expando.secure_input.platform.system", lambda: "Linux")
    assert is_secure_input_active() is False
from unittest.mock import patch

from expando.secure_input import _probe_secure_input_active, is_secure_input_active


def test_secure_input_prefers_native_and_skips_ax_when_false():
    with patch("expando.secure_input._probe_secure_input_native", return_value=True):
        with patch("expando.secure_input._probe_secure_input_ax") as ax:
            assert _probe_secure_input_active() is True
            ax.assert_not_called()
    with patch("expando.secure_input._probe_secure_input_native", return_value=False):
        with patch("expando.secure_input._probe_secure_input_ax") as ax:
            assert _probe_secure_input_active() is False
            ax.assert_not_called()
    with patch("expando.secure_input._probe_secure_input_native", return_value=None):
        with patch("expando.secure_input._probe_secure_input_ax", return_value=False):
            assert _probe_secure_input_active() is False
    with patch("expando.secure_input._probe_secure_input_native", return_value=None):
        with patch("expando.secure_input._probe_secure_input_ax", return_value=True):
            assert _probe_secure_input_active() is True


def test_is_secure_input_non_darwin(monkeypatch):
    monkeypatch.setattr("expando.secure_input.platform.system", lambda: "Linux")
    assert is_secure_input_active() is False
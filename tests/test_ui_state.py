import time

from expando.ui_state import clear_ui_active, is_ui_active, set_ui_active


def test_ui_state_toggle():
    set_ui_active(False)
    assert is_ui_active() is False
    set_ui_active(True)
    assert is_ui_active() is True
    set_ui_active(False)
    assert is_ui_active() is False


def test_ui_state_auto_clears_after_timeout(monkeypatch):
    import expando.ui_state as ui_state

    monkeypatch.setattr(ui_state, "_UI_ACTIVE_TIMEOUT_SECONDS", 0.05)
    set_ui_active(True)
    assert is_ui_active() is True
    time.sleep(0.06)
    assert is_ui_active() is False


def test_clear_ui_active():
    set_ui_active(True)
    clear_ui_active()
    assert is_ui_active() is False
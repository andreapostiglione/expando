from expando.ui_state import is_ui_active, set_ui_active


def test_ui_state_toggle():
    set_ui_active(False)
    assert is_ui_active() is False
    set_ui_active(True)
    assert is_ui_active() is True
    set_ui_active(False)
    assert is_ui_active() is False
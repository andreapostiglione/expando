from __future__ import annotations

import platform
import time

import pytest

from expando.injector import InjectorSettings, TextInjector
from expando.listener import build_service

from tests.e2e.helpers import get_textedit_content, type_text_via_subprocess

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")]


@pytest.mark.integration
def test_textinjector_types_into_textedit(require_live_injection_e2e, textedit_document):
    injector = TextInjector(InjectorSettings(backend="inject", clipboard_threshold=9999))
    payload = "hello expando typing"
    injector.inject(payload)
    time.sleep(0.5)
    content = get_textedit_content()
    assert payload in content, content


@pytest.mark.clipboard
def test_textinjector_clipboard_paste_into_textedit(require_clipboard_e2e, textedit_document):
    injector = TextInjector(InjectorSettings(backend="clipboard"))
    injector.inject("hello e2e clipboard")
    time.sleep(0.8)
    content = get_textedit_content()
    assert "hello e2e clipboard" in content, content


@pytest.mark.integration
def test_global_listener_captures_keystrokes(
    require_full_e2e,
    require_live_injection_e2e,
    textedit_document,
    e2e_config_dir,
):
    """Verifies the OS-wide pynput listener; needs Input Monitoring permission."""
    service = build_service(e2e_config_dir)
    events: list[object] = []
    original_release = service._on_release

    def traced_release(key) -> None:
        events.append(key)
        original_release(key)

    service._on_release = traced_release  # type: ignore[method-assign]
    service.start()
    try:
        type_text_via_subprocess("ab")
        time.sleep(0.8)
        if not events:
            pytest.skip(
                "Global keyboard listener received no events — grant Input Monitoring to "
                "Terminal/Python in System Settings → Privacy & Security → Input Monitoring"
            )
    finally:
        service.stop()
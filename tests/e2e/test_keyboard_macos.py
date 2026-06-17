from __future__ import annotations

import platform
import time

import pytest

from expando.injector import InjectorSettings, TextInjector
from expando.listener import build_service

from tests.e2e.helpers import (
    close_textedit_documents,
    get_textedit_content,
    open_textedit_blank,
    type_text_via_subprocess,
)

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")]


def test_textinjector_types_into_textedit(require_accessibility):
    open_textedit_blank()
    try:
        injector = TextInjector(InjectorSettings(backend="inject", clipboard_threshold=9999))
        injector.inject("hello e2e typing")
        time.sleep(0.5)
        content = get_textedit_content()
        assert "hello e2e typing" in content, content
    finally:
        close_textedit_documents()


def test_textinjector_clipboard_paste_into_textedit(require_accessibility):
    open_textedit_blank()
    try:
        injector = TextInjector(InjectorSettings(backend="clipboard"))
        injector.inject("hello e2e clipboard")
        time.sleep(0.6)
        content = get_textedit_content()
        assert "hello e2e clipboard" in content, content
    finally:
        close_textedit_documents()


def test_global_listener_captures_keystrokes(require_accessibility, e2e_config_dir):
    """Full OS listener path; requires Input Monitoring in addition to Accessibility."""
    open_textedit_blank()
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
        type_text_via_subprocess(":e2e")
        time.sleep(1.0)
        content = get_textedit_content()
        assert "Expanded E2E text" in content, content
    finally:
        service.stop()
        close_textedit_documents()
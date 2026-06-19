from __future__ import annotations

import platform
import time

import pytest

from expando.engine import build_engine
from expando.listener import build_service

from tests.e2e.helpers import get_textedit_content, type_text_via_subprocess

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only"),
]


@pytest.mark.integration
def test_secure_input_blocks_expansion(require_full_e2e, textedit_document, e2e_config_dir, monkeypatch):
    """Expansion must not run while secure input is active."""
    monkeypatch.setattr("expando.secure_input.is_secure_input_active", lambda: True)

    service = build_service(e2e_config_dir)
    service.start()
    try:
        type_text_via_subprocess(":e2e")
        time.sleep(0.8)
        content = get_textedit_content()
        assert "Expanded E2E text" not in content
        assert ":e2e" in content
    finally:
        service.stop()


def test_engine_respects_secure_input_flag(e2e_config_dir, monkeypatch):
    monkeypatch.setattr("expando.secure_input.is_secure_input_active", lambda: True)
    engine = build_engine(e2e_config_dir)
    assert engine.handle_char("e") is False
    assert engine.handle_char("2") is False
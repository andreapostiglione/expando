from __future__ import annotations

import platform
import time
from unittest.mock import patch

import pytest

from expando.app_context import AppContext
from expando.engine import build_engine
from expando.listener import build_service

from tests.e2e.helpers import get_textedit_content, type_text_via_subprocess

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only"),
]


def _enable_secure_input_respect(config_dir) -> None:
    config_file = config_dir / "config" / "default.yml"
    text = config_file.read_text(encoding="utf-8")
    assert "respect_secure_input: false" in text
    config_file.write_text(
        text.replace("respect_secure_input: false", "respect_secure_input: true"),
        encoding="utf-8",
    )


@pytest.mark.integration
def test_secure_input_blocks_expansion(require_full_e2e, textedit_document, e2e_config_dir, monkeypatch):
    """Expansion must not run while secure input is active."""
    _enable_secure_input_respect(e2e_config_dir)
    monkeypatch.setattr("expando.engine.is_secure_input_active", lambda: True)

    service = build_service(e2e_config_dir)
    service.start()
    try:
        time.sleep(0.3)
        type_text_via_subprocess(":e2e", delay=0.18)
        content = ""
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            content = get_textedit_content()
            if ":e2e" in content or "Expanded E2E text" in content:
                break
            time.sleep(0.2)
        assert "Expanded E2E text" not in content
        if ":e2e" not in content:
            pytest.skip(f"Synthetic typing did not deliver the full trigger: {content!r}")
        assert ":e2e" in content
    finally:
        service.stop()


def test_engine_respects_secure_input_flag(e2e_config_dir, monkeypatch):
    _enable_secure_input_respect(e2e_config_dir)
    monkeypatch.setattr("expando.engine.is_secure_input_active", lambda: True)
    engine = build_engine(e2e_config_dir)
    injected: list[str] = []
    deleted: list[int] = []
    engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    engine.injector.delete_chars = lambda count: deleted.append(count)  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="TextEdit"),
    ):
        for char in ":e2e":
            assert engine.handle_char(char) is False

    assert injected == []
    assert deleted == []

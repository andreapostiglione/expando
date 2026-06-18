from __future__ import annotations

from unittest.mock import patch

import pytest
from pynput.keyboard import Key

from expando.app_context import AppContext
from expando.listener import KeyboardService, build_service


class _KeyChar:
    def __init__(self, char: str) -> None:
        self.char = char


def _type_chars(service: KeyboardService, text: str) -> None:
    for char in text:
        service._on_release(_KeyChar(char))


def test_build_service_expands_trigger_end_to_end(e2e_config_dir):
    service = build_service(e2e_config_dir)
    injected: list[str] = []
    deleted: list[int] = []

    service.engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    service.engine.injector.delete_chars = lambda count: deleted.append(count)  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="TextEdit"),
    ):
        _type_chars(service, ":e2e")

    assert deleted == [4]
    assert injected == ["Expanded E2E text"]


def test_build_service_respects_if_app_filter(e2e_config_dir):
    service = build_service(e2e_config_dir)
    injected: list[str] = []

    service.engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    service.engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Safari"),
    ):
        _type_chars(service, ":term")

    assert injected == []

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="Terminal"),
    ):
        _type_chars(service, ":term")

    assert injected == ["terminal only"]


@pytest.mark.image
def test_build_service_expands_image_trigger_end_to_end(e2e_config_dir):
    service = build_service(e2e_config_dir)
    injected_images: list[object] = []
    injected_text: list[str] = []

    service.engine.injector.inject_image = (  # type: ignore[method-assign]
        lambda path: injected_images.append(path) or True
    )
    service.engine.injector.inject = lambda text, **kwargs: injected_text.append(text)  # type: ignore[method-assign]
    service.engine.injector.delete_chars = lambda count: None  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="TextEdit"),
    ):
        _type_chars(service, ":img")

    assert len(injected_images) == 1
    assert injected_images[0].name == "badge.png"  # type: ignore[attr-defined]
    assert injected_text == []


def test_build_service_undo_shortcut_end_to_end(e2e_config_dir):
    service = build_service(e2e_config_dir)
    injected: list[str] = []
    deleted: list[int] = []

    service.engine.injector.inject = lambda text, **kwargs: injected.append(text)  # type: ignore[method-assign]
    service.engine.injector.delete_chars = lambda count: deleted.append(count)  # type: ignore[method-assign]

    with patch(
        "expando.engine.get_frontmost_context",
        return_value=AppContext(name="TextEdit"),
    ):
        _type_chars(service, ":e2e")
        service._track_modifier_press(Key.cmd)
        service._track_modifier_press(Key.shift)
        service._on_press(_KeyChar("z"))

    assert injected[-1] == ":e2e"
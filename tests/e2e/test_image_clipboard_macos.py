from __future__ import annotations

import platform
import time
from pathlib import Path

import pytest

from expando.injector import InjectorSettings, TextInjector

from tests.e2e.helpers import get_textedit_content, run_applescript

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")]

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def e2e_png_image(tmp_path: Path) -> Path:
    image_dir = tmp_path / "images"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "badge.png"
    image_path.write_bytes(MINIMAL_PNG)
    return image_path


def clipboard_contains_image() -> bool:
    info = run_applescript('return clipboard info as string')
    lowered = info.casefold()
    return "png" in lowered or "tiff" in lowered or "jpeg" in lowered or "picture" in lowered


@pytest.mark.clipboard
@pytest.mark.image
def test_image_injector_sets_clipboard(require_clipboard_e2e, e2e_png_image: Path):
    injector = TextInjector(InjectorSettings(backend="clipboard"))
    assert injector.inject_image(e2e_png_image) is True
    time.sleep(0.3)
    assert clipboard_contains_image(), run_applescript("return clipboard info as string")


def textedit_attachment_count() -> int:
    return int(
        run_applescript(
            "tell application \"TextEdit\" to return count of attachments of front document"
        )
    )


@pytest.mark.clipboard
@pytest.mark.image
def test_image_injector_paste_into_textedit(
    require_clipboard_e2e,
    textedit_document,
    e2e_png_image: Path,
):
    injector = TextInjector(InjectorSettings(backend="clipboard"))
    assert injector.inject_image(e2e_png_image) is True
    time.sleep(0.8)
    attachments = textedit_attachment_count()
    content = get_textedit_content()
    assert attachments > 0 or content.strip() != "", f"attachments={attachments}, text={content!r}"
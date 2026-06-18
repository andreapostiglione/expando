from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

import pytest

from expando.permissions import _check_accessibility_macos, clipboard_injection_ready
from tests.e2e.helpers import close_textedit_documents, open_textedit_blank


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "e2e: end-to-end tests; macOS injection tests need Accessibility permission",
    )
    config.addinivalue_line(
        "markers",
        "clipboard: clipboard injection E2E; needs Accessibility and working pbcopy/pbpaste",
    )
    config.addinivalue_line(
        "markers",
        "image: image clipboard injection E2E; needs Accessibility and PNG paste support",
    )


@pytest.fixture
def require_accessibility() -> None:
    if platform.system() != "Darwin":
        pytest.skip("macOS only")
    if _check_accessibility_macos() is not True:
        pytest.skip(
            "Accessibility permission not granted — enable Terminal or Python in "
            "System Settings → Privacy & Security → Accessibility"
        )


@pytest.fixture
def require_clipboard_e2e(require_textedit_e2e) -> None:
    if os.environ.get("EXPANDO_E2E_CLIPBOARD") != "1" and os.environ.get("EXPANDO_E2E_FULL") != "1":
        pytest.skip(
            "Clipboard E2E disabled — set EXPANDO_E2E_CLIPBOARD=1 on a runner with full TCC"
        )
    ready = clipboard_injection_ready()
    if ready is False:
        pytest.skip(
            "Clipboard injection unavailable — grant Accessibility to the runner process and "
            "ensure pbcopy/pbpaste work in the runner session"
        )
    if ready is None:
        pytest.skip("Could not verify clipboard injection readiness on this host")


@pytest.fixture
def require_full_e2e(require_accessibility) -> None:
    if os.environ.get("EXPANDO_E2E_FULL") != "1":
        pytest.skip(
            "Full E2E requires self-hosted runner with Accessibility — "
            "set EXPANDO_E2E_FULL=1"
        )


@pytest.fixture
def require_textedit_e2e(require_accessibility) -> None:
    try:
        subprocess.run(
            ["osascript", "-e", 'tell application "TextEdit" to id'],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as exc:
        pytest.skip(f"TextEdit E2E unavailable on this host: {exc}")


@pytest.fixture
def textedit_document(require_textedit_e2e) -> None:
    try:
        open_textedit_blank()
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        pytest.skip(f"TextEdit E2E unavailable on this host: {exc}")
    yield
    try:
        close_textedit_documents()
    except Exception:
        pass


@pytest.fixture
def e2e_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "expando"
    (config_dir / "config").mkdir(parents=True)
    (config_dir / "match").mkdir(parents=True)
    (config_dir / "config" / "default.yml").write_text(
        "\n".join(
            [
                "toggle_key: OFF",
                "undo_shortcut: CMD+SHIFT+Z",
                "search_shortcut: CMD+SHIFT+E",
                "auto_restart: false",
                "respect_secure_input: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    images = config_dir / "images"
    images.mkdir(parents=True)
    (images / "badge.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n"
        "  - trigger: ':e2e'\n"
        "    replace: 'Expanded E2E text'\n"
        "  - trigger: ':term'\n"
        "    replace: 'terminal only'\n"
        "    if_app:\n"
        "      - Terminal\n"
        "  - trigger: ':img'\n"
        "    image: images/badge.png\n",
        encoding="utf-8",
    )
    return config_dir
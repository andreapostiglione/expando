from __future__ import annotations

import platform
from pathlib import Path

import pytest

from expando.permissions import _check_accessibility_macos


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "e2e: end-to-end tests; macOS injection tests need Accessibility permission",
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
    (config_dir / "match" / "base.yml").write_text(
        "matches:\n"
        "  - trigger: ':e2e'\n"
        "    replace: 'Expanded E2E text'\n"
        "  - trigger: ':term'\n"
        "    replace: 'terminal only'\n"
        "    if_app:\n"
        "      - Terminal\n",
        encoding="utf-8",
    )
    return config_dir
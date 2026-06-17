from pathlib import Path

import pytest

from expando.image_paths import resolve_image_path


def test_resolve_image_path_inside_config(tmp_path: Path):
    config_dir = tmp_path / "expando"
    images = config_dir / "images"
    images.mkdir(parents=True)
    image = images / "logo.png"
    image.write_bytes(b"\x89PNG\r\n")

    resolved = resolve_image_path(config_dir, "images/logo.png")
    assert resolved == image.resolve()


def test_resolve_image_path_blocks_traversal(tmp_path: Path):
    config_dir = tmp_path / "expando"
    config_dir.mkdir(parents=True)
    outside = tmp_path / "secret.png"
    outside.write_bytes(b"\x89PNG\r\n")

    with pytest.raises(RuntimeError, match="inside config"):
        resolve_image_path(config_dir, str(outside))
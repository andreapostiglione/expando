from __future__ import annotations


def test_ui_appkit_imports_search_picker() -> None:
    from expando.ui_appkit import run_search_picker

    assert callable(run_search_picker)


def test_brand_asset_logo_exists() -> None:
    from expando.brand_assets import brand_asset_path

    from expando.brand_assets import menubar_template_icon

    assert brand_asset_path("logo.png") is not None
    assert menubar_template_icon() is not None


def test_menubar_template_sizes() -> None:
    from PIL import Image

    from expando.brand_assets import brand_asset_path

    for name, size in [
        ("logoTemplate.png", 22),
        ("logoTemplate@2x.png", 44),
        ("logoTemplate@3x.png", 66),
    ]:
        path = brand_asset_path(name)
        assert path is not None
        image = Image.open(path)
        assert image.size == (size, size)


def test_load_menubar_nsimage_has_representations() -> None:
    import sys

    if sys.platform != "darwin":
        return
    from expando.brand_assets import load_menubar_nsimage

    image = load_menubar_nsimage()
    assert image is not None
    assert image.representations()


def test_build_search_controller_does_not_raise() -> None:
    from expando.ui_appkit import _build_search_controller

    controller = _build_search_controller(
        [{"id": "0", "trigger": ":claude", "label": ":claude", "preview": "claude"}]
    )
    assert controller.window is not None
    assert controller.table_view.numberOfRows() == 1
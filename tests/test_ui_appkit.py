from __future__ import annotations


def test_ui_appkit_imports_search_picker() -> None:
    from expando.ui_appkit import run_search_picker

    assert callable(run_search_picker)


def test_brand_asset_logo_exists() -> None:
    from expando.brand_assets import brand_asset_path

    from expando.brand_assets import menubar_template_icon

    assert brand_asset_path("logo.png") is not None
    assert menubar_template_icon() is not None


def test_build_search_controller_does_not_raise() -> None:
    from expando.ui_appkit import _build_search_controller

    controller = _build_search_controller(
        [{"id": "0", "trigger": ":claude", "label": ":claude", "preview": "claude"}]
    )
    assert controller.window is not None
    assert controller.table_view.numberOfRows() == 1
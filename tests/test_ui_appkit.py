from __future__ import annotations


def test_ui_appkit_imports_search_picker() -> None:
    from expando.ui_appkit import run_search_picker

    assert callable(run_search_picker)


def test_brand_asset_logo_exists() -> None:
    from expando.brand_assets import brand_asset_path

    assert brand_asset_path("logo.png") is not None
    assert brand_asset_path("menubar-icon.png") is not None
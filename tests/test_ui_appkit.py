from __future__ import annotations


def test_ui_appkit_imports_search_picker() -> None:
    from expando.ui_appkit import run_search_picker

    assert callable(run_search_picker)


def test_brand_asset_logo_exists() -> None:
    from expando.brand_assets import brand_asset_path

    from expando.brand_assets import menubar_template_icon

    assert brand_asset_path("logo.png") is not None
    assert menubar_template_icon() is not None


def test_menubar_icon_when_launched_with_python_m(monkeypatch) -> None:
    import shutil
    import sys
    from pathlib import Path

    from expando.brand_assets import _app_bundle_resources, menubar_template_icon

    source = Path(__file__).resolve().parents[1] / "assets" / "logoTemplate.png"
    resources = Path("/tmp/expando-test-resources")
    if resources.exists():
        shutil.rmtree(resources)
    resources.mkdir()
    shutil.copy(source, resources / "logoTemplate.png")

    monkeypatch.setenv("EXPANDO_RESOURCES", str(resources))
    monkeypatch.setattr(
        sys,
        "argv",
        ["/opt/homebrew/bin/python3", "-m", "expando", "run"],
    )

    assert _app_bundle_resources() == resources
    assert menubar_template_icon() == resources / "logoTemplate.png"


def test_menubar_template_sizes() -> None:
    from PIL import Image

    from expando.brand_assets import brand_asset_path

    for name, size in [
        ("logoTemplate.png", 24),
        ("logoTemplate@2x.png", 48),
        ("logoTemplate@3x.png", 72),
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
    assert controller.table_view.numberOfColumns() == 1


def test_search_controller_keeps_selection_when_row_deselected() -> None:
    from expando.ui_appkit import _SearchController

    controller = _SearchController.alloc().initWithItems_(
        [
            {"id": "0", "trigger": ":date", "label": ":date", "preview": "06/19/2026"},
            {"id": "1", "trigger": ":claude", "label": ":claude", "preview": "claude"},
        ]
    )
    controller.visible = list(controller.items)
    controller._focused_item = controller.visible[1]

    class _Table:
        def selectedRow(self):
            return -1

    controller.table_view = _Table()
    item = controller._selected_item()
    assert item is not None
    assert item["trigger"] == ":claude"


def test_search_controller_accept_uses_focused_item() -> None:
    from expando.ui_appkit import _SearchController

    controller = _SearchController.alloc().initWithItems_(
        [{"id": "3", "trigger": ":claude", "label": ":claude", "preview": "claude"}]
    )
    controller.visible = list(controller.items)
    controller._focused_item = controller.visible[0]

    class _Table:
        def selectedRow(self):
            return -1

    controller.table_view = _Table()
    controller.window = None

    with __import__("unittest.mock").mock.patch(
        "expando.ui_appkit.close_appkit_session",
        lambda _controller: None,
    ):
        controller.accept_(None)

    assert controller.result == {"id": "3", "trigger": ":claude"}


def test_configure_single_column_table_adds_column() -> None:
    import sys

    if sys.platform != "darwin":
        return
    from AppKit import NSTableView

    from expando.ui_appkit_runtime import configure_single_column_table

    table = NSTableView.alloc().init()
    configure_single_column_table(table)
    assert table.numberOfColumns() == 1
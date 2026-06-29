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


def test_menubar_keeps_advanced_actions_out_of_main_menu() -> None:
    from expando.menubar import menu_layout_keys

    main, advanced = menu_layout_keys()
    assert "new_snippet" in main
    assert "editor" in main
    assert "hub" in main
    assert "advanced" in main

    advanced_only = {"health", "hub_updates", "backup", "restore", "restart"}
    assert advanced_only.isdisjoint({key for key in main if key})
    assert advanced_only.issubset(set(advanced))


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


def test_text_view_setter_preserves_editability() -> None:
    import sys

    if sys.platform != "darwin":
        return
    from AppKit import NSTextView

    from expando.ui_appkit_runtime import set_text_view_string

    editable = NSTextView.alloc().init()
    editable.setEditable_(True)
    set_text_view_string(editable, "editable")
    assert editable.isEditable()
    assert str(editable.string()) == "editable"

    readonly = NSTextView.alloc().init()
    readonly.setEditable_(False)
    set_text_view_string(readonly, "readonly")
    assert not readonly.isEditable()
    assert str(readonly.string()) == "readonly"


def test_snippet_editor_appkit_layout_has_no_overlapping_controls(monkeypatch) -> None:
    import sys

    if sys.platform != "darwin":
        return

    from expando import snippet_editor_appkit

    captured = {}

    def fake_run_appkit_session(builder):
        controller = builder()
        controller.window.orderOut_(None)
        captured["controller"] = controller
        return {"opened": "1"}

    monkeypatch.setattr(snippet_editor_appkit, "run_appkit_session", fake_run_appkit_session)
    snippet_editor_appkit.run_snippet_editor(
        [
            {
                "id": "0",
                "trigger": ":hello",
                "label": ":hello",
                "replace": "Hello",
                "editable": "1",
            }
        ],
        on_save=lambda _payload: None,
        on_create=lambda _payload: None,
        on_delete=lambda _entry_id: None,
        reload_items=lambda: [],
        match_files=["dev.yml"],
    )

    controller = captured["controller"]
    content = getattr(controller, "editor_content_view", controller.window.contentView())
    frames = []
    for view in content.subviews():
        frame = view.frame()
        frames.append(
            (
                str(view.className()),
                float(frame.origin.x),
                float(frame.origin.y),
                float(frame.size.width),
                float(frame.size.height),
            )
        )

    def overlaps(first, second) -> bool:
        _, ax, ay, aw, ah = first
        _, bx, by, bw, bh = second
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    for index, first in enumerate(frames):
        for second in frames[index + 1 :]:
            assert not overlaps(first, second), (first, second)

from expando.menubar_status import resolve_menubar_title


def test_resolve_menubar_title_priority() -> None:
    assert resolve_menubar_title(
        listener_dead=True,
        enabled=True,
        hub_updates=3,
        permissions_ok=True,
        snoozed=True,
    ) == "⚠"
    assert resolve_menubar_title(
        listener_dead=False,
        enabled=True,
        hub_updates=3,
        permissions_ok=False,
        snoozed=True,
    ) == "🔒"
    assert resolve_menubar_title(
        listener_dead=False,
        enabled=True,
        hub_updates=3,
        permissions_ok=True,
        snoozed=True,
    ) == "⏸"
    assert resolve_menubar_title(
        listener_dead=False,
        enabled=True,
        hub_updates=2,
        permissions_ok=True,
        snoozed=False,
    ) == "↑2"
    assert resolve_menubar_title(
        listener_dead=False,
        enabled=False,
        hub_updates=0,
        permissions_ok=True,
        snoozed=False,
    ) == "○"
    assert resolve_menubar_title(
        listener_dead=False,
        enabled=True,
        hub_updates=0,
        permissions_ok=True,
        snoozed=False,
    ) is None
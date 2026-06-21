from __future__ import annotations


def pick_list_item(
    items: list[str],
    *,
    title: str,
    message: str,
    confirm_label: str,
    cancel_label: str,
) -> str | None:
    """Show a native popup to pick one string from *items*."""
    if not items:
        return None

    def _ask() -> str | None:
        from AppKit import (
            NSAlert,
            NSAlertFirstButtonReturn,
            NSMakeRect,
            NSPopUpButton,
            NSView,
        )

        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(0, 0, 320, 26))
        for item in items:
            popup.addItemWithTitle_(item)
        accessory = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 320, 26))
        accessory.addSubview_(popup)
        alert.setAccessoryView_(accessory)
        alert.addButtonWithTitle_(confirm_label)
        alert.addButtonWithTitle_(cancel_label)
        if alert.runModal() != NSAlertFirstButtonReturn:
            return None
        return str(popup.titleOfSelectedItem())

    try:
        from .ui_main_thread import call_on_main_thread

        return call_on_main_thread(_ask, wait=True)
    except Exception:
        return items[0] if len(items) == 1 else None
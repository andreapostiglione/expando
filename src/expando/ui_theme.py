"""AppKit visual tokens for Expando product UI (snippet editor, pickers)."""

from __future__ import annotations

from AppKit import (
    NSBezierPath,
    NSButton,
    NSButtonTypeMomentaryPushIn,
    NSColor,
    NSFont,
    NSFontWeightMedium,
    NSFontWeightRegular,
    NSFontWeightSemibold,
    NSMakeRect,
    NSTextField,
    NSView,
    NSViewHeightSizable,
    NSViewMaxXMargin,
    NSViewMinYMargin,
    NSViewWidthSizable,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialSidebar,
    NSVisualEffectMaterialWindowBackground,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSBezelStyleRounded,
)

# Layout rhythm (pt)
SPACE_XS = 6.0
SPACE_SM = 10.0
SPACE_MD = 16.0
SPACE_LG = 24.0
SPACE_XL = 32.0

SIDEBAR_WIDTH = 300.0
WINDOW_WIDTH = 1080.0
WINDOW_HEIGHT = 720.0
TOOLBAR_HEIGHT = 56.0
ROW_HEIGHT = 34.0


def font_title() -> NSFont:
    return NSFont.systemFontOfSize_weight_(20.0, NSFontWeightSemibold)


def font_section() -> NSFont:
    return NSFont.systemFontOfSize_weight_(11.0, NSFontWeightSemibold)


def font_label() -> NSFont:
    return NSFont.systemFontOfSize_weight_(13.0, NSFontWeightRegular)


def font_body() -> NSFont:
    return NSFont.systemFontOfSize_weight_(13.0, NSFontWeightRegular)


def font_mono() -> NSFont:
    return NSFont.monospacedSystemFontOfSize_weight_(13.0, NSFontWeightRegular)


def font_caption() -> NSFont:
    return NSFont.systemFontOfSize_weight_(11.0, NSFontWeightRegular)


def color_label():
    return NSColor.labelColor()


def color_secondary():
    return NSColor.secondaryLabelColor()


def color_tertiary():
    return NSColor.tertiaryLabelColor()


def color_field_bg():
    return NSColor.textBackgroundColor()


def color_control_bg():
    return NSColor.controlBackgroundColor()


def color_separator():
    return NSColor.separatorColor()


def color_accent():
    return NSColor.controlAccentColor()


def make_label(
    text: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float = 18.0,
    secondary: bool = False,
    section: bool = False,
) -> NSTextField:
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    label.setStringValue_(text)
    label.setEditable_(False)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setSelectable_(False)
    if section:
        label.setFont_(font_section())
        label.setTextColor_(color_secondary())
    elif secondary:
        label.setFont_(font_caption())
        label.setTextColor_(color_secondary())
    else:
        label.setFont_(font_label())
        label.setTextColor_(color_label())
    return label


def make_text_field(
    *,
    x: float,
    y: float,
    width: float,
    height: float = 28.0,
    mono: bool = False,
    placeholder: str = "",
) -> NSTextField:
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    field.setFont_(font_mono() if mono else font_body())
    field.setTextColor_(color_label())
    field.setBackgroundColor_(color_field_bg())
    field.setDrawsBackground_(True)
    field.setBezeled_(True)
    if placeholder:
        try:
            field.setPlaceholderString_(placeholder)
        except Exception:
            pass
    return field


def make_button(
    title: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float = 32.0,
    primary: bool = False,
    destructive: bool = False,
) -> NSButton:
    button = NSButton.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    button.setTitle_(title)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setButtonType_(NSButtonTypeMomentaryPushIn)
    button.setFont_(NSFont.systemFontOfSize_weight_(13.0, NSFontWeightMedium))
    if primary:
        try:
            button.setKeyEquivalent_("\r")
        except Exception:
            pass
        # Emphasize primary action when AppKit supports it.
        try:
            from AppKit import NSControlStateValueOn

            button.setHighlighted_(False)
        except Exception:
            pass
    if destructive:
        try:
            button.setContentTintColor_(NSColor.systemRedColor())
        except Exception:
            pass
    return button


def make_sidebar_effect(frame) -> NSVisualEffectView:
    visual = NSVisualEffectView.alloc().initWithFrame_(frame)
    visual.setAutoresizingMask_(NSViewHeightSizable | NSViewMaxXMargin)
    visual.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
    try:
        visual.setMaterial_(NSVisualEffectMaterialSidebar)
    except Exception:
        visual.setMaterial_(NSVisualEffectMaterialWindowBackground)
    visual.setState_(NSVisualEffectStateActive)
    return visual


def make_content_effect(frame) -> NSVisualEffectView:
    visual = NSVisualEffectView.alloc().initWithFrame_(frame)
    visual.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    visual.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
    visual.setMaterial_(NSVisualEffectMaterialWindowBackground)
    visual.setState_(NSVisualEffectStateActive)
    return visual


def make_panel_view(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> NSView:
    """Soft card surface for grouped content."""
    panel = NSView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    panel.setWantsLayer_(True)
    layer = panel.layer()
    if layer is not None:
        try:
            layer.setCornerRadius_(10.0)
            layer.setBackgroundColor_(color_control_bg().CGColor())
            layer.setBorderWidth_(1.0)
            layer.setBorderColor_(color_separator().CGColor())
        except Exception:
            pass
    return panel


def style_editor_text_view(text_view, *, editable: bool = True, mono: bool = False) -> None:
    text_view.setEditable_(editable)
    text_view.setRichText_(False)
    text_view.setFont_(font_mono() if mono else font_body())
    text_view.setTextColor_(color_label())
    text_view.setDrawsBackground_(True)
    text_view.setBackgroundColor_(color_field_bg())
    text_view.setInsertionPointColor_(color_label())
    try:
        text_view.setAutomaticQuoteSubstitutionEnabled_(False)
        text_view.setAutomaticDashSubstitutionEnabled_(False)
    except Exception:
        pass


def style_sidebar_table(table) -> None:
    table.setRowHeight_(ROW_HEIGHT)
    table.setUsesAlternatingRowBackgroundColors_(False)
    try:
        table.setBackgroundColor_(NSColor.clearColor())
        table.setSelectionHighlightStyle_(1)  # regular
    except Exception:
        pass
    try:
        from AppKit import NSTableViewRowSizeStyleMedium

        table.setRowSizeStyle_(NSTableViewRowSizeStyleMedium)
    except Exception:
        pass

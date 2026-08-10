"""AppKit visual tokens for Expando product UI.

On macOS 26+ (Tahoe) prefers Liquid Glass via NSGlassEffectView / glass
bezels. Falls back to NSVisualEffectView on older systems.
"""

from __future__ import annotations

from AppKit import (
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
    NSVisualEffectMaterialUnderWindowBackground,
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
ROW_HEIGHT = 36.0

# Liquid Glass radii
RADIUS_CONTROL = 10.0
RADIUS_CARD = 18.0
RADIUS_SIDEBAR = 20.0
RADIUS_WINDOW_INSET = 12.0


def _has_glass() -> bool:
    try:
        from AppKit import NSGlassEffectView  # noqa: F401

        return True
    except Exception:
        return False


def font_title() -> NSFont:
    return NSFont.systemFontOfSize_weight_(22.0, NSFontWeightSemibold)


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
    # Slight translucency so glass shows through on Tahoe
    try:
        return NSColor.textBackgroundColor().colorWithAlphaComponent_(0.72)
    except Exception:
        return NSColor.textBackgroundColor()


def color_control_bg():
    return NSColor.controlBackgroundColor()


def color_separator():
    return NSColor.separatorColor()


def color_accent():
    return NSColor.controlAccentColor()


def color_glass_tint():
    """Very soft accent wash for glass panels."""
    try:
        return NSColor.controlAccentColor().colorWithAlphaComponent_(0.08)
    except Exception:
        return None


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
    height: float = 30.0,
    mono: bool = False,
    placeholder: str = "",
) -> NSTextField:
    field = NSTextField.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    field.setFont_(font_mono() if mono else font_body())
    field.setTextColor_(color_label())
    field.setBackgroundColor_(color_field_bg())
    field.setDrawsBackground_(True)
    field.setBezeled_(True)
    try:
        field.setFocusRingType_(1)  # exterior
    except Exception:
        pass
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
    button.setButtonType_(NSButtonTypeMomentaryPushIn)
    button.setFont_(NSFont.systemFontOfSize_weight_(13.0, NSFontWeightMedium))
    # Prefer Liquid Glass bezel on macOS 26+
    try:
        from AppKit import NSBezelStyleGlass

        button.setBezelStyle_(NSBezelStyleGlass)
    except Exception:
        button.setBezelStyle_(NSBezelStyleRounded)
    if primary:
        try:
            button.setKeyEquivalent_("\r")
        except Exception:
            pass
        try:
            # Emphasize primary control when supported
            button.setHighlighted_(False)
            if hasattr(button, "setHasDestructiveAction_"):
                pass
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
    try:
        visual.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
    except Exception:
        visual.setMaterial_(NSVisualEffectMaterialWindowBackground)
    visual.setState_(NSVisualEffectStateActive)
    return visual


def make_window_backdrop(frame) -> NSView:
    """Full-window soft backdrop so Liquid Glass has something ambient to sample."""
    visual = NSVisualEffectView.alloc().initWithFrame_(frame)
    visual.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    visual.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
    try:
        visual.setMaterial_(NSVisualEffectMaterialUnderWindowBackground)
    except Exception:
        visual.setMaterial_(NSVisualEffectMaterialWindowBackground)
    visual.setState_(NSVisualEffectStateActive)
    return visual


def make_glass_panel(
    frame,
    *,
    corner_radius: float = RADIUS_CARD,
    clear: bool = False,
    tint: bool = False,
    autoresizing: int | None = None,
) -> tuple[NSView, NSView]:
    """Return (shell, content) — shell is glass on Tahoe, vibrancy fallback otherwise.

    Put all interactive subviews into *content*.
    """
    if _has_glass():
        from AppKit import (
            NSGlassEffectView,
            NSGlassEffectViewStyleClear,
            NSGlassEffectViewStyleRegular,
        )

        glass = NSGlassEffectView.alloc().initWithFrame_(frame)
        glass.setCornerRadius_(corner_radius)
        try:
            glass.setStyle_(
                NSGlassEffectViewStyleClear if clear else NSGlassEffectViewStyleRegular
            )
        except Exception:
            pass
        if tint:
            tint_color = color_glass_tint()
            if tint_color is not None:
                try:
                    glass.setTintColor_(tint_color)
                except Exception:
                    pass
        if autoresizing is not None:
            glass.setAutoresizingMask_(autoresizing)
        else:
            glass.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        content = NSView.alloc().initWithFrame_(glass.bounds())
        content.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        glass.setContentView_(content)
        return glass, content

    # Fallback: soft vibrancy card
    shell = make_sidebar_effect(frame) if clear else make_content_effect(frame)
    if autoresizing is not None:
        shell.setAutoresizingMask_(autoresizing)
    shell.setWantsLayer_(True)
    if shell.layer() is not None:
        try:
            shell.layer().setCornerRadius_(corner_radius)
            shell.layer().setMasksToBounds_(True)
        except Exception:
            pass
    content = NSView.alloc().initWithFrame_(shell.bounds())
    content.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    shell.addSubview_(content)
    return shell, content


def make_glass_container(frame, *, spacing: float = 16.0) -> tuple[NSView, NSView]:
    """Container that merges nearby glass surfaces (Tahoe). Falls back to plain view."""
    try:
        from AppKit import NSGlassEffectContainerView

        container = NSGlassEffectContainerView.alloc().initWithFrame_(frame)
        container.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        try:
            container.setSpacing_(spacing)
        except Exception:
            pass
        content = NSView.alloc().initWithFrame_(container.bounds())
        content.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        container.setContentView_(content)
        return container, content
    except Exception:
        host = NSView.alloc().initWithFrame_(frame)
        host.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        return host, host


def make_panel_view(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
) -> NSView:
    """Soft card surface for grouped content (legacy helper)."""
    panel = NSView.alloc().initWithFrame_(NSMakeRect(x, y, width, height))
    panel.setWantsLayer_(True)
    layer = panel.layer()
    if layer is not None:
        try:
            layer.setCornerRadius_(RADIUS_CARD)
            layer.setBackgroundColor_(
                NSColor.controlBackgroundColor().colorWithAlphaComponent_(0.55).CGColor()
            )
            layer.setBorderWidth_(0.5)
            layer.setBorderColor_(
                NSColor.separatorColor().colorWithAlphaComponent_(0.35).CGColor()
            )
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
        text_view.setTextContainerInset_((8.0, 10.0))
    except Exception:
        pass


def style_sidebar_table(table) -> None:
    table.setRowHeight_(ROW_HEIGHT)
    table.setUsesAlternatingRowBackgroundColors_(False)
    try:
        table.setBackgroundColor_(NSColor.clearColor())
        table.setSelectionHighlightStyle_(1)  # regular
        table.setIntercellSpacing_((0.0, 4.0))
    except Exception:
        pass
    try:
        from AppKit import NSTableViewRowSizeStyleMedium

        table.setRowSizeStyle_(NSTableViewRowSizeStyleMedium)
    except Exception:
        pass


def style_scroll_field(scroll_view, *, inset: bool = True) -> None:
    """Round, soft scrollable field shell that sits on glass."""
    scroll_view.setBorderType_(0)
    scroll_view.setDrawsBackground_(True)
    scroll_view.setBackgroundColor_(color_field_bg())
    scroll_view.setWantsLayer_(True)
    if scroll_view.layer() is not None:
        try:
            scroll_view.layer().setCornerRadius_(RADIUS_CONTROL)
            scroll_view.layer().setMasksToBounds_(True)
            scroll_view.layer().setBorderWidth_(0.5)
            scroll_view.layer().setBorderColor_(
                NSColor.separatorColor().colorWithAlphaComponent_(0.28).CGColor()
            )
        except Exception:
            pass

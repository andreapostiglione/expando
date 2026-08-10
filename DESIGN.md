# Expando design system (product UI)

## Scene

A focused macOS utility used between tasks — quick open, edit a snippet, close. Ambient light is typical office/home desk; UI should respect system light/dark appearance rather than force a theme.

## Color strategy

**Restrained.** System materials (sidebar / window background) + one system accent for primary actions and selection. No decorative gradients, no glassmorphism for its own sake.

| Token | Role |
|-------|------|
| Window / content | `NSVisualEffectMaterialWindowBackground` |
| Sidebar | `NSVisualEffectMaterialSidebar` |
| Fields | `textBackgroundColor` |
| Labels | `labelColor` / `secondaryLabelColor` |
| Accent | `controlAccentColor` (primary Save) |
| Danger | `systemRedColor` tint on Delete |

## Typography

- System SF Pro only (product familiarity)
- Title 20 semibold, body 13 regular, section 11 semibold, mono 13 for triggers/preview
- No display fonts in tool chrome

## Layout

- Window default **1080×720**, min **900×560**
- Sidebar **300pt** list + search
- Content column with 24pt padding, label column ~120pt
- Bottom toolbar **56pt** full width: New / Save / Delete / Duplicate · Close
- Three non-overlapping root regions (toolbar · sidebar · main) for reliable hit-testing

## Components

- Search field: standard `NSSearchField`
- List: single-column table, row height ~34, no alternating stripes in sidebar
- Text areas: bezeled scroll views, monospaced preview
- Buttons: rounded bezel; Save is primary (Return); Delete is destructive tint

## Motion

- None beyond AppKit defaults. State changes are immediate.

## Do / Don't

- **Do** use system materials and semantic colors
- **Do** keep advanced YAML fields available but out of the primary path
- **Don't** invent custom chrome that fights macOS
- **Don't** nest cards inside cards

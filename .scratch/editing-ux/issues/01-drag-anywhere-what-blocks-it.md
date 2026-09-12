# Drag anywhere: what stops it today?

Type: grilling
Status: resolved
Blocked by: 06

## Question

The ask is "make sure I can drag the overlay wherever I want on the screen". Code
already lets edit mode drag with no clamp (`Overlay.mouseMoveEvent` -> `self.move()`),
so the gap is one of these, and the answer decides the whole ticket tree under it:

1. **Gating**: the user wants to drag without first pressing **Edit on screen** in
   settings (e.g. hold a modifier, tray toggle, or hotkey to unlock dragging).
2. **Reach**: dragging works but some region is unreachable or the window snaps back
   (screen edges at 150% DPI, partially off-screen placement, position reset by
   `apply()`/`keep_on_top`, edit mode auto-ending when the settings window loses
   focus via `applicationStateChanged`).
3. **Persistence**: the drop position is not the position after restart or after
   switching layouts (x/y are per-layout in `PROFILE_KEYS`).

Decide which of these is the real complaint (may be several), and whether partially
off-screen placement should be allowed or clamped to the visible area.

Recommended: wait for ticket 06's measured facts, then ask the user to reproduce the
failure once; default to allowing partial off-screen but never fully off-screen.

## Comments

### Round 1 (2026-09-12, user confirmed every recommendation)

1b 2c 3b 4y 5y. No round 2 needed.

## Answer

**Diagnosis.** Reach is not the problem (see "Verify drag reach on the real
screen"). The user pressed Edit on screen, switched to the game, and the overlay
stopped responding because edit mode ends on focus loss. The fix is entry, not
reach.

**Entry points.** Edit mode toggles from three places showing one state:
- Hotkey **Ctrl+Alt+E** (default; editable in the Keyboard shortcuts card like
  the other three, stored under `hotkeys.edit`).
- Tray menu item **Edit on screen** (same words as the button; the glossary avoids "move mode").
- The existing **Edit on screen** button on the Layout page.
Entering edit mode shows the overlay if it was hidden (as the button does today).

**Exit.** Explicitly via hotkey again, **Esc** while the overlay has focus, or
**Done editing**; and, as today, automatically when the app loses focus (the
protection against game input dragging/resizing the overlay). The on-overlay hint
bar names the hotkey and Esc.

**Lost-overlay safety.** On startup and on every apply, if the overlay rect
intersects no screen at all, move it to the nearest position where it is visible.
Partial off-screen placement stays allowed.

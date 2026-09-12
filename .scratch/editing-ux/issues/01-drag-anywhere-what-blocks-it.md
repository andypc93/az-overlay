# Drag anywhere: what stops it today?

Type: grilling
Status: open
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

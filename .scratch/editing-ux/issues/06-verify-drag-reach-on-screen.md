# Verify drag reach on the real screen

Type: task
Status: resolved

## Question

AFK fact-finding for ticket 01. Using `debug/az_debug.py` (move logger) and
`debug/edit_mode_game_loop.py` (real-input loop), establish on the user's 4K/150% DPI
single monitor:

- Can the overlay be dragged to every screen edge and partially off-screen? Does
  anything snap it back (`apply()`, `keep_on_top`, `applicationStateChanged`)?
- Does the dropped position survive **Done editing**, closing settings, switching
  layouts, and restart?
- Does the position drift between logical and physical px at 150% DPI?

Must run while the user is present (moves the real mouse). Record measured
findings under `## Answer`.

## Answer

Ran `debug/drag_reach_probe.py` (new, throwaway; real Win32 mouse input against a
temp copy of config/profiles) on the user's screen, 2026-09-12.

Screen: 2560x1440 logical at DPR 1.5 (3840x2160 physical), taskbar takes 48 px.
Overlay at scale 0.5: 488x446 logical.

| Target | Reached | Stable after 2 s (keep_on_top tick) |
| --- | --- | --- |
| top-left, top-right, bottom-right, bottom-left corners | yes, exact | yes |
| half off the left edge (x = -244) | yes, exact | yes |
| half off bottom-right | to (2316, 1180) | yes |
| half off top | to (400, -75) | yes |

The two "half off" shortfalls are not code limits: a slow per-step re-run shows
the window following the cursor 1:1 on every step. The cursor itself is clamped
to the screen by Windows, so the overlay can leave the screen only as far as
the grabbed point allows (the point you hold must stay on screen). No snap-back
from `apply()`, `keep_on_top`, or `applicationStateChanged`.

Persistence: dropped position is identical after **Done editing**, after a
settings-driven `apply()`, and after closing settings and reloading config from
disk (saved into the current layout file). DPI: `cfg x/y` are logical px, Win32
rect = logical x 1.5, no drift.

Conclusion for "Drag anywhere: what stops it today?": in edit mode, nothing.
The remaining candidates are gating (must press **Edit on screen** in settings
first) or something outside this probe (e.g. edit mode ending when the settings
window loses focus, by design since the alt-tab fix).

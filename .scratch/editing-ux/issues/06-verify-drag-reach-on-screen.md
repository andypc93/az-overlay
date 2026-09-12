# Verify drag reach on the real screen

Type: task
Status: open

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

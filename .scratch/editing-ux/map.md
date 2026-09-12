# Wayfinder map: editing-ux

Label: wayfinder:map
Created: 2026-09-12

## Destination

A spec (ready to hand to `/to-tickets`) for the overlay-editing experience covering
four asks: (1) drag the overlay anywhere on screen, (2) delete multiple pads and whole
rows/columns easily, (3) every edit persists automatically with no Save button, and
(4) a newly created layout is saved from the moment it exists.

## Notes

- Domain: Windows PySide6 input overlay. `overlay.py` = the on-screen window,
  `settings_ui.py` = settings window, `templates.py` = device templates.
- Terms (no `CONTEXT.md` yet; create one when the first term is settled in a ticket):
  **layout** (README term) = **profile** (code term, `profiles/<name>.json`, `PROFILE_KEYS`).
  Canonical word: **layout** (decided in ticket 03). **Pad** = one key/button cell in `cfg["keys"]`
  (`col`,`row`,`w`,`h` in key units). **Stick** = `cfg["sticks"]` entry (not a pad).
  **Edit on screen** = overlay edit mode (drag / wheel / click-to-rebind).
- Skills every session should consult: `mattpocock-skills:grilling`,
  `mattpocock-skills:domain-modeling`; `mattpocock-skills:prototype` for UI tickets.
- Standing preference: keep edits live-applied (no Apply/OK). Saved layouts already
  autosave via a 400 ms debounce (`SettingsWindow._schedule_save` -> `save_config`).
- Regression loop for anything touching edit mode: `debug/edit_mode_game_loop.py`
  and `debug/az_debug.py` (see memory note). Tests: `python -m pytest -q` (78 pass).
- Facts established while charting:
  - Drag exists only in edit mode; `Overlay.mouseMoveEvent` calls `self.move()` with
    no clamp, so nothing in code stops off-screen or edge placement. Position is
    absolute px (`cfg["x"]`,`cfg["y"]`), spinboxes allow -10000..10000. User's box:
    single 4K monitor at 150% DPI.
  - Pads table is `SingleSelection`; **Remove** deletes exactly one pad. No row/column
    delete exists. `Add row`/`Add column` append blank pads at the layout edge.
  - "Unnamed layout" state exists: `cfg["profile"] == ""`. In that state
    `save_config` deliberately drops all `PROFILE_KEYS` edits (memory only). You land
    there after **Delete saved layout** on the current layout, or with an empty
    `profiles/` dir. That is the only path where edits are lost.
  - `_new_from_template` already writes `profiles/<name>.json` immediately and later
    edits autosave. `save_profile` silently overwrites an existing name (no collision
    check). `_profile_save_as` is a copy, not a rename; there is no rename.

## Decisions so far

<!-- one line per resolved ticket: [title](issues/NN-slug.md): gist -->
- [Drag anywhere: what stops it today?](issues/01-drag-anywhere-what-blocks-it.md): entry, not reach. Edit mode toggles via Ctrl+Alt+E hotkey (editable), tray "Edit on screen", and the existing button; exits via hotkey/Esc/Done and still on focus loss; overlay pulled back if it touches no screen.
- [Verify drag reach on the real screen](issues/06-verify-drag-reach-on-screen.md): measured on the real 4K/150% screen: drag reaches every corner and partial off-screen, follows the cursor 1:1, no snap-back, position survives Done editing / apply / restart. Only limit = cursor clamped to screen. Drag complaint must be gating, not reach.
- [Prototype: Keys page with multi-select and row/column delete](issues/05-keys-page-prototype.md): winner = B's selection toolbar (only while pads selected) above search + table, A's full-width Undo bar under the table, Add controls at the bottom; canvas linked on the ticket.
- [New layout creation and naming](issues/04-new-layout-creation-flow.md): creation already autosaves; names unique case-insensitively after filename sanitising; Create auto-suffixes "(2)" on collision, blank name = template suggestion; Rename added (collision rejected inline); "Save as new" becomes Duplicate ("<name> copy", switches to copy); new layouts inherit colors/position/opacity.
- [Remove the unnamed layout state](issues/03-no-unnamed-layout-state.md): every layout always named + on disk, Save button gone; empty profiles/ re-seeds bundled default; delete current -> first in list, deleting the last one allowed; word is "layout"; config.json = globals only with one-time "Recovered" migration; static "Changes save automatically" header text.
- [Bulk delete: pads, rows, columns](issues/02-bulk-delete-interaction-model.md): shared multi-select in table + visual layout; Remove/Delete key/Delete row/Delete column act on it; column = centre-in-span rule; no relayout, sticks untouched; single-level delete-only Undo (button + Ctrl+Z), no dialogs.

## Not yet specified

- README / Help page copy updates once the Save button is gone.

## Out of scope

- Multi-monitor placement rules (user has a single monitor); revisit as a new effort
  if a second monitor appears.
- Moving/resizing pads by dragging on the overlay itself (visual geometry editing).
  The asks are about deleting pads, not repositioning them.

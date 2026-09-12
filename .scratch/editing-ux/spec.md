# Spec: editing-ux

Status: ready-for-agent
Map: [map.md](map.md) (wayfinder, 7 tickets resolved 2026-09-12)
Glossary: `CONTEXT.md` at the repo root (Layout, Pad, Stick, Selection, Column/Row, Edit on screen, Undo)

## Problem Statement

Four things get in the way of editing the overlay:

1. **Moving the overlay stops working mid-edit.** Edit on screen can only be
   started from the settings Layout page, and it ends the moment the settings
   window loses focus. Switch to the game and the overlay no longer responds.
   Reach itself is fine: measured on the user's 4K/150% screen, a drag lands the
   overlay on every corner and partially off-screen, exactly and without snapping
   back.
2. **Deleting pads is one at a time.** The pads table is single-select, Remove
   deletes one pad, and there is no way to remove a whole row or column, even
   though Add row / Add column exist.
3. **Some edits are not saved.** Named layouts autosave, but an "unnamed" layout
   (after deleting the current layout, or with no layouts on disk) keeps edits in
   memory only until the user presses Save layout. The Save button exists only to
   escape that state.
4. **Naming a new layout is fragile.** Creating a layout with a name that already
   exists silently overwrites it, there is no Rename, and "Save as new layout…"
   is really Duplicate.

## Solution

- Edit on screen becomes reachable from anywhere: a Ctrl+Alt+E hotkey and a tray
  item toggle it, Esc ends it, and it still ends on focus loss so game input can
  never drag or resize the overlay. If the overlay ever sits on no screen at all,
  it is pulled back into view.
- Pads can be multi-selected in the table and on the visual layout (one shared
  selection), and removed with Remove, the Delete key, Delete row, or Delete
  column. Deletes are reversible with a single-level Undo. No confirmation
  dialogs.
- Every layout always has a name and a file. The Save button, the unnamed state,
  and the layout copy inside `config.json` all go away. Deleting every layout
  re-seeds the bundled default.
- Names are unique (case-insensitive after filename sanitising). Create
  auto-suffixes on collision, Rename is added, Duplicate replaces Save-as.
- The settings header becomes one row: the layout name as a big title (click to
  rename, chevron to switch), tagline under it, and Rename / Duplicate / Delete /
  + New layout on the right. The Theme selector moves to the Appearance page.

Reference mockups (chosen designs on the "Chosen" page of each):
- Keys page with bulk delete: https://claude.ai/code/artifact/f1218af6-0d38-4db9-98ff-7c71c4aeb252
- Settings header and Appearance page: https://claude.ai/code/artifact/b77b82b1-8362-413a-ac15-64afc1d2a0f7

## User Stories

### Moving the overlay

1. As a player, I want to press Ctrl+Alt+E while my game is in front, so that the overlay becomes draggable without opening settings.
2. As a player, I want the hotkey to show the overlay if it was hidden, so that I can position it even after hiding it.
3. As a player, I want pressing Ctrl+Alt+E again to end Edit on screen, so that the overlay goes back to click-through.
4. As a player, I want Esc to end Edit on screen while the overlay has focus, so that I have a second obvious way out.
5. As a player, I want a tray menu item "Edit on screen" that toggles the same mode, so that I can find it without remembering a hotkey.
6. As a user, I want the Layout page button, the tray item, and the hotkey to reflect one shared state, so that the button reads "Done editing" whenever edit mode is on, however it was started.
7. As a user, I want to change the edit hotkey in the Keyboard shortcuts card like the other three, so that it does not clash with my game's bindings.
8. As a player, I want Edit on screen to end automatically when the app loses focus, so that clicking back into my game never drags or resizes the overlay.
9. As a player, I want the on-overlay hint bar to name the hotkey and Esc, so that I know how to finish when settings is not open.
10. As a user, I want to drag the overlay to any screen corner and partially off-screen, so that I can tuck it wherever my HUD has room.
11. As a user, I want the dropped position to be exactly where I let go, after Done editing, after any other settings change, and after a restart, so that I never re-position it.
12. As a user, I want the overlay pulled back to the nearest visible spot if it would otherwise sit on no screen at all, so that a resolution change or a typo in Precise position cannot lose it.
13. As a user, I want partial off-screen placement to stay allowed, so that "pulled back" never fights a deliberate edge placement.

### Selecting and deleting pads

14. As a user, I want to ctrl-click and shift-click rows in the pads table, so that I can select several pads.
15. As a user, I want Ctrl+A in the table to select every visible pad, so that I can act on all of them at once.
16. As a user, I want Ctrl+A under an active search filter to select only the pads that match, so that "filter, select all, delete" removes exactly what I searched for.
17. As a user, I want to ctrl-click pads on the visual layout to add them to the selection, so that I can pick by position instead of by name.
18. As a user, I want to drag a box on the visual layout to select every pad inside it, so that a block of pads is one gesture.
19. As a user, I want the table and the visual layout to show the same selection, so that whichever I use, the other agrees.
20. As a user, I want the Remove button to delete every selected pad and show how many, so that it is clear what one click will do.
21. As a user, I want the Delete key to remove the selection when the table or the visual layout has focus, so that I do not have to reach for the mouse.
22. As a user, I want the Delete key ignored while Record input capture is active, so that recording a Delete binding never deletes pads.
23. As a user, I want a Delete row button next to Add row, so that I can remove the row of every selected pad.
24. As a user, I want a Delete column button next to Add column, so that I can remove the column of every selected pad.
25. As a user, I want "the column of a pad" to mean every pad whose horizontal centre lies within that pad's horizontal span, so that staggered keyboard keys are not swept up by quarter-unit overlaps.
26. As a user, I want "the row of a pad" defined the same way vertically, so that rows and columns behave alike.
27. As a user, I want the remaining pads to stay exactly where they are after a delete, so that nothing shifts unexpectedly.
28. As a user, I want sticks and d-pads left untouched by Remove, Delete row, and Delete column, so that pad cleanup never removes my stick.
29. As a user, I want no confirmation dialog on any delete, so that cleanup stays fast.
30. As a user, I want an "Undo delete · N pads" bar to appear under the table after a delete, so that a mistake is one click away from fixed.
31. As a user, I want Ctrl+Z to undo the last delete while settings has focus and capture is off, so that undo works from the keyboard.
32. As a user, I want the undo bar to disappear after the next non-delete edit, so that stale undo never resurrects pads I have since worked around.
33. As a user, I want Undo to restore the deleted pads with their labels, inputs, and geometry intact, so that undo is a true reversal.
34. As a user, I want the selection toolbar ("N selected · Delete · Delete row · Delete column · Clear") to appear only while pads are selected, so that the resting Keys page stays calm.
35. As a user, I want the search field directly above the table, so that it sits with the list it filters.
36. As a user, I want Record input, Add pad, Add row, and Add column in one row under the undo bar, so that adding and recording stay where they were.
37. As a user, I want the visual layout to highlight every selected pad, so that I can see a multi-selection at a glance.
38. As a user, I want the overlay to update immediately after a delete or undo, so that what I see on screen matches the table.

### Saving

39. As a user, I want every edit saved automatically, so that I never think about saving.
40. As a user, I want no Save layout button, so that there is nothing to forget.
41. As a user, I want every layout to have a name and a file from the moment it exists, so that "unsaved layout" is not a state I can be in.
42. As a user, I want deleting the current layout to switch me to the first layout in the list, so that I always land on something.
43. As a user, I want to be allowed to delete the last remaining layout, so that "delete everything" works as a reset.
44. As a user, I want the app to re-seed the bundled default layout when no layouts exist on disk, so that first run and "deleted everything" behave the same.
45. As a user, I want a remembered layout name that no longer exists on disk to fall back to the first layout (or the re-seed rule), so that a missing file never breaks startup.
46. As a user, I want `config.json` to hold only globals (hotkeys, theme, current layout name), so that one layout never has two copies on disk.
47. As a user upgrading, I want an old `config.json` that still carries layout data to be migrated once into a layout named "Recovered" when no layouts exist, so that nothing I had is lost.
48. As a user upgrading, I want that stale layout data dropped when layouts already exist, so that a stale copy never shadows a real layout.
49. As a user, I want the word "layout" everywhere I read (UI, README, Help), so that "profile" never appears in the interface.

### Creating, naming, and managing layouts

50. As a user, I want a new layout from a template to be written to disk immediately, so that it autosaves from its first second.
51. As a user, I want a new layout to keep my current colors, position, and opacity, so that only the pads change.
52. As a user, I want a blank name on Create to fall back to the suggested template name, so that I can just press Create.
53. As a user, I want creating a layout with a taken name to auto-suffix it ("(2)", "(3)"), so that nothing is ever overwritten.
54. As a user, I want name comparison to be case-insensitive after trimming and stripping filename-illegal characters, so that "cyborg " and "Cyborg" count as one name, as the filesystem does.
55. As a user, I want a Rename layout action, so that I can fix an auto-suffixed or mistyped name.
56. As a user, I want renaming onto a taken name refused inline (OK disabled, hint shown), so that rename never merges two layouts.
57. As a user, I want Rename to update the remembered current layout, so that the app reopens the renamed layout next time.
58. As a user, I want a Duplicate layout action defaulting to "<name> copy" that switches to the copy, so that I can branch a layout safely.
59. As a user, I want Delete layout to keep its confirmation, so that a whole layout is never lost to a slip.

### Settings header and Appearance

60. As a user, I want the current layout's name shown as a large title in the header, so that I always know which layout I am editing.
61. As a user, I want to click the title to rename the layout, so that renaming is where the name is.
62. As a user, I want a chevron next to the title that opens the list of layouts, so that switching is one click.
63. As a user, I want the tagline "Every move. On display." shown under the title in the accent color, so that the header keeps its character without a second row.
64. As a user, I want Rename, Duplicate, Delete, and + New layout visible on the right of the header, so that nothing hides in a menu.
65. As a user, I want no "Changes save automatically" note, so that the header stays clean.
66. As a user, I want the Theme selector on the Appearance page in a "Settings window" card at the top, so that all look-and-feel choices live on one page.
67. As a user, I want the theme change to still apply immediately and persist, so that moving the control loses nothing.
68. As a user, I want the settings screenshot in the README and the Help page copy updated, so that the docs match the app.

## Implementation Decisions

### Vocabulary

- **Layout** in every user-facing string, README, Help page, tooltips, and
  dialog titles. The on-disk key `profile`, the `profiles/` folder, and existing
  function names stay for compatibility.

### Edit on screen entry and exit (overlay + settings + tray)

- New global hotkey `edit`, default `E`, stored beside `toggle`/`settings`/`quit`
  in the config's hotkeys map and editable in the Keyboard shortcuts card.
  `load_config` defaults it like the others.
- Edit mode has one owner: the overlay's `set_edit_mode`. The Layout page button,
  the tray item, and the hotkey all call into the same toggle and reflect the
  same state (button text, tray item checked state). The overlay emits a signal
  when edit mode changes so settings can sync the button without polling.
- Entering edit mode shows the overlay if hidden (existing button behaviour).
- Esc while the overlay has focus in edit mode ends it. Focus-loss ending stays
  exactly as today (`applicationStateChanged`).
- Hint bar text names the hotkey label and Esc.
- Lost-overlay rule in `apply()`: compute the overlay rect; if it intersects no
  screen's geometry, move it to the nearest point where it is at least partly
  visible (clamp so that a minimum of, say, 40 logical px of the window is on
  the nearest screen). Partial off-screen stays untouched.

### Selection model (settings Keys page)

- The pads table switches to extended selection. The visual layout keeps a set
  of selected pad indices, supports ctrl-click toggle and drag-box selection,
  and mirrors the table's selection both ways through one shared "selection"
  (a set of indices into the layout's pad list). Sticks are never part of it.
- Ctrl+A in the table selects visible (unfiltered) rows only.
- Delete key handling lives on the table and the visual layout; it is a no-op
  while capture is active.
- Selection toolbar widget above the search field: hidden when the selection is
  empty; shows count, Delete, Delete row, Delete column, Clear.
- Column / row membership rule (from the grilling, exact): pad B is in selected
  pad A's column when `A.col <= centre_x(B) < A.col + A.w` where
  `centre_x(B) = B.col + B.w / 2`; rows use `row`, `h`, and `centre_y`. The
  set for Delete row / Delete column is the union over every selected pad.
- Deleting removes entries from the layout's pad list without touching any
  other pad's coordinates.

### Undo

- Single-level, delete-only. The last delete stores the removed pads with their
  original indices. Undo reinserts them at those indices. Any non-delete edit
  (cell edit, add, capture, geometry, layout switch, layout delete) clears it.
- Surfaced as a full-width bar under the table ("Undo delete · N pads",
  Ctrl+Z hint) and a Ctrl+Z shortcut scoped to the settings window, inactive
  during capture.

### Layout invariant and persistence

- `config.json` carries only globals: hotkeys, theme, current layout name.
  `save_config` writes the current layout to its file and the globals to
  `config.json`; it no longer has an unnamed branch.
- `load_config`: read globals; pick the remembered layout if it exists, else the
  first listed; if none exist, re-seed the bundled default (the same seeding
  first run already does) and pick it. One-time migration: if the old
  `config.json` still carries layout keys and no layouts exist, write them as
  "Recovered" before the pick; otherwise drop them.
- Delete layout: switch to the first remaining layout; if none remain, apply the
  re-seed rule. The confirmation dialog stays.
- Remove the Save layout button, `_profile_save`, and the "unnamed edits stay
  temporary" copy everywhere (README, Help, tooltips).

### Names

- Canonical name key: trim, strip `\/:*?"<>|`, casefold. Uniqueness is checked
  against the canonical keys of existing layout files.
- Create: blank -> template suggestion; collision -> " (2)", " (3)", ...
- Rename: dialog prefilled with the current name; OK disabled with an inline
  hint while the canonical key collides with another layout; on OK, rename the
  file and update the remembered name.
- Duplicate: replaces "Save as new layout…"; default "<name> copy"; collision
  auto-suffixes; switches to the copy.
- New layouts inherit colors, position, and opacity from the current layout
  (unchanged).

### Settings header and Appearance page

- Header becomes one row: a title control showing the layout name (clicking
  opens Rename), a chevron control opening the layout list (replaces the combo
  as the switching affordance; keyboard-accessible), the tagline under the
  title in the accent color, and Rename / Duplicate / Delete / + New layout
  buttons on the right. No Save, no autosave note, no Theme.
- The Theme selector moves to the Appearance page in a "Settings window" card
  above Preview, with the helper text that overlay colors are set below.
  Behaviour (immediate apply, persisted globally) is unchanged.
- The design canvas sources under `design/` gain the chosen header and Keys
  page as their Screens artboards; the option artboards from the prototypes are
  dropped from the main canvas.

## Testing Decisions

- A good test drives the same surface the user does and asserts external
  behaviour: what the table shows, what the layout contains, what is on disk,
  where the overlay window is. It never asserts private attributes, timers, or
  call order.
- Seams (all existing):
  1. **Settings window seam**: build a real `SettingsWindow` around a stub
     overlay with temp `config.json` / `profiles/` (the `editor` fixture in the
     settings tests). Use it for selection, delete, undo, header actions, naming
     rules, layout switch/delete/re-seed, and the Theme move. Drive with QTest
     clicks, key presses, and `selectRow`/`setText`; assert on the layout dict
     and the profile files.
  2. **Overlay widget seam**: a real `Overlay` with listeners stubbed and a
     temp config (the `window` fixture in the overlay widget tests). Use it for
     hotkey/Esc/tray toggling of edit mode, the shared edit-state signal, and
     the lost-overlay pull-back (feed it screens through `QGuiApplication`
     geometry or a monkeypatched screen list).
  3. **Config function seam**: `load_config` / `save_config` / profile helpers
     against `tmp_path` (the overlay unit tests). Use it for the globals-only
     `config.json`, the "Recovered" migration, re-seeding, name canonicalisation,
     auto-suffixing, and rename/duplicate on disk.
- Prior art: `tests/test_settings_ui.py` (autosave, filter, capture, profile
  delete), `tests/test_overlay_widget.py` (synthetic drag, capture-on-click),
  `tests/test_overlay.py` (profile roundtrip, sanitised names, startup restore).
- Real-input checks (the debug harnesses) stay manual and out of the suite.
- Remove tests that encode the unnamed state
  (`test_unnamed_edits_are_not_saved_on_close`,
  `test_no_saved_layout_keeps_temporary_edits_out_of_config`) and replace them
  with the invariant's tests.

## Out of Scope

- Multi-monitor placement rules (single-monitor user; revisit as a new effort).
- Moving or resizing individual pads by dragging on the overlay.
- Row/column gutters on the visual layout (rejected: fractional keyboard grids).
- Undo for anything other than pad deletion.
- Transient "Saved" feedback of any kind.
- Merging layouts on rename collision.
- Changing how sticks are added, edited, or removed.

## Further Notes

- Facts measured on the user's screen (2560x1440 logical at DPR 1.5): the
  overlay follows the cursor 1:1 to every corner and partially off-screen, no
  snap-back from the keep-on-top tick or from `apply()`, and position survives
  Done editing and restart. Reach needs no work; entry does.
- Prototype sources (throwaway) live in `design/gen.py` as `bulk_*`,
  `header_*`, `appearance_page_final`, `sidebar_brand`, with generated
  `Bulk*.dc.html`, `Header*.dc.html`, `AppearanceFinal.dc.html`, and canvas
  pages 5 and 6. Fold the chosen designs into the Screens page and drop the
  rest when implementing.
- Two earlier decisions were overridden by the header prototype reaction: the
  static "Changes save automatically" note (dropped) and the Theme selector's
  place in the header (moved to Appearance).

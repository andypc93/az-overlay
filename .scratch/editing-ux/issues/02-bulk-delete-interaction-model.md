# Bulk delete: pads, rows, columns

Type: grilling
Status: resolved

## Question

Today the pads table is single-select and **Remove** deletes one pad; there is no
row or column delete. Decide the interaction model:

1. **Selection**: multi-select in the table (Ctrl/Shift click, Ctrl+A) and/or in the
   visual layout (`PadLayoutEditor`: ctrl-click, drag a box). Does selecting in one
   mirror the other?
2. **Row/column delete**: a) explicit **Delete row** / **Delete column** buttons that
   act on the row/column of the current selection; b) clickable row/column gutters
   in the visual layout; c) both.
3. **Semantics**: deleting a column removes every pad whose `col` range intersects
   it. Do remaining pads to the right shift left (close the gap) or stay put?
   Same for rows. What happens to sticks occupying that row/column?
4. **Safety**: confirmation dialog for multi-delete, or rely on undo (see fog) /
   autosave + duplicate layout?

Recommended: table multi-select mirrored to the visual layout; Delete row/column
buttons next to Add row/Add column acting on the selected pads' rows/columns; no
shift (keep coordinates stable, matching Add row/column which never shifts); no
confirmation but a single-level undo (tracked in fog until this resolves).

## Comments

### Round 1 (2026-09-12, user confirmed every recommendation)

1. Column/row = pads whose span overlaps the selected pad's span on that axis (a).
2. Multi-select in both the table and the visual layout, mirrored.
3. Delete row / Delete column buttons beside Add row / Add column; no gutters.
4. Remaining pads stay put; no shifting.
5. Sticks untouched by row/column delete.
6. Single-level Undo, no confirmation dialog.
7. Delete key removes the selection unless Record input capture is active.

Round 2 open: overlap threshold (stagger and wide pads), undo scope and trigger,
Ctrl+A under a search filter, Delete key in the visual layout.

### Round 2 (2026-09-12, user confirmed every recommendation)

1. Overlap rule sharpened: a pad belongs to the selected pad's column when its
   horizontal centre lies inside the selected pad's span (same for rows, vertical).
2. Undo covers deletes only: Remove, Delete row, Delete column, Delete key.
3. Undo via both a button ("Undo delete · N pads", visible until the next
   non-delete edit) and Ctrl+Z; Ctrl+Z ignored while Record input capture runs.
4. Ctrl+A under an active search filter selects visible pads only.
5. Delete key in the visual layout behaves exactly as in the table.

## Answer

**Selection.** Pads can be multi-selected in the pads table (Ctrl/Shift-click,
Ctrl+A) and in the visual layout (Ctrl-click toggle, drag a box). The two surfaces
show one shared selection. Ctrl+A selects only pads visible under the current search
filter.

**Deleting.** Three actions remove the selected pads and nothing else:
- **Remove** button and the **Delete** key (table or visual layout focused) delete
  the selection.
- **Delete row** / **Delete column** buttons, placed beside Add row / Add column,
  delete every pad in the row/column of each selected pad.
- The Delete key is swallowed while **Record input** capture is active.

**Column / row rule.** Pad B is in selected pad A's column when B's horizontal centre
lies within A's horizontal span `[col, col + w)`. Rows use the vertical centre and
`[row, row + h)`. Wide pads therefore sweep their full span (the user chose them);
staggered keyboard keys are not caught by quarter-unit overlaps.

**No relayout.** Remaining pads keep their coordinates; gaps stay. Sticks are never
touched by pad deletion.

**Undo.** Single-level, deletes only. Surfaced as an **Undo delete · N pads** button
that appears after a delete and disappears after the next non-delete edit, plus
Ctrl+Z (inactive during capture). No confirmation dialogs anywhere.

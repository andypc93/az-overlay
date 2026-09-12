# 14: Undo delete

Spec: ../spec.md

**What to build:** Every pad deletion (Remove, Delete key, Delete row, Delete column) can be undone once. After a delete, a full-width "Undo delete / N pads" bar with a Ctrl+Z hint appears under the table; clicking it or pressing Ctrl+Z (while settings has focus and capture is off) restores the pads with their labels, inputs, and geometry at their original positions in the list. Any non-delete edit (cell edit, add, capture, geometry change, layout switch or delete) clears the undo and hides the bar. Single level only.

**Blocked by:** 13 (Delete row and Delete column)

**Status:** ready-for-agent

- [ ] After Remove, Delete key, Delete row, or Delete column, the undo bar shows the deleted count.
- [ ] Undo (bar or Ctrl+Z) restores the exact pads at their original indices; the overlay and table reflect it.
- [ ] A second undo does nothing (single level).
- [ ] Ctrl+Z during capture does nothing.
- [ ] Any non-delete edit hides the bar and discards the undo.
- [ ] Covered at the settings-window seam.

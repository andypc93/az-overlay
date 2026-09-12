# 12: Select many pads

Spec: ../spec.md

**What to build:** On the Keys page, pads can be multi-selected: ctrl-click, shift-click, and Ctrl+A in the table; ctrl-click and drag-box on the visual layout. Both surfaces show one shared selection; sticks are never part of it. Ctrl+A selects only pads visible under the current search filter. Remove deletes every selected pad and shows the count; the Delete key does the same when the table or the visual layout has focus, but is ignored while Record input capture is active. A selection toolbar ("N selected / Delete / Delete row / Delete column / Clear") appears above the search field only while pads are selected; Delete row and Delete column are placeholders here and become live in ticket 13. The search field sits directly above the table. Remaining pads keep their coordinates. The overlay updates immediately.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Ctrl-click and shift-click select several rows; the visual layout highlights the same pads.
- [ ] Ctrl-click and a drag-box on the visual layout change the selection and the table follows.
- [ ] Ctrl+A with a search filter active selects only matching pads.
- [ ] Remove shows the count ("Remove 3 pads") and deletes exactly the selection; other pads keep their positions; sticks untouched.
- [ ] Delete key deletes the selection from the table or the visual layout; during capture it does nothing.
- [ ] Selection toolbar is hidden with an empty selection and visible with one; Clear empties the selection.
- [ ] Search field sits directly above the table (per the chosen mockup on the Keys page canvas, "Chosen" page).
- [ ] No confirmation dialog on delete.
- [ ] Covered at the settings-window seam.

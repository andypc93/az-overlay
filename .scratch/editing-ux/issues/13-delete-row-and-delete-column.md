# 13: Delete row and Delete column

Spec: ../spec.md

**What to build:** Delete row and Delete column buttons sit beside Add row / Add column (and in the selection toolbar) and remove every pad in the row or column of each selected pad. Membership uses the centre-in-span rule from the grilling: pad B is in selected pad A's column when `A.col <= B.col + B.w / 2 < A.col + A.w`; rows use `row`, `h`, and the vertical centre. The result is the union over every selected pad. Remaining pads keep their coordinates; sticks are never touched; no confirmation dialog.

**Blocked by:** 12 (Select many pads)

**Status:** ready-for-agent

- [ ] With one pad selected, Delete column removes every pad whose horizontal centre lies within that pad's span, and nothing else.
- [ ] On a staggered keyboard layout, a quarter-unit overlap does not count: only centre-in-span pads go.
- [ ] A wide pad (space bar) selected sweeps its full span.
- [ ] With pads in two columns selected, Delete column removes both columns.
- [ ] Delete row behaves symmetrically.
- [ ] Sticks in the deleted row or column remain; remaining pads do not shift.
- [ ] Buttons are disabled with an empty selection.
- [ ] Covered at the settings-window seam with a keyboard template and an Azeron template.

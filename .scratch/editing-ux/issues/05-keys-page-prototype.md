# Prototype: Keys page with multi-select and row/column delete

Type: prototype
Status: resolved
Blocked by: 02

## Question

Produce a cheap, reactable mockup of the Keys page implementing the model chosen in
ticket 02 (selection in table + visual layout, Delete row / Delete column controls,
any confirmation or undo affordance). Use the design canvas sources in `design/`
(`gen.py`, `canvas.json`) so it sits next to the existing mockups. Link the asset
here; resolve when the user has reacted and the layout is settled.

## Comments

### Prototype published (2026-09-12)

Asset: https://claude.ai/code/artifact/f1218af6-0d38-4db9-98ff-7c71c4aeb252
Source: `design/gen.py` (`BULK_OPTIONS`, functions `bulk_a`/`bulk_b`/`bulk_c`),
emitted as `design/BulkA.dc.html`, `BulkB.dc.html`, `BulkC.dc.html` and page-5
"Bulk delete (prototype)" of `design/canvas.json`. Throwaway: remove once one wins.

- Option A · Buttons row: today's page; Remove counts the selection, Delete row /
  Delete column sit beside Add row / Add column; Undo bar under the table.
- Option B · Selection toolbar: delete actions exist only while pads are selected;
  Add controls stay quiet at the bottom.
- Option C · Visual first: large layout with a drag-box, actions in a side rail,
  table demoted to a compact list.

Waiting on the user's reaction (which option, or which pieces from each).

### Decision (2026-09-12)

User: "B's toolbar with A's undo bar. Search bar goes under B toolbar since search
bar is to look for things in the label list."

## Answer

Winning Keys page, top to bottom inside the Pads card:

1. Show all pads switch, then the visual layout (selection highlighted).
2. **Selection toolbar** (from Option B): visible only while pads are selected.
   "N selected · Delete · Delete row · Delete column · Clear".
3. **Search** field, directly above the table: it filters the label list, so it
   sits with the table, not with the layout.
4. Pads table.
5. **Undo bar** (from Option A): full width under the table, "Undo delete · N pads
   · Ctrl+Z", shown after a delete until the next non-delete edit.
6. Record input · Add pad · Add row · Add column row, then Edit position & size.

Canvas: https://claude.ai/code/artifact/f1218af6-0d38-4db9-98ff-7c71c4aeb252
("Chosen" page = final; "Options" page = A/B/C). Source `design/gen.py`
`bulk_final` -> `design/BulkFinal.dc.html`. Option C rejected (too much rework,
table loses room).

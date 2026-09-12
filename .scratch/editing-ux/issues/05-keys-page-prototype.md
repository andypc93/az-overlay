# Prototype: Keys page with multi-select and row/column delete

Type: prototype
Status: claimed
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

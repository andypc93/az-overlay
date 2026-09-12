# Prototype: settings header without a Save button

Type: prototype
Status: resolved
Blocked by: 03, 04

## Question

Mock the settings header once **Save layout** is gone: layout selector plus
New / Duplicate / Rename / Delete as decided in 03 and 04, and an "autosaved"
indicator if one is wanted. Reuse `design/` canvas sources; link the asset here.

## Comments

### Prototype published (2026-09-12)

Asset: https://claude.ai/code/artifact/b77b82b1-8362-413a-ac15-64afc1d2a0f7
Source: `design/gen.py` (`HEADER_OPTIONS`, `header_a`/`header_b`/`header_c`),
emitted as `design/HeaderA.dc.html`, `HeaderB.dc.html`, `HeaderC.dc.html` and
page-6 "Header (prototype)" of `design/canvas.json`. Throwaway once one wins.

- Option A · More menu: today's row minus Save; Duplicate / Rename / Delete under
  More; "Changes save automatically." under the row.
- Option B · Actions in the row: Rename, Duplicate, Delete visible beside the
  selector; autosave note next to the tagline.
- Option C · Layout name as title: the name is a large title (click to rename,
  chevron to switch); Duplicate / Delete / New on the right; note under the title.

Waiting on the user's reaction.

### Round 2 (2026-09-12)

User: "mix B buttons with C big title (remove changes save automatically) and
place 'Every move. On display.' in a prettier way, 3 options again."

Same canvas, page "Round 2": D (uppercase accent eyebrow above the title, Theme
top right), E (tagline moves to a sidebar wordmark, header is one row), F (tagline
under the title in accent, one row). All three: Rename / Duplicate / Delete /
+ New layout visible, big layout name with chevron, no autosave note.
Source: `header_d`/`header_e`/`header_f`, `sidebar_brand` in `design/gen.py`.

### Decision (2026-09-12)

User: "C but move the theme switcher to Appearance." Read as the third option on
the Round 2 page (Option F, tagline under the title), the page in front of them.

## Answer

Header, one row:
- Left: the current layout's name as a large title (click to rename), a chevron
  that opens the layout list, and "Every move. On display." in accent under it.
- Right: **Rename · Duplicate · Delete (quiet) · + New layout (primary)**.
- No Save button, no autosave note (overrides the "static note" choice from
  "Remove the unnamed layout state": the user dropped it on seeing it).
- No Theme control in the header.

Theme selector moves to the **Appearance** page, in a new "Settings window" card
at the top ("Theme: Dark/Light", helper text: overlay colors are set below).

Canvas: https://claude.ai/code/artifact/b77b82b1-8362-413a-ac15-64afc1d2a0f7
("Chosen" page = header + Appearance; "Round 2" and "Round 1" pages keep the
options). Source `design/gen.py`: `header_final`, `appearance_page_final`.

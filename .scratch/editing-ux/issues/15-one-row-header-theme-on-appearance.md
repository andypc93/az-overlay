# 15: One-row header, Theme on Appearance

Spec: ../spec.md

**What to build:** The settings header becomes one row matching the chosen mockup (header canvas, "Chosen" page): the current layout's name as a large title (click opens Rename), a chevron that opens the layout list for switching, "Every move. On display." in the accent color under the title, and Rename / Duplicate / Delete / + New layout buttons on the right. No Save button, no autosave note, no Theme control in the header. The Theme selector moves to the Appearance page in a "Settings window" card above Preview, with helper text that overlay colors are set below; it still applies immediately and persists across restarts and layout changes.

**Blocked by:** 09 (Unique layout names, Rename, Duplicate)

**Status:** ready-for-agent

- [ ] Header shows the current layout name as the title and updates on switch, rename, duplicate, delete, and create.
- [ ] Clicking the title opens Rename; the chevron opens a list of layouts and selecting one switches to it (keyboard-accessible).
- [ ] Rename, Duplicate, Delete, and + New layout are visible buttons; Delete keeps its confirmation.
- [ ] No Save button, no "Changes save automatically" text, no Theme control in the header.
- [ ] Appearance page has a "Settings window" card with the Theme selector; changing it restyles immediately and survives restart and layout changes (existing theme tests adapted).
- [ ] Covered at the settings-window seam.

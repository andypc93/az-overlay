# Remove the unnamed layout state (no Save button)

Type: grilling
Status: resolved

## Question

Autosave already covers saved layouts. The only place edits are not persisted is
the **unnamed layout** state (`cfg["profile"] == ""`), reached after deleting the
current layout or when `profiles/` is empty, and the **Save layout** button exists
only to exit that state. Removing the button means removing the state. Decide:

1. **Invariant**: every layout always has a name and a file. Confirm.
2. **Startup with no profiles**: auto-create a layout from the bundled
   `config.json` (name it "Default"?) or open the New layout dialog?
3. **Deleting the current layout**: switch to the next saved layout; if none
   remain, apply rule 2.
4. **Canonical term**: README says "layout", code says "profile". Pick one for UI
   copy, docs, and `CONTEXT.md` (create it when this resolves).

Recommended: yes to the invariant; auto-create "Default" on empty; switch to the
alphabetically next layout on delete; canonical term **layout** in all user-facing
text, keep `profile` only as the on-disk key for compatibility.

## Comments

### Round 1 (2026-09-12, user confirmed every recommendation)

1y 2a 3c 4y 5layout 6a 7b. No round 2 needed.

## Answer

**Invariant.** A layout always has a name and a file under `profiles/` from the
moment it exists. There is no unnamed or memory-only layout. The **Save layout**
button is removed; every edit autosaves as today's named-layout path already does.

**Zero layouts on disk** (only reachable by deleting every layout): re-seed the
bundled "Cyborg 2 default", exactly as first run does. One rule for first run and
for "deleted everything".

**Deleting the current layout.** Switch to the first layout in the list. Deleting the
last remaining layout is allowed and behaves as a reset (re-seed rule above).
Startup with a remembered name that no longer exists follows the same two rules.

**Canonical word: layout.** Every user-facing string, README, Help page, and
`CONTEXT.md` say "layout". `profile` survives only as the on-disk key and the
`profiles/` folder name for compatibility.

**config.json holds globals only**: hotkeys, theme, current layout name. It no
longer carries a copy of layout data. One-time migration: if an old config.json
still carries layout keys and `profiles/` is empty, write them out as a layout
named "Recovered"; otherwise drop them.

**Autosave feedback.** A static muted line in the header, "Changes save
automatically". No transient "Saved" flashes.

# 08: Layouts always have a file

Spec: ../spec.md

**What to build:** There is no unnamed layout any more. Every layout has a name and a file from the moment it exists, so every edit autosaves and the Save layout button disappears. The global config holds only hotkeys, theme, and the current layout name. Starting the app with no layouts on disk re-seeds the bundled default, the same way first run does. Deleting the current layout switches to the first remaining layout; deleting the last one is allowed and re-seeds. An old config that still carries layout data is migrated once into a layout named "Recovered" when no layouts exist, and dropped otherwise. User-facing strings say "layout", never "profile".

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Saving writes the current layout to its own file and only globals (hotkeys, theme, current layout name) to the global config; no layout keys remain in the global config after a save.
- [ ] Startup with an empty layouts folder re-seeds the bundled default layout and selects it.
- [ ] Startup with a remembered layout name that no longer exists selects the first listed layout, or re-seeds when none exist.
- [ ] Startup with an old global config carrying layout keys and no layout files creates a "Recovered" layout from them; with layout files present, the stale keys are dropped.
- [ ] Deleting the current layout (after the existing confirmation) switches to the first remaining layout; deleting the last layout re-seeds the default.
- [ ] The Save layout button and the "unnamed edits stay temporary" copy (tooltips, Help page, README note) are gone.
- [ ] Tests encoding the unnamed state are replaced by tests of the invariant, driven through the config functions and the settings window against temp config and layout folders.

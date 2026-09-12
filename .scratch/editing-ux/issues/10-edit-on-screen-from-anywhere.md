# 10: Edit on screen from anywhere

Spec: ../spec.md

**What to build:** Edit on screen can be toggled without the settings window: a global hotkey (Ctrl+Alt+E by default, editable in the Keyboard shortcuts card like the other three) and a tray menu item named "Edit on screen". Entering edit mode shows the overlay if it was hidden. Esc while the overlay has focus ends edit mode, the hotkey toggles it, and it still ends automatically when the app loses focus. The Layout page button, the tray item, and the hotkey all reflect one shared state (button reads "Done editing" whenever edit mode is on, however it was entered). The on-overlay hint bar names the hotkey and Esc.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Global config has an `edit` hotkey defaulting to E, editable in the Keyboard shortcuts card, applied like the other hotkeys.
- [ ] Pressing the hotkey with the overlay hidden shows it and enters edit mode; pressing again leaves edit mode.
- [ ] Tray menu item "Edit on screen" toggles the same state and shows it as checked while on.
- [ ] Esc with the overlay focused in edit mode ends edit mode.
- [ ] Turning edit mode on by hotkey or tray flips the Layout page button to "Done editing"; turning it off by any route flips it back.
- [ ] Losing application focus still ends edit mode (existing behaviour and its regression harness stay valid).
- [ ] Hint bar text names the configured hotkey and Esc.
- [ ] Covered at the overlay-widget seam (real overlay, stubbed listeners) and the settings-window seam.

# Spec: release-1.0

Status: ready-for-plan
Decided: 2026-09-13 (grilling session)
Glossary: `CONTEXT.md` at the repo root

## Context

- Today only the author runs the app. First public release follows: unsigned exe on
  GitHub Releases, version 1.0.0, no installer, no code signing.
- The overlay serves the player on screen and stream viewers through OBS.
  Measured on 2026-09-13 with OBS 30.2.3: Display Capture shows the overlay;
  Window Capture cannot list the window (the `Qt.WindowType.Tool` flag at
  `overlay.py:666` makes it a tool window, which OBS skips); Game Capture never
  shows a separate window by design.
- Author hardware: one 4K monitor at 150% DPI. Target: correct placement and size on
  1080p and 1440p at any DPI, two monitors, drag across screens. Verification is by
  real resolution and DPI changes on the 4K, not env-var simulation.
- Ongoing work in four batches, in order. Each batch ships on its own.

## Batch 1: hardening

1. Crash log: `logging` to `<data folder>/az-overlay.log`, rotating; `sys.excepthook`
   writes the traceback there before exit.
2. Single instance: second launch raises the running instance's settings window and
   exits.
3. Corrupt `config.json`: copy it to `config.json.bak`, start with defaults, keep
   running, log it.
4. `__version__ = "1.0.0"` in code; shown on About; stamped into exe metadata by the
   PyInstaller spec. About gets a "Check for updates" link to the GitHub Releases
   page. No network call at startup.

## Batch 2: position model and monitors

5. Position is stored as an anchor plus fractions of the screen. Anchor is chosen
   automatically on drop: nearest corner or edge. Size is stored as a fraction of
   screen height. Old px config is migrated once, silently, using the current screen.
6. Precise position fields become: anchor dropdown, px offset from that corner on
   the current screen.
7. The overlay remembers its screen by name and falls back to the primary screen.
   Dragging across screens is allowed and re-anchors to the new screen. Pullback
   rule from `visible_position()` stays.
8. The settings window remembers size, position, screen, and last page.

## Batch 3: OBS stream window

9. "Stream window" toggle in the tray menu and on the Layout page. A plain titled
   window, "AZ-Overlay Stream": not topmost, not click-through, in the taskbar.
   Solid chroma background, default magenta `#FF00FF`, color is a global setting on
   Appearance. Drawn at scale 1.0 with the same scene and pressed states as the
   overlay. Remembers its own geometry.
10. README and Help: Window Capture + Color Key recipe, Display Capture as the
    alternative, Game Capture limitation stated plainly.

## Batch 4: release polish

11. "Start with Windows" toggle: registry `HKCU\...\Run` key, off by default, only
    offered when running as the packaged exe.
12. First run with no config: open settings landing on the New layout dialog.
13. Export layout and Import layout on the header layout menu (JSON file dialogs;
    import reuses the unique-name rule and switches to the imported layout).
    "Open layouts folder" tray item.
14. README: SmartScreen "More info -> Run anyway" with screenshot. Anti-cheat note
    stays in README and Help only, no first-run notice.
15. Tag `v1.0.0`, GitHub Release with `AZ-Overlay.exe` attached.

## Out of scope for 1.0

Code signing (revisit once strangers download), automatic update check, layout
cycle hotkey, per-game layout switching, fade duration setting, first-run
anti-cheat notice, browser-source overlay, visual pad geometry editing.

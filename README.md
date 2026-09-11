# az-overlay

Transparent, click-through, always-on-top overlay showing the Azeron Cyborg 2
button layout and highlighting keys as you press them. PySide6 (Qt) + one config file.

## Run

```bash
pip install -r requirements.txt
python overlay.py
```

`run.bat` does the same without a console window.

**No Python?** Run `build.bat` (needs `pip install pyinstaller`) and use
`distz-overlay.exe`, or grab the exe from the GitHub release. The exe keeps
its settings and saved layouts in `%APPDATA%z-overlay`, so replacing or
rebuilding the exe never erases them. Put a shortcut to it in
`shell:startup` if you want it at login.

## Settings GUI

A tray icon appears while running. Double-click it (or Ctrl+Alt+S) to open
Settings. Everything applies live and autosaves to `config.json`:

- **Layouts**: header saves/loads named layouts (`profiles/*.json` in the data
  folder). Ship one per game or Azeron profile.
- **Layout tab**: X/Y, scale, opacity, pad size. "Move / resize with mouse"
  makes the overlay solid and clickable: drag to move, scroll-wheel to resize,
  click a key then press the Cyborg button to rebind it, right-click to clear.
- **Keys**: table of pads (label, col, row). Select a row, hit "Capture key",
  press the Cyborg button: label set. Empty label = pad hidden (fully
  transparent). Thumbstick keys editable too.
- **Appearance**: live preview of an idle and a pressed key; font family, size, bold; fill, border and text color for idle and pressed states.

## Hotkeys (always Ctrl+Alt + key, editable)

| Keys         | Action            |
| ------------ | ----------------- |
| Ctrl+Alt+O   | Show / hide       |
| Ctrl+Alt+S   | Open settings     |
| Ctrl+Alt+Q   | Quit              |

## Config (`config.json`)

- `opacity` 0..1, `scale` (0.5 = half size), `x`/`y` screen position.
- `keys`: list of `{label, col, row}`. Label is what the Cyborg sends
  (`Q`, `9`, `Alt`, `Page Up`, `F1`, `Caps Lock`, ...). Empty label = unbound pad.
- `joystick`: 2x2 cell showing the thumbstick in keyboard mode with its four keys.
- `font`: family, size (pt at scale 1.0), bold.
- `colors` (idle_/pressed_ × fill/outline/text), `hotkeys` as named.

Edit the labels to match your Azeron profile. The default layout mirrors the
software's editor view.

## Limitations

- Works over borderless / windowed games. Exclusive fullscreen hides every
  overlay, including this one. Switch the game to borderless.
- Detects keyboard keys only. If the thumbstick is in analog (gamepad) mode
  it won't light up.
- Uses a global keyboard hook. Most anti-cheat is fine with this, but it is
  the same mechanism macro tools use, so check your game's rules.

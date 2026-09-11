# AZ-Overlay

Transparent, click-through, always-on-top overlay that shows your input device
and lights the buttons you press. Built-in templates:

- **Azeron Cyborg 2** (keys + analog thumbstick)
- **Keyboards**: 100%, 1800, 96%, 80% TKL, 75% exploded / compact, 65% exploded /
  compact, 60%, 50%, 40%, each in US (ANSI), UK, German, French, Spanish (ISO)
- **Xbox** and **PlayStation** controllers (analog sticks and triggers animate)

PySide6 (Qt) for drawing, pynput for the keyboard hook, pygame-ce (SDL) for controllers.

## Run

```bash
pip install -r requirements.txt
python overlay.py
```

`run.bat` does the same without a console window.

**No Python?** Run `build.bat` (needs `pip install pyinstaller`) and use
`dist\AZ-Overlay.exe`, or grab the exe from the GitHub release. The exe keeps
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
- **+ New layout**: pick a template (Azeron / keyboard form factor + language /
  Xbox / PlayStation). Creates a saved layout and switches to it.
- **Keys**: table of pads. *Label* is the text shown; *Input* is what lights
  it: a key (`F5`), several keys for a macro (`F5, F6`), a chord
  (`Ctrl+Shift+K`), a controller button (`gp:a`) or a physical key
  (`sc:0x1e`). Empty input = use the label. Select a row, hit "Capture key",
  press the button: input set. Empty label + empty input = pad hidden.
  Sticks / d-pads have their own table (WASD, analog, d-pad).
- **Appearance**: live preview of an idle and a pressed key; font family, size, bold; fill, border and text color for idle and pressed states.

## Hotkeys (always Ctrl+Alt + key, editable)

| Keys         | Action            |
| ------------ | ----------------- |
| Ctrl+Alt+O   | Show / hide       |
| Ctrl+Alt+S   | Open settings     |
| Ctrl+Alt+Q   | Quit              |

## Config (`config.json`)

- `opacity` 0..1, `scale` (0.5 = half size), `x`/`y` screen position.
- `keys`: list of `{label, input?, sc?, col, row, w, h, shape?, axis?}` in key units.
- `sticks`: list of `{label, col, row, w, h, up/down/left/right?, axes?, click?}`.
- `font`: family, size (pt at scale 1.0), bold.
- `colors` (idle_/pressed_ × fill/outline/text), `hotkeys` as named.

Edit the labels to match your Azeron profile. The default layout mirrors the
software's editor view.

## Limitations

- Works over borderless / windowed games. Exclusive fullscreen hides every
  overlay, including this one. Switch the game to borderless.
- Controllers are read through SDL; anything Windows sees as an Xbox or
  PlayStation pad works, including the Azeron thumbstick in analog mode.
- Uses a global keyboard hook. Most anti-cheat is fine with this, but it is
  the same mechanism macro tools use, so check your game's rules.

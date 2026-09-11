# az-overlay

Transparent, click-through, always-on-top overlay showing the Azeron Cyborg 2
button layout and highlighting keys as you press them. PySide6 (Qt) + one config file.

## Run

```bash
pip install -r requirements.txt
python overlay.py
```

`run.bat` does the same without a console window. Put a shortcut to it in
`shell:startup` if you want it at login.

## Hotkeys

| Keys         | Action            |
| ------------ | ----------------- |
| Ctrl+Alt+O   | Show / hide       |
| Ctrl+Alt+Q   | Quit              |

## Config (`config.json`)

- `opacity` 0..1, `scale` (0.5 = half size), `x`/`y` screen position.
- `keys`: list of `{label, col, row}`. Label is what the Cyborg sends
  (`Q`, `9`, `Alt`, `Page Up`, `F1`, `Caps Lock`, ...). Empty label = unbound pad.
- `joystick`: 2x2 cell showing the thumbstick in keyboard mode with its four keys.
- `colors`, `hotkeys` as named.

Edit the labels to match your Azeron profile. The default layout mirrors the
software's editor view.

## Limitations

- Works over borderless / windowed games. Exclusive fullscreen hides every
  overlay, including this one. Switch the game to borderless.
- Detects keyboard keys only. If the thumbstick is in analog (gamepad) mode
  it won't light up.
- Uses a global keyboard hook. Most anti-cheat is fine with this, but it is
  the same mechanism macro tools use, so check your game's rules.

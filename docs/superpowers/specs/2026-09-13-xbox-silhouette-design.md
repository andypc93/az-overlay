# Xbox controller silhouette and Elite paddles

Date: 2026-09-13. Approved design: mockup idea 1, "Outline body"
(https://claude.ai/code/artifact/926bf1f6-8f06-4cae-a312-d1be9de92c4d).

## Goal

The Xbox templates stop being a grid of pads and become one fixed drawing: a
controller body silhouette with the buttons at their real spots. The Elite
template adds a second silhouette, the back of the controller, carrying the
four paddles. Paddles are the only pads the user edits on the Elite; nothing
is editable on the plain Xbox layout except size, position, and appearance.

## Templates (`templates.py`)

- Device "Xbox controller" offers two templates: **Xbox Wireless** and
  **Xbox Elite Series 2**. `templates_for("Xbox controller")` returns both;
  `suggested_name` returns the template name.
- One builder `xbox_profile(elite=False)` produces both. Geometry comes from
  the approved mockup, expressed in a 400 x 372 unit frame and converted to
  col/row floats with `cell_w = cell_h = 20`, `gap = 0`, `scale = 0.8`. The
  col/row values exist only because the renderer places everything through
  `cell_rect`; they are never shown to the user.
- Front pads and their inputs: LT, RT (`gp:lefttrigger`, `gp:righttrigger`,
  with `axis`), LB, RB, Xbox button (`gp:guide`, circle), View, Menu,
  Share (`gp:misc1`) on the Wireless or Profile (unbound, `input: ""`) on the
  Elite, Y X B A circles, left stick, d-pad, right stick. Sticks keep the
  existing stick spec (`axes`, `click`, `w`, `h`).
- Profile flags: `"locked": true`, `"stick_box": false`.
- `decor`: `{"kind": "xbox_front", col, row, w, h}` for the body. The Elite
  adds `{"kind": "xbox_back", ...}` placed to the right of the front body with
  a gap of one body-eighth, and four paddle pads inside it:
  P1, P2 with `shape: "paddle_l"`, P3, P4 with `shape: "paddle_r"`, inputs
  `gp:paddle1` .. `gp:paddle4`, and `"editable": true`.
- The PlayStation template is untouched and still uses `_controller`.

## Paddle inputs (`gamepad.py`, `overlay.py`)

- `BUTTONS` gains `paddle1` .. `paddle4` mapped to
  `CONTROLLER_BUTTON_PADDLE1` .. `PADDLE4`. The existing `hasattr` guard
  skips them on a pygame without those constants.
- `GAMEPAD_LABELS` gains `gp:paddle1` .. `gp:paddle4` with labels P1 .. P4,
  so `parse_input` accepts them and the Keys page can record them.
- README documents the real-world catch: when the Xbox Accessories app maps a
  paddle to a face button, Windows reports only that button. Record the
  mapped button on the paddle pad instead.

## Locked layouts (`settings_ui.py`, `overlay.py`)

A profile with `"locked": true`:

- Keys page hides the Col, Row, W, H columns of both tables and disables
  Add key, Add stick, Remove, Delete row, Delete column. The pad layout
  picture still shows and selects pads.
- Only pads with `"editable": true` accept Label edits and Record input;
  every other row is read-only (no editable cells, Record input disabled when
  such a row is selected). On the Wireless template every row is read-only.
- Layout page hides the Key dimensions group. Size, Opacity, position, and
  Appearance all still apply.
- Edit on screen: drag and wheel work as before; clicking a pad starts a
  rebind only when that pad is editable.
- Undo of deletions never applies because deletions are disabled.

Existing profiles without the flag behave exactly as today.

## Drawing (`overlay.py`)

- `decor_path` gains `"xbox_front"` and `"xbox_back"`. Both scale one body
  path, authored in the 400 x 372 unit frame, into the decor rect. The back
  path adds four faint rounded rectangles where the triggers and bumpers sit
  so the back reads as the same object flipped over. Decor paint stays as it
  is: idle fill, outline at alpha 120, width 1.2.
- `shape_path` gains `"paddle_l"` and `"paddle_r"`: a pill (radius = half
  width) rotated -18 or +18 degrees about the rect centre.
  `key_text_rect` uses the rect centre for these shapes; `TEXT_SHAPES`
  handling is unchanged.
- `design/gen.py` adds an Xbox board built from the real template through
  `decor_path` and `shape_path`, the same way `mouse_board` does, and the
  README gains a screenshot of the Elite layout.

## Tests

- Both Xbox templates build; every front pad rect lies inside the front body
  rect; every paddle lies inside the back body rect; no two pads overlap.
- `parse_input("gp:paddle1")` works; `gamepad.BUTTONS` has the four paddles.
- A locked profile hides the position columns, disables the add and delete
  buttons, and leaves Record input enabled only on editable pads.
- `decor_path("xbox_front", rect)` and `("xbox_back", rect)` return non-empty
  paths bounded by the rect; `shape_path` with a paddle shape returns a
  rotated pill whose bounds stay near the rect.
- The overlay window builds the Elite profile and its width covers the back
  body.

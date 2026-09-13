# Xbox Silhouette and Elite Paddles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the grid-based Xbox template with a fixed controller drawing (body silhouette + buttons at their real spots), add an Elite template with a back silhouette carrying four paddles, and make paddles the only editable pads on locked layouts.

**Architecture:** Templates stay plain dicts placed through `cell_rect`, so the renderer is untouched apart from two new decor kinds and two new pad shapes in `overlay.py`. A `locked` profile flag makes the settings window hide geometry and block structural edits; `editable` on a pad opens Label / Record input for that pad only. Paddle buttons come from SDL through the existing `gamepad.BUTTONS` table.

**Tech Stack:** Python 3.14, PySide6 (QPainterPath, QTableWidget), pygame-ce for SDL game controllers, pytest.

**Spec:** `docs/superpowers/specs/2026-09-13-xbox-silhouette-design.md`

## Global Constraints

- Run tests with `python -m pytest -q` from `C:\dev\az-overlay`. All existing tests must keep passing.
- Unit frame for all Xbox geometry: 400 x 372, `cell_w = cell_h = 20`, `gap = 0`, `scale = 0.8`. col = x / 20, row = y / 20.
- Decor paint stays as it is in `Overlay._paint_scene`: idle fill, outline alpha 120, width 1.2.
- Existing profiles without `locked` behave exactly as today.
- PlayStation template is untouched.
- Commit messages end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

---

### Task 1: Paddle inputs

**Files:**
- Modify: `gamepad.py:27-38` (BUTTONS)
- Modify: `overlay.py:140-146` (GAMEPAD_LABELS)
- Test: `tests/test_overlay.py`

**Interfaces:**
- Produces: tokens `"gp:paddle1"` .. `"gp:paddle4"` accepted by `overlay.parse_input`; labels `"P1"` .. `"P4"` in `overlay.GAMEPAD_LABELS`; keys `"paddle1"` .. `"paddle4"` in `gamepad.BUTTONS`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_overlay.py`:

```python
def test_elite_paddles_are_controller_inputs():
    import gamepad
    for n in range(1, 5):
        assert overlay.input_matches(overlay.parse_input(f"gp:paddle{n}"), {f"gp:paddle{n}"})
        assert overlay.GAMEPAD_LABELS[f"gp:paddle{n}"] == f"P{n}"
        assert gamepad.BUTTONS[f"paddle{n}"] == f"CONTROLLER_BUTTON_PADDLE{n}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_overlay.py::test_elite_paddles_are_controller_inputs -q`
Expected: FAIL with `ValueError: Unknown controller input: 'gp:paddle1'`

- [ ] **Step 3: Add the paddles**

In `gamepad.py`, inside `BUTTONS` after the `"misc1"` / `"touchpad"` line:

```python
    "paddle1": "CONTROLLER_BUTTON_PADDLE1", "paddle2": "CONTROLLER_BUTTON_PADDLE2",
    "paddle3": "CONTROLLER_BUTTON_PADDLE3", "paddle4": "CONTROLLER_BUTTON_PADDLE4",
```

Also extend the module docstring line 7 list of button names with `paddle1 paddle2 paddle3 paddle4`.

In `overlay.py`, inside `GAMEPAD_LABELS` after the `"gp:righttrigger": "RT",` line:

```python
    "gp:paddle1": "P1", "gp:paddle2": "P2", "gp:paddle3": "P3", "gp:paddle4": "P4",
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_overlay.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add gamepad.py overlay.py tests/test_overlay.py
git commit -m "Controller paddles P1 to P4 as inputs

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Xbox body decor and paddle pad shapes

**Files:**
- Modify: `overlay.py:539-557` (`decor_path`), `overlay.py:525-537` (`shape_path`), `overlay.py:463-472` (`key_text_rect`)
- Test: `tests/test_xbox_templates.py` (create)

**Interfaces:**
- Produces: `decor_path("xbox_front", rect)` and `decor_path("xbox_back", rect)` return a `QPainterPath` scaled into `rect`; `shape_path(rect, "paddle_l", radius)` / `"paddle_r"` return a rotated pill; `key_text_rect(rect, "paddle_l")` returns a centred square.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_xbox_templates.py`:

```python
"""Xbox Wireless and Elite templates: fixed drawing, back silhouette, paddles."""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

import overlay


@pytest.fixture(autouse=True)
def _app():
    QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", ["xbox_front", "xbox_back"])
def test_xbox_decor_paths_fill_their_rect(kind):
    rect = QRectF(10, 20, 400, 372)
    path = overlay.decor_path(kind, rect)
    box = path.boundingRect()
    assert not path.isEmpty()
    assert rect.contains(box)
    assert box.width() > rect.width() * 0.9 and box.height() > rect.height() * 0.75


def test_back_decor_carries_trigger_ghosts():
    rect = QRectF(0, 0, 400, 372)
    front = overlay.decor_path("xbox_front", rect)
    back = overlay.decor_path("xbox_back", rect)
    assert back.elementCount() > front.elementCount()
    assert back.boundingRect().top() < front.boundingRect().top()  # ghosts sit above the body


@pytest.mark.parametrize("shape, sign", [("paddle_l", -1), ("paddle_r", 1)])
def test_paddle_shapes_are_tilted_pills(shape, sign):
    rect = QRectF(100, 100, 20, 70)
    path = overlay.shape_path(rect, shape, 4)
    box = path.boundingRect()
    assert box.width() > rect.width() + 10  # tilted, so wider than the upright pill
    assert abs(box.center().x() - rect.center().x()) < 0.5
    assert abs(box.center().y() - rect.center().y()) < 0.5
    top = min((path.elementAt(i) for i in range(path.elementCount())), key=lambda e: e.y)
    assert (top.x - rect.center().x()) * sign > 0  # top end leans away from the crotch
    text = overlay.key_text_rect(rect, shape)
    assert rect.contains(text) and text.center() == rect.center()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_xbox_templates.py -q`
Expected: FAIL. `decor_path` falls through to `addRoundedRect` (bounding box equals the rect, back has same element count), `shape_path` returns an upright rounded rect.

- [ ] **Step 3: Implement the drawing**

In `overlay.py` add above `decor_path` (after `shape_path`):

```python
# Xbox body outline, authored in a 400 x 372 unit frame (see docs/superpowers/specs/2026-09-13-xbox-silhouette-design.md).
XBOX_BODY = [
    ("M", (88, 88)),
    ("C", (130, 58), (270, 58), (312, 88)),      # top edge
    ("C", (350, 100), (372, 130), (380, 172)),   # right shoulder
    ("C", (392, 230), (372, 300), (352, 340)),   # right grip, outer
    ("C", (340, 362), (300, 362), (288, 340)),   # right grip, bottom
    ("C", (272, 312), (262, 284), (250, 258)),   # right grip, inner
    ("C", (236, 240), (164, 240), (150, 258)),   # crotch
    ("C", (138, 284), (128, 312), (112, 340)),   # left grip, inner
    ("C", (100, 362), (60, 362), (48, 340)),     # left grip, bottom
    ("C", (28, 300), (8, 230), (20, 172)),       # left grip, outer
    ("C", (28, 130), (50, 100), (88, 88)),       # left shoulder
]
XBOX_FRAME = (400.0, 372.0)
XBOX_BACK_GHOSTS = [(70, 30, 64, 22), (266, 30, 64, 22), (70, 60, 64, 18), (266, 60, 64, 18)]  # triggers, bumpers


def _xbox_body(rect):
    sx, sy = rect.width() / XBOX_FRAME[0], rect.height() / XBOX_FRAME[1]
    def pt(p):
        return QPointF(rect.x() + p[0] * sx, rect.y() + p[1] * sy)
    path = QPainterPath()
    for op, *pts in XBOX_BODY:
        if op == "M":
            path.moveTo(pt(pts[0]))
        else:
            path.cubicTo(pt(pts[0]), pt(pts[1]), pt(pts[2]))
    path.closeSubpath()
    return path, sx, sy
```

Replace the body of `decor_path` with:

```python
def decor_path(kind, rect):
    """Silhouette drawn behind the pads. "mouse": domed top, straight flanks, rounded tail.
    "xbox_front" / "xbox_back": the controller body; the back adds faint trigger and bumper ghosts."""
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    path = QPainterPath()
    if kind == "mouse":
        top, rb = h * 0.232, w * 0.42
        path.moveTo(x, y + top)
        path.arcTo(x, y, w, 2 * top, 180, -180)
        path.lineTo(x + w, y + h - rb)
        path.arcTo(x + w - 2 * rb, y + h - 2 * rb, 2 * rb, 2 * rb, 0, -90)
        path.lineTo(x + rb, y + h)
        path.arcTo(x, y + h - 2 * rb, 2 * rb, 2 * rb, 270, -90)
        path.closeSubpath()
    elif kind in ("xbox_front", "xbox_back"):
        path, sx, sy = _xbox_body(rect)
        if kind == "xbox_back":
            for gx, gy, gw, gh in XBOX_BACK_GHOSTS:
                path.addRoundedRect(QRectF(x + gx * sx, y + gy * sy, gw * sx, gh * sy), 6 * sx, 6 * sy)
    else:
        path.addRoundedRect(rect, w * 0.1, w * 0.1)
    return path
```

In `shape_path`, add a branch before the final `else`:

```python
    elif shape in ("paddle_l", "paddle_r"):  # pill tilted 18° away from the controller's centre line
        r = min(rect.width(), rect.height()) / 2
        pill = QPainterPath()
        pill.addRoundedRect(rect, r, r)
        t = QTransform().translate(rect.center().x(), rect.center().y()).rotate(-18 if shape == "paddle_l" else 18)
        t.translate(-rect.center().x(), -rect.center().y())
        path = t.map(pill)
```

Check `QTransform` is imported from `PySide6.QtGui` at the top of `overlay.py`; add it if missing.

In `key_text_rect`, after the `mouse_` branch add:

```python
    if shape in ("paddle_l", "paddle_r"):  # label sits in the pill's waist
        side = min(area.width(), area.height())
        return QRectF(area.center().x() - side / 2, area.center().y() - side / 2, side, side)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_xbox_templates.py tests/test_mouse_templates.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add overlay.py tests/test_xbox_templates.py
git commit -m "Xbox body silhouette and tilted paddle pad shapes

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Xbox Wireless and Elite templates

**Files:**
- Modify: `templates.py:382-431` (controller section), `templates.py:478-518` (catalogue)
- Modify: `overlay.py:69-70` (PROFILE_KEYS), `overlay.py:277-278` (config defaults)
- Test: `tests/test_xbox_templates.py`

**Interfaces:**
- Consumes: decor kinds `"xbox_front"`, `"xbox_back"`, shapes `"paddle_l"`, `"paddle_r"` (Task 2); tokens `gp:paddle1..4` (Task 1).
- Produces: `templates.XBOX_TEMPLATES = ["Xbox Wireless", "Xbox Elite Series 2"]`; `templates.xbox_profile(elite: bool) -> dict`; profile keys `"locked": bool` and per-pad `"editable": bool`; `overlay.PROFILE_KEYS` includes `"locked"`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_xbox_templates.py`:

```python
import templates
from tests.test_stick_styles import window  # noqa: F401  (fixture)


def _rect(k, default=1):
    return QRectF(k["col"], k["row"], k.get("w", default), k.get("h", default))


def test_xbox_device_offers_wireless_and_elite():
    assert templates.templates_for("Xbox controller") == ["Xbox Wireless", "Xbox Elite Series 2"]
    assert templates.suggested_name("Xbox controller", "Xbox Elite Series 2") == "Xbox Elite Series 2"
    assert templates.build("Xbox controller") == templates.xbox_profile(False)
    assert templates.build("Xbox controller", "Xbox Elite Series 2") == templates.xbox_profile(True)


@pytest.mark.parametrize("elite", [False, True])
def test_xbox_templates_are_locked_fixed_drawings(elite):
    prof = templates.xbox_profile(elite)
    assert prof["locked"] is True and prof["stick_box"] is False
    assert prof["decor"][0]["kind"] == "xbox_front"
    front = _rect(prof["decor"][0])
    for k in prof["keys"]:
        if k.get("shape", "").startswith("paddle"):
            continue
        assert front.contains(_rect(k)), k["label"]
        overlay.pad_inputs(k)  # must not raise
    for st in prof["sticks"]:
        assert front.contains(_rect(st, 2)), st["label"]
    labels = {k["label"] for k in prof["keys"]}
    assert {"LT", "RT", "LB", "RB", "View", "Menu", "Y", "X", "B", "A"} <= labels
    assert ("Profile" in labels) == elite and ("Share" in labels) != elite


def test_elite_back_body_holds_four_editable_paddles():
    prof = templates.xbox_profile(True)
    back = [d for d in prof["decor"] if d["kind"] == "xbox_back"]
    assert len(back) == 1
    back_rect = _rect(back[0])
    front_rect = _rect(prof["decor"][0])
    assert back_rect.left() > front_rect.right()
    paddles = [k for k in prof["keys"] if k.get("shape", "").startswith("paddle")]
    assert [k["label"] for k in paddles] == ["P1", "P2", "P3", "P4"]
    assert [k["input"] for k in paddles] == [f"gp:paddle{n}" for n in range(1, 5)]
    assert all(k["editable"] for k in paddles) and all(back_rect.contains(_rect(k)) for k in paddles)
    assert not any(k.get("editable") for k in prof["keys"] if k not in paddles)
    assert not any(k.get("editable") for k in templates.xbox_profile(False)["keys"])


@pytest.mark.parametrize("elite", [False, True])
def test_xbox_pads_do_not_overlap(elite):
    prof = templates.xbox_profile(elite)
    rects = [_rect(k) for k in prof["keys"]] + [_rect(s, 2) for s in prof["sticks"]]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.intersects(b.adjusted(0.01, 0.01, -0.01, -0.01))


def test_locked_travels_with_the_profile():
    assert "locked" in overlay.PROFILE_KEYS


def test_elite_paints_and_covers_the_back_body(window):  # noqa: F811
    window.cfg.update(templates.xbox_profile(True))
    window.apply()
    kinds = [kind for kind, _r in window.decor]
    assert kinds == ["xbox_front", "xbox_back"]
    assert window.width() >= window.decor[1][1].right()
    window.grab()  # paints every pad, paddle, and both silhouettes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_xbox_templates.py -q`
Expected: FAIL with `AttributeError: module 'templates' has no attribute 'xbox_profile'` and `templates_for` returning `["Xbox controller"]`.

- [ ] **Step 3: Write the templates**

In `templates.py`, after `PLAYSTATION = {...}` add:

```python
# ---- Xbox: a fixed drawing, not a grid ----------------------------------------
# Geometry from the approved mockup (docs/superpowers/specs/2026-09-13-xbox-silhouette-design.md),
# authored in a 400 x 372 unit frame at 20 units per cell. The col/row values only
# feed cell_rect; the layout is locked, so nobody edits them.
XBOX_TEMPLATES = ["Xbox Wireless", "Xbox Elite Series 2"]
XBOX_CELL = 20
XBOX_BACK_COL = 22.5  # the back body starts here: one body width plus a 50-unit gap


def _u(x, y, w, h, **extra):
    """A pad in unit coordinates -> cell coordinates."""
    d = {"col": round(x / XBOX_CELL, 3), "row": round(y / XBOX_CELL, 3),
         "w": round(w / XBOX_CELL, 3), "h": round(h / XBOX_CELL, 3)}
    d.update(extra)
    return d


def _circle(cx, cy, r, label, inp):
    return _u(cx - r, cy - r, 2 * r, 2 * r, label=label, shape="circle", input=inp)


def xbox_profile(elite=False):
    """Xbox Wireless, or Elite Series 2 with a second body for the four rear paddles."""
    keys = [
        _u(70, 30, 64, 22, label="LT", axis="gp:lefttrigger", input="gp:lefttrigger"),
        _u(266, 30, 64, 22, label="RT", axis="gp:righttrigger", input="gp:righttrigger"),
        _u(70, 60, 64, 18, label="LB", input="gp:leftshoulder"),
        _u(266, 60, 64, 18, label="RB", input="gp:rightshoulder"),
        _circle(200, 104, 17, "ⓧ", "gp:guide"),
        _u(150, 132, 28, 18, label="View", input="gp:back"),
        _u(222, 132, 28, 18, label="Menu", input="gp:start"),
        _u(184, 166, 32, 16, label="Profile", input="") if elite
        else _u(184, 166, 32, 16, label="Share", input="gp:misc1"),
        _circle(306, 100, 16, "Y", "gp:y"),
        _circle(276, 134, 16, "X", "gp:x"),
        _circle(336, 134, 16, "B", "gp:b"),
        _circle(306, 168, 16, "A", "gp:a"),
    ]
    sticks = [
        _u(60, 108, 64, 64, label="L", axes=["gp:leftx", "gp:lefty"], click="gp:leftstick"),
        _u(120, 180, 52, 52, label="", up="gp:dpup", down="gp:dpdown", left="gp:dpleft", right="gp:dpright"),
        _u(224, 174, 64, 64, label="R", axes=["gp:rightx", "gp:righty"], click="gp:rightstick"),
    ]
    decor = [_u(0, 0, 400, 372, kind="xbox_front")]
    if elite:
        bx = XBOX_BACK_COL * XBOX_CELL
        decor.append(_u(bx, 0, 400, 372, kind="xbox_back"))
        for label, cx, cy, w, h, shape in (("P1", 168, 268, 20, 70, "paddle_l"), ("P2", 128, 302, 18, 50, "paddle_l"),
                                           ("P3", 232, 268, 20, 70, "paddle_r"), ("P4", 272, 302, 18, 50, "paddle_r")):
            n = label[1]
            keys.append(_u(bx + cx - w / 2, cy - h / 2, w, h, label=label, shape=shape,
                           input=f"gp:paddle{n}", editable=True))
    return {
        "cell_w": XBOX_CELL, "cell_h": XBOX_CELL, "gap": 0, "scale": 0.8, "shape": "rect",
        "locked": True, "stick_box": False,
        "font": {"family": "Segoe UI", "size": 9, "bold": True},
        "keys": keys, "sticks": sticks, "decor": decor,
    }
```

Update the catalogue:

```python
def templates_for(device):
    if device == "Keyboard":
        return [name for name, _ in KEYBOARDS]
    if device == "Azeron":
        return [name for name, _ in AZERON_MODELS]
    if device == "Mouse":
        return [name for name, _ in MICE]
    if device == "Xbox controller":
        return list(XBOX_TEMPLATES)
    return [device]
```

In `build`, replace the Xbox line:

```python
    if device == "Xbox controller":
        return xbox_profile(elite=template == XBOX_TEMPLATES[1])
```

In `suggested_name`, before the final `return device`:

```python
    if device == "Xbox controller":
        return template or XBOX_TEMPLATES[0]
```

Update the `templates.py` module docstring (line 2) so it still describes the file; the XBOX name dict stays for `_controller` callers? No: `XBOX` is now unused. Delete `XBOX = {...}` and keep `PLAYSTATION`.

In `overlay.py` `PROFILE_KEYS` add `"locked"` after `"decor"`. Next to `cfg.setdefault("decor", [])` add:

```python
    cfg["locked"] = bool(cfg.get("locked", False))  # fixed drawing: geometry and structure are not edited
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_xbox_templates.py tests/test_settings_ui.py -q`
Expected: all PASS. If `test_xbox_pads_do_not_overlap` fails on the sticks, shrink the stick `w`/`h` to 3.0 cells (60 units) in `xbox_profile` and re-run.

- [ ] **Step 5: Commit**

```bash
git add templates.py overlay.py tests/test_xbox_templates.py
git commit -m "Xbox Wireless and Elite Series 2 templates as fixed drawings

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Locked layouts in settings

**Files:**
- Modify: `settings_ui.py:1156-1244` (`_layout_page`), `settings_ui.py:1246-1400` (`_keys_page`), `settings_ui.py:1789-1805` (`_pad_selection_changed`), `settings_ui.py:1819-1840` (`_fill_table`), `settings_ui.py:1984-1996` (`_fill_sticks`)
- Test: `tests/test_settings_ui.py`

**Interfaces:**
- Consumes: `cfg["locked"]`, per-pad `cfg["keys"][i]["editable"]` (Task 3).
- Produces: `SettingsWindow.locked -> bool` property; `SettingsWindow._pad_editable(index) -> bool`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_settings_ui.py`:

```python
def _load_xbox(editor, elite):
    editor.cfg.update(templates.build("Xbox controller", "Xbox Elite Series 2" if elite else "Xbox Wireless"))
    editor._rebuild_tabs()


def test_locked_layout_hides_geometry_and_structure(editor):
    _load_xbox(editor, elite=False)
    assert editor.locked
    assert all(editor.table.isColumnHidden(c) for c in (2, 3, 4, 5))
    assert all(editor.stick_table.isColumnHidden(c) for c in (5, 6, 7, 8))
    assert not editor.show_geometry.isVisible() or not editor.show_geometry.isEnabled()
    for b in (editor.btn_add_pad, editor.btn_add_row, editor.btn_add_column,
              editor.btn_add_wasd, editor.btn_add_analog, editor.btn_add_dpad, editor.btn_remove_stick):
        assert not b.isEnabled(), b.text()
    assert not editor.key_dimensions.isEnabled()
    editor.table.selectRow(0)
    assert not editor.btn_remove_pad.isEnabled()
    assert not editor.btn_delete_row.isEnabled()
    assert not editor.btn_delete_column.isEnabled()
    assert not editor.btn_capture.isEnabled()
    item = editor.table.item(0, 1)
    assert not item.flags() & Qt.ItemFlag.ItemIsEditable


def test_elite_paddles_are_the_only_editable_pads(editor):
    _load_xbox(editor, elite=True)
    rows = {editor.table.item(r, 0).text(): r for r in range(editor.table.rowCount())}
    for label in ("A", "LT", "Profile"):
        editor.table.selectRow(rows[label])
        assert not editor.btn_capture.isEnabled(), label
        assert not editor.table.item(rows[label], 1).flags() & Qt.ItemFlag.ItemIsEditable
    editor.table.selectRow(rows["P2"])
    assert editor.btn_capture.isEnabled()
    assert editor.table.item(rows["P2"], 0).flags() & Qt.ItemFlag.ItemIsEditable
    assert editor.table.item(rows["P2"], 1).flags() & Qt.ItemFlag.ItemIsEditable
    editor.btn_capture.setChecked(True)
    editor._on_key_captured("gp:a")
    assert editor.cfg["keys"][rows["P2"]]["input"] == "gp:a"
    assert editor.cfg["keys"][rows["P2"]]["label"] == "P2"  # a custom label survives a rebind


def test_unlocked_layout_is_unchanged(editor):
    assert not editor.locked
    assert editor.btn_add_pad.isEnabled() and editor.key_dimensions.isEnabled()
    editor.table.selectRow(0)
    assert editor.btn_capture.isEnabled() and editor.btn_remove_pad.isEnabled()
    assert editor.table.item(0, 1).flags() & Qt.ItemFlag.ItemIsEditable
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_settings_ui.py -k "locked or paddles or unlocked" -q`
Expected: FAIL with `AttributeError: 'SettingsWindow' object has no attribute 'locked'`.

- [ ] **Step 3: Implement locking**

In `SettingsWindow`, next to `selected_pads` (around line 1730) add:

```python
    @property
    def locked(self):
        """A fixed drawing (Xbox templates): no geometry, no adding or removing pads."""
        return bool(self.cfg.get("locked"))

    def _pad_editable(self, index):
        """Label and input of this pad may change: any pad on a free layout, flagged pads on a locked one."""
        return not self.locked or bool(self.cfg["keys"][index].get("editable"))
```

In `_layout_page`, keep a handle on the Key dimensions card and disable it when locked. After `l2.addLayout(f2)`:

```python
        self.key_dimensions = c2
        c2.setEnabled(not self.locked)
        if self.locked:
            c2.setToolTip("This layout is a fixed drawing. Use Size on this page to scale it.")
```

In `_keys_page`:

- Name the add buttons: `btn_add = self.btn_add_pad = QPushButton("Add pad")`; `b_add_keys = self.btn_add_wasd = ...`, `b_add_analog = self.btn_add_analog = ...`, `b_add_dpad = self.btn_add_dpad = ...`, `b_del = self.btn_remove_stick = ...`.
- After `self._show_key_geometry(False)` (the last line before `c2, l2 = card()`):

```python
        if self.locked:
            self.show_geometry.hide()
            for b in (self.btn_add_pad, self.btn_add_row, self.btn_add_column):
                b.setEnabled(False)
                b.setToolTip("This layout is a fixed drawing; pads cannot be added.")
```

- After the stick buttons are added to `srow` (before `self.joy_edits = {}`):

```python
        if self.locked:
            for c in range(5, 9):
                self.stick_table.setColumnHidden(c, True)
            for b in (self.btn_add_wasd, self.btn_add_analog, self.btn_add_dpad, self.btn_remove_stick):
                b.setEnabled(False)
            self.stick_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
```

In `_fill_table`, after the two `setItem` calls for label and input, gate editability:

```python
            if not self._pad_editable(r):
                for c in (0, 1):
                    it = self.table.item(r, c)
                    it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
```

In `_pad_selection_changed`, replace the four `setEnabled` lines:

```python
        editable = len(rows) == 1 and self._pad_editable(rows[0])
        self.btn_capture.setEnabled(editable)
        structural = bool(rows) and not self.locked
        self.btn_remove_pad.setEnabled(structural)
        self.btn_remove_pad.setText(f"Remove {len(rows)} pads" if len(rows) > 1 else "Remove")
        self.btn_delete_row.setEnabled(structural)
        self.btn_delete_column.setEnabled(structural)
```

In `_toggle_capture`, extend the guard so a locked pad cannot start recording:

```python
        target = self._capture_target()
        if on and (target is None or not self._pad_editable(target)):
            self.btn_capture.setChecked(False)
            self._show_error("Select one pad first" if target is None else "This pad is part of the drawing; only paddles can be changed")
            return
```

In `_delete_pads` (line 1924) add a first line `if self.locked: return`, and in `_remove_stick` / `_add_stick` / `_add_pad` / `_add_pad_line` add the same guard as their first statement, so the Delete key and shortcuts cannot bypass the disabled buttons.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_settings_ui.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add settings_ui.py tests/test_settings_ui.py
git commit -m "Locked layouts: fixed drawings edit only their flagged pads

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Edit on screen respects locked pads

**Files:**
- Modify: `overlay.py:1118-1132` (`mousePressEvent`), `overlay.py:1141-1160` (`mouseReleaseEvent`)
- Test: `tests/test_overlay_widget.py`

**Interfaces:**
- Consumes: `cfg["locked"]`, pad `source == ("key", i)`, `cfg["keys"][i]["editable"]`.
- Produces: `Overlay.pad_editable(pad) -> bool`.

- [ ] **Step 1: Write the failing test**

Read the top of `tests/test_overlay_widget.py` for the existing overlay fixture name (it builds an `overlay.Overlay` with hooks stubbed). Append, using that fixture as `ov`:

```python
def test_locked_layout_rebinds_only_editable_pads(ov):
    import templates
    ov.cfg.update(templates.build("Xbox controller", "Xbox Elite Series 2"))
    ov.apply()
    ov.set_edit_mode(True)
    by_label = {p.label: p for p in ov.pads}
    a, p2 = by_label["A"], by_label["P2"]
    assert not ov.pad_editable(a) and ov.pad_editable(p2)
    for pad, expect in ((a, False), (p2, True)):
        spot = pad.rect.center().toPoint()
        QTest.mousePress(ov, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, spot)
        QTest.mouseRelease(ov, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, spot)
        assert ov.capturing is expect and (ov.capture_pad is pad) is expect
        ov.capturing, ov.capture_pad = False, None
    QTest.mouseClick(ov, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, a.rect.center().toPoint())
    assert ov.cfg["keys"][a.source[1]]["input"] == "gp:a"  # right-click clears nothing on a fixed pad
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_overlay_widget.py -k locked -q`
Expected: FAIL with `AttributeError: 'Overlay' object has no attribute 'pad_editable'`.

- [ ] **Step 3: Implement**

In `Overlay`, above `mousePressEvent`:

```python
    def pad_editable(self, pad):
        """Clicking this pad in edit mode may rebind it: every pad on a free layout, flagged pads on a locked one."""
        if pad is None or not pad.source:
            return False
        if not self.cfg.get("locked"):
            return True
        return pad.source[0] == "key" and bool(self.cfg["keys"][pad.source[1]].get("editable"))
```

In `mousePressEvent`, right-button branch: change `if pad is not None and pad.source and pad.source[0] == "key":` to `if self.pad_editable(pad) and pad.source[0] == "key":`.

In `mouseReleaseEvent`: change `if pad is not None and pad.source:` to `if self.pad_editable(pad):`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_overlay_widget.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add overlay.py tests/test_overlay_widget.py
git commit -m "Edit on screen rebinds only editable pads on locked layouts

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Design board, docs, and README

**Files:**
- Modify: `design/gen.py:724-766` (add `xbox_board` after `mouse_board`), `design/gen.py` canvas list
- Modify: `README.md:138-157` (devices table and notes), `README.md:181-200` (config field table)
- Modify: `debug/screenshots.py` (add an Elite overlay capture to `docs/xbox.png`)

**Interfaces:**
- Consumes: `templates.xbox_profile`, `overlay.decor_path`, `overlay.shape_path`, `overlay.key_text_rect`.

- [ ] **Step 1: Add the design board**

In `design/gen.py` after `mouse_board`:

```python
def xbox_board():
    """Xbox Wireless front, Elite front, Elite back: geometry straight from the app."""
    radius = 4.0  # min(10, 20 * 0.2)
    font_px = 9 * PT
    lit = {"A", "P2"}
    x_cursor, gap, top = 30.0, 60.0, 50.0
    svg, bottom = "", 0
    for title, prof in (("Xbox Wireless", app_templates.xbox_profile(False)),
                        ("Xbox Elite Series 2", app_templates.xbox_profile(True))):
        cw = ch = float(prof["cell_w"])
        def cell(col, row, w, h):
            return QRectF(x_cursor + col * cw + 2, top + row * ch + 2, w * cw, h * ch)
        rects = []
        for d in prof["decor"]:
            r = cell(d["col"], d["row"], d["w"], d["h"])
            rects.append(r)
            svg += (f'<path d="{qpath_to_svg(app_overlay.decor_path(d["kind"], r))}" fill="{C["idle_fill"]}" '
                    f'stroke="{C["idle_outline"]}" stroke-opacity="0.47" stroke-width="1.2" fill-rule="evenodd"></path>')
        for st in prof["sticks"]:
            r = cell(st["col"], st["row"], st["w"], st["h"])
            rects.append(r)
            rad = min(r.width(), r.height()) * 0.30
            cx, cy = r.center().x(), r.center().y()
            svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="{C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>'
            if st.get("axes"):
                svg += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad * 0.42:.1f}" fill="{C["idle_outline"]}"></circle>'
            else:
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    svg += (f'<circle cx="{cx + dx * rad * 0.62:.1f}" cy="{cy + dy * rad * 0.62:.1f}" r="{rad * 0.30:.1f}" '
                            f'fill="{C["idle_fill"]}" stroke="{C["idle_outline"]}" stroke-width="1.2"></circle>')
        for k in prof["keys"]:
            r = cell(k["col"], k["row"], k["w"], k["h"])
            rects.append(r)
            on = k["label"] in lit
            body = qpath_to_svg(app_overlay.shape_path(r, k.get("shape", "rect"), radius))
            if on:
                svg += (f'<path d="{body}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.18" stroke-width="12"></path>'
                        f'<path d="{body}" fill="none" stroke="{C["pressed_outline"]}" stroke-opacity="0.09" stroke-width="6"></path>')
            svg += (f'<path d="{body}" fill="{C["pressed_fill"] if on else C["idle_fill"]}" stroke="{C["idle_outline"]}" '
                    f'stroke-width="{2.2 if on else 1.2}"></path>')
            tr = app_overlay.key_text_rect(r, k.get("shape", "rect"))
            size = font_px if len(k["label"]) <= 4 else font_px * 0.8
            svg += _txt(tr.center().x(), tr.center().y(), k["label"], size, C["pressed_text"] if on else C["idle_text"])
        w = max(r.right() for r in rects) - x_cursor + 4
        svg += _txt(x_cursor + w / 2, top - 22, title, 8 * PT, T["muted"], weight=400)
        x_cursor += w + gap
        bottom = max(bottom, max(r.bottom() for r in rects))
    fw, fh = int(x_cursor - gap + 30), int(bottom + 40)
    inner = (f'<div style="width: {fw}px; height: {fh}px; background: #0c0c0e; position: relative; overflow: hidden;">'
             f'<svg width="{fw}" height="{fh}" viewBox="0 0 {fw} {fh}" xmlns="http://www.w3.org/2000/svg" style="display: block;">{svg}</svg></div>')
    return inner, fw, fh
```

`qpath_to_svg` emits one `Z` at the end only; the back body contains five subpaths (body + four ghosts). Update `qpath_to_svg` so every `MoveToElement` after the first is preceded by `Z`:

```python
        if e.type == QPainterPath.ElementType.MoveToElement:
            if out:
                out.append("Z")
            out.append(f"M {e.x:.1f} {e.y:.1f}")
```

In the emit section after `boards["MouseLayouts.dc.html"] = mouse_html` add:

```python
xbox_html, xw, xh = xbox_board()
boards["XboxLayouts.dc.html"] = xbox_html
```

and in `canvas["artboards"]` after the MouseLayouts entry:

```python
        {"file": "XboxLayouts.dc.html", "title": "Overlay · Xbox layouts", "x": mw + 100, "y": H + 140 + KEYS_H + 140, "w": xw, "h": xh},
```

Run `python design/gen.py` and confirm `design/XboxLayouts.dc.html` exists.

- [ ] **Step 2: Screenshot for the docs**

Open `debug/screenshots.py`, find how `docs/overlay.png` and `docs/mouse.png` are produced, and add a capture of `templates.xbox_profile(True)` with A and P2 lit to `docs/xbox.png` following the same pattern. Run it and confirm `docs/xbox.png` shows both bodies.

- [ ] **Step 3: README**

In the devices table change the Controllers row to:

```markdown
| **Controllers** | Xbox Wireless, Xbox Elite Series 2 (with rear paddles), and PlayStation, with analog sticks and triggers |
```

After the `![The five mouse templates](docs/mouse.png)` line add:

```markdown
![Xbox Elite Series 2: front and back bodies with the four paddles](docs/xbox.png)
```

After the mouse paragraph ending "record an input for them on **Keys**." add:

```markdown
Xbox layouts are fixed drawings: the body and buttons stay where they are, and
**Size** scales the whole controller. On the Elite, the four paddles on the
back body are the only pads you edit. They start as `gp:paddle1` to
`gp:paddle4`. If the Xbox Accessories app maps a paddle to another button,
Windows reports only that button, so select the paddle and record the button
it is mapped to.
```

In the config field table add two rows after `decor`:

```markdown
| `locked` | `true` for fixed drawings such as the Xbox layouts: positions and pad count cannot be edited |
| `editable` (per key) | On a locked layout, the pads whose label and input may still change, such as the Elite paddles |
```

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add design/gen.py design/XboxLayouts.dc.html design/canvas.json debug/screenshots.py docs/xbox.png README.md
git commit -m "Xbox layouts on the design canvas, docs screenshot, README

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

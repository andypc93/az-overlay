"""Built-in layout templates: Azeron Cyborg 2, keyboards (form factor x language),
Xbox and PlayStation controllers.

A template yields the profile fields (keys, sticks, cell size, ...). Keys are
placed in key units (1u = one square key): col/row = position, w/h = size.

Keyboard keys carry a physical scancode ("sc"), so highlighting follows the
key's position no matter which Windows keyboard layout is active. Labels for
the printable keys come from the chosen language.
"""

# ---------------------------------------------------------------------------
# Scancodes (set 1). Extended keys carry the 0xE0 prefix.
# ---------------------------------------------------------------------------
SC = {
    "Esc": 0x01, "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06, "6": 0x07, "7": 0x08,
    "8": 0x09, "9": 0x0A, "0": 0x0B, "-": 0x0C, "=": 0x0D, "Backspace": 0x0E, "Tab": 0x0F,
    "Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13, "T": 0x14, "Y": 0x15, "U": 0x16, "I": 0x17,
    "O": 0x18, "P": 0x19, "[": 0x1A, "]": 0x1B, "Enter": 0x1C, "LCtrl": 0x1D,
    "A": 0x1E, "S": 0x1F, "D": 0x20, "F": 0x21, "G": 0x22, "H": 0x23, "J": 0x24, "K": 0x25,
    "L": 0x26, ";": 0x27, "'": 0x28, "`": 0x29, "LShift": 0x2A, "\\": 0x2B,
    "Z": 0x2C, "X": 0x2D, "C": 0x2E, "V": 0x2F, "B": 0x30, "N": 0x31, "M": 0x32,
    ",": 0x33, ".": 0x34, "/": 0x35, "RShift": 0x36, "Num *": 0x37, "LAlt": 0x38,
    "Space": 0x39, "Caps": 0x3A,
    "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E, "F5": 0x3F, "F6": 0x40, "F7": 0x41,
    "F8": 0x42, "F9": 0x43, "F10": 0x44, "Num Lock": 0x45, "Scroll Lock": 0x46,
    "Num 7": 0x47, "Num 8": 0x48, "Num 9": 0x49, "Num -": 0x4A, "Num 4": 0x4B, "Num 5": 0x4C,
    "Num 6": 0x4D, "Num +": 0x4E, "Num 1": 0x4F, "Num 2": 0x50, "Num 3": 0x51, "Num 0": 0x52,
    "Num .": 0x53, "ISO \\": 0x56, "F11": 0x57, "F12": 0x58,
    "RCtrl": 0xE01D, "RAlt": 0xE038, "Num /": 0xE035, "Num Enter": 0xE01C,
    "Insert": 0xE052, "Delete": 0xE053, "Home": 0xE047, "End": 0xE04F,
    "Page Up": 0xE049, "Page Down": 0xE051,
    "Up": 0xE048, "Down": 0xE050, "Left": 0xE04B, "Right": 0xE04D,
    "LWin": 0xE05B, "RWin": 0xE05C, "Menu": 0xE05D, "Print": 0xE037, "Pause": 0xE11D,
}

# Display label for a scancode name when it differs from the name itself.
DISPLAY = {
    "LCtrl": "Ctrl", "RCtrl": "Ctrl", "LAlt": "Alt", "RAlt": "Alt", "LShift": "Shift",
    "RShift": "Shift", "LWin": "Win", "RWin": "Win", "Caps": "Caps", "Backspace": "Bksp",
    "ISO \\": "\\", "Print": "PrtSc", "Scroll Lock": "ScrLk", "Num Lock": "Num",
    "Page Up": "PgUp", "Page Down": "PgDn", "Insert": "Ins", "Delete": "Del",
    "Num *": "*", "Num -": "-", "Num +": "+", "Num /": "/", "Num Enter": "Enter",
    "Num 0": "0", "Num 1": "1", "Num 2": "2", "Num 3": "3", "Num 4": "4", "Num 5": "5",
    "Num 6": "6", "Num 7": "7", "Num 8": "8", "Num 9": "9", "Num .": ".",
    "Up": "▲", "Down": "▼", "Left": "◀", "Right": "▶",
}

# Printable-key labels per language, keyed by the US name of the physical key.
LANGUAGES = {
    "US (ANSI)": {},
    "UK (ISO)": {"\\": "#", "ISO \\": "\\", "`": "`", "'": "'"},
    "German (ISO)": {
        "Y": "Z", "Z": "Y", "-": "ß", "=": "´", "[": "Ü", "]": "+", ";": "Ö",
        "'": "Ä", "\\": "#", "`": "^", "ISO \\": "<", "/": "-",
    },
    "French (ISO)": {
        "Q": "A", "W": "Z", "A": "Q", "Z": "W", "M": ",", ",": ";", ".": ":", "/": "!",
        ";": "M", "'": "ù", "\\": "*", "[": "^", "]": "$", "-": ")", "=": "=", "`": "²",
        "ISO \\": "<", "1": "&", "2": "é", "3": "\"", "4": "'", "5": "(", "6": "-",
        "7": "è", "8": "_", "9": "ç", "0": "à",
    },
    "Spanish (ISO)": {
        "`": "º", "-": "'", "=": "¡", "[": "`", "]": "+", ";": "Ñ", "'": "´",
        "\\": "Ç", "ISO \\": "<", "/": "-",
    },
}
ISO_LANGUAGES = {name for name in LANGUAGES if "ISO" in name}

# Row y positions (units). F row on top, then a 0.25u gap.
Y_F, Y_NUM, Y_Q, Y_A, Y_Z, Y_BOT = 0, 1.25, 2.25, 3.25, 4.25, 5.25


def _key(name, x, y, w=1.0, h=1.0):
    return {"name": name, "col": x, "row": y, "w": w, "h": h}


def _row(y, x0, items):
    """items: list of (name, width). Returns keys laid out left to right."""
    keys, x = [], x0
    for name, w in items:
        keys.append(_key(name, x, y, w))
        x += w
    return keys


def _main_block(iso, y0=Y_NUM, bottom="full", rshift=2.75, backspace=2.0):
    """The alphanumeric block. Returns keys; 15u wide."""
    k = []
    k += _row(y0, 0, [("`", 1)] + [(c, 1) for c in "1234567890"] + [("-", 1), ("=", 1), ("Backspace", backspace)])
    q = [("Tab", 1.5)] + [(c, 1) for c in "QWERTYUIOP"] + [("[", 1), ("]", 1)]
    if iso:
        k += _row(y0 + 1, 0, q)
        k.append(_key("Enter", 13.75, y0 + 1, 1.25, 2.0))
        k += _row(y0 + 2, 0, [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("'", 1), ("\\", 1)])
        k += _row(y0 + 3, 0, [("LShift", 1.25), ("ISO \\", 1)] + [(c, 1) for c in "ZXCVBNM"]
                  + [(",", 1), (".", 1), ("/", 1), ("RShift", rshift)])
    else:
        k += _row(y0 + 1, 0, q + [("\\", 1.5)])
        k += _row(y0 + 2, 0, [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("'", 1), ("Enter", 2.25)])
        k += _row(y0 + 3, 0, [("LShift", 2.25)] + [(c, 1) for c in "ZXCVBNM"]
                  + [(",", 1), (".", 1), ("/", 1), ("RShift", rshift)])
    if bottom == "full":
        k += _row(y0 + 4, 0, [("LCtrl", 1.25), ("LWin", 1.25), ("LAlt", 1.25), ("Space", 6.25),
                             ("RAlt", 1.25), ("RWin", 1.25), ("Menu", 1.25), ("RCtrl", 1.25)])
    elif bottom == "arrows":  # compact bottom row with arrow keys at the end
        k += _row(y0 + 4, 0, [("LCtrl", 1.25), ("LWin", 1.25), ("LAlt", 1.25), ("Space", 6.25),
                             ("RAlt", 1), ("Fn", 1), ("RCtrl", 1), ("Left", 1), ("Down", 1), ("Right", 1)])
    return k


def _f_row(x_gap=True, extra=()):
    k = [_key("Esc", 0, Y_F)]
    if x_gap:
        for i, f in enumerate(["F1", "F2", "F3", "F4"]):
            k.append(_key(f, 2 + i, Y_F))
        for i, f in enumerate(["F5", "F6", "F7", "F8"]):
            k.append(_key(f, 6.5 + i, Y_F))
        for i, f in enumerate(["F9", "F10", "F11", "F12"]):
            k.append(_key(f, 11 + i, Y_F))
        x = 15.25
    else:
        for i in range(12):
            k.append(_key(f"F{i + 1}", 1 + i, Y_F))
        x = 13
    for name in extra:
        k.append(_key(name, x, Y_F))
        x += 1
    return k


def _nav_cluster(x0=15.25):
    k = [_key("Print", x0, Y_F), _key("Scroll Lock", x0 + 1, Y_F), _key("Pause", x0 + 2, Y_F),
         _key("Insert", x0, Y_NUM), _key("Home", x0 + 1, Y_NUM), _key("Page Up", x0 + 2, Y_NUM),
         _key("Delete", x0, Y_Q), _key("End", x0 + 1, Y_Q), _key("Page Down", x0 + 2, Y_Q),
         _key("Up", x0 + 1, Y_Z), _key("Left", x0, Y_BOT), _key("Down", x0 + 1, Y_BOT), _key("Right", x0 + 2, Y_BOT)]
    return k


def _numpad(x0=18.5, y0=Y_NUM):
    return [
        _key("Num Lock", x0, y0), _key("Num /", x0 + 1, y0), _key("Num *", x0 + 2, y0), _key("Num -", x0 + 3, y0),
        _key("Num 7", x0, y0 + 1), _key("Num 8", x0 + 1, y0 + 1), _key("Num 9", x0 + 2, y0 + 1),
        _key("Num +", x0 + 3, y0 + 1, 1, 2),
        _key("Num 4", x0, y0 + 2), _key("Num 5", x0 + 1, y0 + 2), _key("Num 6", x0 + 2, y0 + 2),
        _key("Num 1", x0, y0 + 3), _key("Num 2", x0 + 1, y0 + 3), _key("Num 3", x0 + 2, y0 + 3),
        _key("Num Enter", x0 + 3, y0 + 3, 1, 2),
        _key("Num 0", x0, y0 + 4, 2), _key("Num .", x0 + 2, y0 + 4),
    ]


def _side_column(x, names, rows=(Y_NUM, Y_Q, Y_A, Y_Z)):
    return [_key(n, x, y) for n, y in zip(names, rows) if n]


def _shift(keys, dx=0.0, dy=0.0):
    for k in keys:
        k["col"] += dx
        k["row"] += dy
    return keys


# ---- form factors ----------------------------------------------------------
def kb_full(iso):
    return _f_row() + _main_block(iso) + _nav_cluster() + _numpad()


def kb_tkl(iso):
    return _f_row() + _main_block(iso) + _nav_cluster()


def kb_1800(iso):
    k = _f_row(extra=("Delete",))
    k += _main_block(iso, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_Z))
    k += _numpad(x0=16.25)
    k += [_key("Home", 16.25, Y_F), _key("End", 17.25, Y_F), _key("Page Up", 18.25, Y_F), _key("Page Down", 19.25, Y_F)]
    return k


def kb_96(iso):
    k = _f_row(x_gap=False, extra=("Print", "Delete", "Home", "End", "Page Up", "Page Down"))
    k += _main_block(iso, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_Z))
    k += _numpad(x0=16)
    return k


def kb_75_exploded(iso):
    k = _f_row(x_gap=False, extra=("Print", "Pause"))
    k[-1]["col"] += 0.25
    k[-2]["col"] += 0.25
    k += _main_block(iso, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_Z))
    k += _side_column(15.25, ("Delete", "Page Up", "Page Down", None))
    return k


def kb_75_compact(iso):
    k = _f_row(x_gap=False, extra=("Print", "Pause", "Delete"))
    k += _main_block(iso, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_Z))
    k += _side_column(15, ("Home", "Page Up", "Page Down", "End"))
    return k


def kb_65_exploded(iso):
    k = _main_block(iso, y0=Y_F, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_F + 3))
    k += _side_column(15.25, ("Delete", "Page Up", "Page Down", None), rows=(Y_F, Y_F + 1, Y_F + 2, Y_F + 3))
    return k


def kb_65_compact(iso):
    k = _main_block(iso, y0=Y_F, bottom="arrows", rshift=1.75)
    k.append(_key("Up", 14, Y_F + 3))
    k += _side_column(15, ("Delete", "Page Up", "Page Down", "End"), rows=(Y_F, Y_F + 1, Y_F + 2, Y_F + 3))
    return k


def kb_60(iso):
    return _main_block(iso, y0=Y_F)


def kb_50(iso):
    k = _row(0, 0, [("Esc", 1)] + [(c, 1) for c in "1234567890"] + [("-", 1), ("Backspace", 1.75)])
    k += _row(1, 0, [("Tab", 1.25)] + [(c, 1) for c in "QWERTYUIOP"] + [("[", 1), ("]", 1.5)])
    k += _row(2, 0, [("Caps", 1.75)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("Enter", 2)])
    k += _row(3, 0, [("LShift", 2.25)] + [(c, 1) for c in "ZXCVBNM"] + [(",", 1), (".", 1), ("RShift", 2.5)])
    k += _row(4, 0, [("LCtrl", 1.25), ("LAlt", 1.25), ("Space", 8.75), ("RAlt", 1.25), ("RCtrl", 1.25)])
    return k


def kb_40(iso):
    k = _row(0, 0, [("Esc", 1)] + [(c, 1) for c in "QWERTYUIOP"] + [("Backspace", 1.75)])
    k += _row(1, 0, [("Tab", 1.25)] + [(c, 1) for c in "ASDFGHJKL"] + [(";", 1), ("Enter", 1.5)])
    k += _row(2, 0, [("LShift", 1.75)] + [(c, 1) for c in "ZXCVBNM"] + [(",", 1), (".", 1), ("/", 1), ("RShift", 1)])
    k += _row(3, 0, [("LCtrl", 1.25), ("LWin", 1.25), ("LAlt", 1.25), ("Space", 6.75), ("RAlt", 1.25), ("RCtrl", 1)])
    return k


KEYBOARDS = [
    ("100% Full size", kb_full),
    ("1800", kb_1800),
    ("96% Compact", kb_96),
    ("80% TKL", kb_tkl),
    ("75% Exploded", kb_75_exploded),
    ("75% Compact", kb_75_compact),
    ("65% Exploded", kb_65_exploded),
    ("65% Compact", kb_65_compact),
    ("60%", kb_60),
    ("50%", kb_50),
    ("40%", kb_40),
]


def keyboard_profile(form, language):
    builder = dict(KEYBOARDS)[form]
    iso = language in ISO_LANGUAGES
    names = LANGUAGES[language]
    keys = []
    for k in builder(iso):
        name = k.pop("name")
        label = names.get(name, DISPLAY.get(name, name))
        entry = {"label": label, "col": k["col"], "row": k["row"], "w": k["w"], "h": k["h"]}
        if name == "Fn":
            entry["input"] = ""  # Fn never reaches the OS
        else:
            entry["sc"] = SC[name]
        keys.append(entry)
    return {
        "cell_w": 54, "cell_h": 54, "gap": 5, "scale": 0.7, "shape": "rect",
        "font": {"family": "Segoe UI", "size": 9, "bold": True},
        "keys": keys, "sticks": [],
    }


# ---- Azeron keypads ------------------------------------------------------------
# Drawn in the style of the Azeron software editor: finger towers as columns,
# thumb cluster to the right. Default bindings are placeholders; rebind by
# clicking a pad in move mode. Geometry is approximate per model.
_CYBORG_II = [
    ("Page Up", 7, 0), ("9", 1, 1), ("Alt", 2, 1), ("H", 3, 1), ("X", 4, 1), ("F1", 6, 1),
    ("Esc", 7, 1), ("F2", 8, 1), ("0", 1, 2), ("", 2, 2), ("G", 3, 2), ("I", 4, 2),
    ("Page Down", 7, 2), ("Q", 0, 3), ("B", 1, 3), ("Z", 2, 3), ("V", 3, 3), ("F", 4, 3),
    ("E", 5, 3), ("J", 8, 3), ("R", 1, 4), ("Shift", 2, 4), ("Space", 3, 4), ("Ctrl", 4, 4),
    ("Caps Lock", 8, 4), ("L", 1, 5), ("M", 2, 5), ("", 3, 5), ("C", 4, 5), ("Tab", 6, 5),
]
_STICK = {"label": "Left Stick", "up": "W", "left": "A", "down": "S", "right": "D",
          "axes": ["gp:leftx", "gp:lefty"], "click": "gp:leftstick"}


def _azeron(pads, stick_pos=(6, 3)):
    stick = dict(_STICK, col=stick_pos[0], row=stick_pos[1], w=2, h=2)
    return {
        "cell_w": 100, "cell_h": 140, "gap": 8, "scale": 0.5, "shape": "rect",
        "font": {"family": "Segoe UI", "size": 13, "bold": True},
        "keys": [{"label": l, "col": c, "row": r, "w": 1, "h": 1} for l, c, r in pads],
        "sticks": [stick],
    }


def _towers(cols, rows, labels, x0=1, y0=1):
    """Finger towers: `rows[i]` pads in column i, labelled from `labels`."""
    pads, it = [], iter(labels)
    for i in range(cols):
        for r in range(rows[i]):
            pads.append((next(it, ""), x0 + i, y0 + r))
    return pads


def az_cyborg_ii():
    return _azeron(_CYBORG_II)


def az_cyborg_ii_compact():
    pads = [p for p in _CYBORG_II if p[2] != 5 and p != ("Page Up", 7, 0)]
    pads.append(("Page Up", 6, 2))
    return _azeron(pads)


def az_cyborg():
    return _azeron([p for p in _CYBORG_II if p != ("Tab", 6, 5)])


def az_cyborg_compact():
    pads = [p for p in _CYBORG_II if p[2] != 5 and p not in (("Page Up", 7, 0), ("Tab", 6, 5))]
    pads.append(("Page Up", 6, 2))
    return _azeron(pads)


def az_keyzen():
    finger = _towers(5, (4, 4, 4, 4, 4), list("12345QWERTASDFGZXCVB"), x0=0, y0=0)
    thumb = [("Esc", 6, 0), ("Tab", 7, 0), ("Enter", 8, 0), ("Shift", 8, 1), ("Ctrl", 8, 2),
             ("Space", 6, 3), ("Alt", 7, 3)]
    return _azeron(finger + thumb, stick_pos=(6, 1))


def az_cyro():
    finger = _towers(4, (3, 3, 3, 3), list("1234QWERASDF"), x0=0, y0=0)
    thumb = [("Esc", 5, 0), ("Tab", 6, 0), ("Shift", 5, 3), ("Ctrl", 6, 3)]
    mouse = [("Mouse Left", 8, 0), ("Mouse Right", 8, 1), ("Mouse Middle", 8, 2)]
    prof = _azeron(finger + thumb + mouse, stick_pos=(5, 1))
    short = {"Mouse Left": "LMB", "Mouse Right": "RMB", "Mouse Middle": "MMB"}
    for k in prof["keys"]:
        if k["label"] in short:
            k["input"] = k["label"]
            k["label"] = short[k["label"]]
    return prof


def az_classic():
    finger = _towers(4, (4, 4, 4, 4), list("1234QWERASDFZXCV"), x0=1, y0=0)
    thumb = [("Q", 0, 2), ("E", 5, 2), ("F1", 6, 0), ("Esc", 7, 0), ("F2", 8, 0), ("Tab", 6, 3),
             ("Space", 8, 2), ("Shift", 8, 3)]
    return _azeron(finger + thumb, stick_pos=(6, 1))


def az_compact():
    finger = _towers(4, (3, 3, 3, 3), list("1234QWERASDF"), x0=1, y0=0)
    thumb = [("Q", 0, 1), ("E", 5, 1), ("F1", 6, 0), ("Esc", 7, 0), ("F2", 8, 0), ("Tab", 6, 3),
             ("Space", 8, 2), ("Shift", 8, 3)]
    return _azeron(finger + thumb, stick_pos=(6, 1))


AZERON_MODELS = [
    ("Cyborg II", az_cyborg_ii),
    ("Cyborg II Compact", az_cyborg_ii_compact),
    ("Cyborg", az_cyborg),
    ("Cyborg Compact", az_cyborg_compact),
    ("Keyzen", az_keyzen),
    ("Cyro", az_cyro),
    ("Classic", az_classic),
    ("Compact", az_compact),
]


def azeron_profile(model="Cyborg II"):
    return dict(AZERON_MODELS)[model]()


# ---- controllers -------------------------------------------------------------
def _controller(names):
    """Grid controller geometry (PlayStation); `names` maps logical inputs to labels."""
    n = names
    keys = [
        {"label": n["lt"], "col": 0.6, "row": 0, "w": 2.2, "h": 0.9, "axis": "gp:lefttrigger", "input": "gp:lefttrigger"},
        {"label": n["rt"], "col": 9.2, "row": 0, "w": 2.2, "h": 0.9, "axis": "gp:righttrigger", "input": "gp:righttrigger"},
        {"label": n["lb"], "col": 0.6, "row": 1.05, "w": 2.2, "h": 0.7, "input": "gp:leftshoulder"},
        {"label": n["rb"], "col": 9.2, "row": 1.05, "w": 2.2, "h": 0.7, "input": "gp:rightshoulder"},
        {"label": n["back"], "col": 4.3, "row": 2.9, "w": 1.1, "h": 0.7, "input": "gp:back"},
        {"label": n["start"], "col": 6.6, "row": 2.9, "w": 1.1, "h": 0.7, "input": "gp:start"},
        {"label": n["guide"], "col": 5.5, "row": 1.9, "w": 1, "h": 1, "shape": "circle", "input": "gp:guide"},
        {"label": n["y"], "col": 9.8, "row": 2.2, "w": 1, "h": 1, "shape": "circle", "input": "gp:y"},
        {"label": n["x"], "col": 8.7, "row": 3.2, "w": 1, "h": 1, "shape": "circle", "input": "gp:x"},
        {"label": n["b"], "col": 10.9, "row": 3.2, "w": 1, "h": 1, "shape": "circle", "input": "gp:b"},
        {"label": n["a"], "col": 9.8, "row": 4.2, "w": 1, "h": 1, "shape": "circle", "input": "gp:a"},
    ]
    if n.get("misc1"):
        keys.append({"label": n["misc1"], "col": 5.5, "row": 4.0, "w": 1, "h": 0.6, "input": "gp:misc1"})
    if n.get("touchpad"):
        keys.append({"label": n["touchpad"], "col": 4.0, "row": 0.6, "w": 4, "h": 1.4, "input": "gp:touchpad"})
        for k in keys:  # PlayStation: Create / Options sit under the touchpad, PS button below them
            if k["input"] in ("gp:back", "gp:start"):
                k["row"] = 2.3
            elif k["input"] == "gp:guide":
                k.update(row=3.3)
    dpad = {"label": "", "up": "gp:dpup", "down": "gp:dpdown", "left": "gp:dpleft", "right": "gp:dpright", "w": 2.2, "h": 2.2}
    lstick = {"label": "L", "axes": ["gp:leftx", "gp:lefty"], "click": "gp:leftstick", "w": 2.4, "h": 2.4}
    rstick = {"label": "R", "axes": ["gp:rightx", "gp:righty"], "click": "gp:rightstick", "w": 2.4, "h": 2.4}
    if n.get("touchpad"):  # PlayStation: dpad top-left, both sticks low
        dpad.update(col=1.0, row=2.5)
        lstick.update(col=3.4, row=4.9)
        rstick.update(col=6.6, row=4.9)
    else:  # Xbox: left stick top-left, dpad low-left
        lstick.update(col=0.9, row=2.3)
        dpad.update(col=3.0, row=5.0)
        rstick.update(col=7.0, row=5.0)
    return {
        "cell_w": 54, "cell_h": 54, "gap": 0, "scale": 0.8, "shape": "rect",
        "font": {"family": "Segoe UI", "size": 9, "bold": True},
        "keys": keys, "sticks": [lstick, dpad, rstick],
    }


PLAYSTATION = {"lt": "L2", "rt": "R2", "lb": "L1", "rb": "R1", "back": "Create", "start": "Options",
               "guide": "PS", "y": "△", "x": "□", "b": "○", "a": "✕",
               "touchpad": "Touchpad"}


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
        _u(60, 12, 64, 22, label="LT", axis="gp:lefttrigger", input="gp:lefttrigger"),
        _u(276, 12, 64, 22, label="RT", axis="gp:righttrigger", input="gp:righttrigger"),
        _u(60, 44, 64, 18, label="LB", input="gp:leftshoulder"),   # sits on the bumper hump
        _u(276, 44, 64, 18, label="RB", input="gp:rightshoulder"),
        _circle(200, 74, 18, "ⓧ", "gp:guide"),
        _u(150, 120, 30, 18, label="View", input="gp:back"),
        _u(220, 120, 30, 18, label="Menu", input="gp:start"),
        _u(186, 144, 28, 14, label="Profile", input="") if elite
        else _u(186, 144, 28, 14, label="Share", input="gp:misc1"),
        _circle(306, 98, 15, "Y", "gp:y"),
        _circle(275, 129, 15, "X", "gp:x"),
        _circle(337, 129, 15, "B", "gp:b"),
        _circle(306, 160, 15, "A", "gp:a"),
    ]
    # Sticks draw their ring at 0.3 of the box, so the boxes overlap their neighbours; the rings do not.
    sticks = [
        _u(40, 80, 100, 100, label="L", axes=["gp:leftx", "gp:lefty"], click="gp:leftstick"),
        _u(96, 152, 96, 96, label="", up="gp:dpup", down="gp:dpdown", left="gp:dpleft", right="gp:dpright"),
        _u(210, 152, 96, 96, label="R", axes=["gp:rightx", "gp:righty"], click="gp:rightstick"),
    ]
    decor = [_u(0, 0, 400, 372, kind="xbox_front")]
    if elite:
        bx = XBOX_BACK_COL * XBOX_CELL
        decor.append(_u(bx, 0, 400, 372, kind="xbox_back"))
        # Paddles hang from the lower back between the grips, as on the real controller.
        for label, cx, cy, w, h, shape in (("P1", 170, 262, 20, 66, "paddle_l"), ("P2", 132, 282, 18, 48, "paddle_l"),
                                           ("P3", 230, 262, 20, 66, "paddle_r"), ("P4", 268, 282, 18, 48, "paddle_r")):
            keys.append(_u(bx + cx - w / 2, cy - h / 2, w, h, label=label, shape=shape,
                           input=f"gp:paddle{label[1]}", editable=True))
    return {
        "cell_w": XBOX_CELL, "cell_h": XBOX_CELL, "gap": 0, "scale": 0.8, "shape": "rect",
        "locked": True, "stick_box": False,
        "font": {"family": "Segoe UI", "size": 9, "bold": True},
        "keys": keys, "sticks": sticks, "decor": decor,
    }


# ---- mice --------------------------------------------------------------------
# From a plain two-button mouse to an MMO mouse with a 12-key thumb grid. Main
# buttons and Back / Forward send real mouse buttons and the wheel shows scroll
# ticks above and below the middle click; the MMO thumb grid uses the
# 1-9, 0, -, = keys that Naga / G600 style mice send by default. DPI and sniper
# buttons normally send nothing, so they start unbound: record an input on Keys.
MICE = [("2 buttons", 2), ("3 buttons", 3), ("5 buttons", 5), ("8 buttons", 8), ("MMO (12 side buttons)", 12)]
MMO_SIDE = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="]


def mouse_profile(template="3 buttons"):
    """A mouse seen from above: the body is a silhouette behind the pads, the two main
    buttons carry the domed top, thumb keys hang off the left flank."""
    buttons = dict(MICE).get(template, 3)
    bx = 2.0 if buttons == 12 else (0.6 if buttons >= 5 else 0.0)  # body x; thumb keys sit left of it
    body = {"kind": "mouse", "col": bx, "row": 0, "w": 4.0, "h": 6.4}
    keys = []
    if buttons == 2:
        keys += [{"label": "Left", "input": "Mouse Left", "shape": "mouse_left_full", "col": bx, "row": 0, "w": 2.0, "h": 2.7},
                 {"label": "Right", "input": "Mouse Right", "shape": "mouse_right_full", "col": bx + 2.0, "row": 0, "w": 2.0, "h": 2.7}]
    else:
        keys += [{"label": "Left", "input": "Mouse Left", "shape": "mouse_left", "col": bx, "row": 0, "w": 1.6, "h": 2.7},
                 {"label": "▲", "input": "Wheel Up", "col": bx + 1.6, "row": 0.45, "w": 0.8, "h": 0.45},
                 {"label": "Wheel", "input": "Mouse Middle", "col": bx + 1.6, "row": 0.95, "w": 0.8, "h": 0.9},
                 {"label": "▼", "input": "Wheel Down", "col": bx + 1.6, "row": 1.9, "w": 0.8, "h": 0.45},
                 {"label": "Right", "input": "Mouse Right", "shape": "mouse_right", "col": bx + 2.4, "row": 0, "w": 1.6, "h": 2.7}]
    if buttons in (5, 8):
        keys += [{"label": "Fwd", "input": "Mouse 5", "col": bx - 0.5, "row": 2.9, "w": 1.0, "h": 0.7},
                 {"label": "Back", "input": "Mouse 4", "col": bx - 0.5, "row": 3.7, "w": 1.0, "h": 0.7}]
    if buttons == 8:
        keys += [{"label": "DPI +", "input": "", "col": bx + 1.6, "row": 2.85, "w": 0.8, "h": 0.5},
                 {"label": "DPI −", "input": "", "col": bx + 1.6, "row": 3.4, "w": 0.8, "h": 0.5},
                 {"label": "Sniper", "input": "", "col": bx - 0.5, "row": 4.5, "w": 1.0, "h": 0.7}]
    if buttons == 12:  # a 3 x 4 thumb plate on the flank replaces Back / Forward
        for i, key in enumerate(MMO_SIDE):
            keys.append({"label": key, "input": key, "col": 0.1 + (i % 3) * 0.95, "row": 2.8 + (i // 3) * 0.85,
                         "w": 0.9, "h": 0.8})
    return {
        "cell_w": 40, "cell_h": 40, "gap": 0, "scale": 1.0, "shape": "rect",
        "font": {"family": "Segoe UI", "size": 9, "bold": True},
        "keys": keys, "sticks": [], "decor": [body],
    }


# ---- catalogue ----------------------------------------------------------------
DEVICES = ["Azeron", "Keyboard", "Mouse", "Xbox controller", "PlayStation controller"]


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


def layouts_for(device):
    return list(LANGUAGES) if device == "Keyboard" else []


def build(device, template=None, layout=None):
    """Return a fresh profile dict for the chosen template."""
    if device == "Keyboard":
        return keyboard_profile(template or KEYBOARDS[0][0], layout or "US (ANSI)")
    if device == "Mouse":
        return mouse_profile(template or MICE[0][0])
    if device == "Xbox controller":
        return xbox_profile(elite=template == XBOX_TEMPLATES[1])
    if device == "PlayStation controller":
        return _controller(PLAYSTATION)
    if template in dict(AZERON_MODELS):
        return azeron_profile(template)
    return azeron_profile()


def suggested_name(device, template=None, layout=None):
    if device == "Keyboard":
        return f"{template} – {layout}"
    if device == "Azeron":
        return f"Azeron {template}"
    if device == "Mouse":
        return f"Mouse – {template}"
    if device == "Xbox controller":
        return template or XBOX_TEMPLATES[0]
    return device

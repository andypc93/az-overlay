"""AZ-Overlay: transparent, click-through input overlay for the Azeron Cyborg 2,
keyboards, and Xbox / PlayStation controllers.

Qt (PySide6) window: frameless, always on top, transparent background, mouse
events pass through to the game. A global keyboard hook (pynput) plus SDL
game-controller polling light pads while they are held; releases fade out.

A tray icon opens the Settings window (see settings_ui.py) where layout, keys,
colors, position and scale are edited live and saved to config.json.

Hotkeys: Ctrl+Alt+O toggles visibility, Ctrl+Alt+S opens settings,
Ctrl+Alt+E toggles Edit on screen, Ctrl+Alt+Q quits (editable in config).
"""

import ctypes
import json
import math
import os
import queue
import shutil
import sys
import time

from pynput import keyboard, mouse
from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QFontMetrics, QFontMetricsF, QGuiApplication, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from gamepad import Gamepad, is_gamepad_input

APP_NAME = "AZ-Overlay"

FROZEN = getattr(sys, "frozen", False)
_HERE = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
# Bundled defaults (inside the exe when frozen, the repo when running from source).
_DEFAULTS = getattr(sys, "_MEIPASS", _HERE)
# User data. The exe keeps it in %APPDATA% so rebuilding / replacing the exe
# never touches saved settings or layouts. From source it lives in the repo.
if FROZEN:
    _BASE = os.path.join(os.environ.get("APPDATA", _HERE), "az-overlay")
else:
    _BASE = _HERE
CONFIG_PATH = os.path.join(_BASE, "config.json")
PROFILE_DIR = os.path.join(_BASE, "profiles")
LOGO_PATH = os.path.join(_DEFAULTS, "assets", "logo_256.png")


def ensure_user_data():
    """First run: seed %APPDATA%\\az-overlay from the bundled defaults (or from
    files next to the exe, for installs that used to keep them there)."""
    if not FROZEN:
        return
    os.makedirs(PROFILE_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        for src in (os.path.join(_HERE, "config.json"), os.path.join(_DEFAULTS, "config.json")):
            if os.path.exists(src):
                shutil.copy(src, CONFIG_PATH)
                break
    if not os.listdir(PROFILE_DIR):
        for src in (os.path.join(_HERE, "profiles"), os.path.join(_DEFAULTS, "profiles")):
            if os.path.isdir(src):
                for f in os.listdir(src):
                    if f.lower().endswith(".json"):
                        shutil.copy(os.path.join(src, f), os.path.join(PROFILE_DIR, f))
                break


# What a saved layout profile carries (hotkeys and app theme stay global).
PROFILE_KEYS = ("x", "y", "scale", "opacity", "cell_w", "cell_h", "gap", "shape",
                "pad_style", "stick_style", "stick_box", "colors", "font", "keys", "sticks", "decor", "locked")

# How keys and buttons are drawn; the idle/pressed colors apply to every style.
PAD_STYLES = ("classic", "outline", "keycap", "underline", "pill")

# How sticks and d-pads are drawn. "classic" is the ring-and-dots look from the first versions.
STICK_STYLES = ("classic", "ring", "petals", "vector", "keys")
STICK_DIRS = (("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0))
STICK_VECTORS = {name: (dx, dy) for name, dx, dy in STICK_DIRS}
TEXT_SHAPES = ("dot", "letter", "petal")  # pads whose label is drawn at a point, not fitted in a rect

# ---------------------------------------------------------------------------
# Input tokens. A pad is lit when its input is held. Tokens are either Windows
# virtual-key codes (int) or gamepad ids ("gp:a"). Keyboard keys can be given
# by name ("Page Up"), or physically by scancode (templates do this so the
# highlight follows the key position on any Windows layout).
# ---------------------------------------------------------------------------
WHEEL_UP, WHEEL_DOWN = 0x100, 0x101  # pseudo virtual-key codes for scroll ticks
WHEEL_HOLD_S = 0.12

VK_BY_LABEL = {
    "Alt": [0x12, 0xA4, 0xA5],
    "Shift": [0x10, 0xA0, 0xA1],
    "Ctrl": [0x11, 0xA2, 0xA3],
    "Space": [0x20],
    "Esc": [0x1B],
    "Escape": [0x1B],
    "Tab": [0x09],
    "Enter": [0x0D],
    "Backspace": [0x08],
    "Delete": [0x2E],
    "Insert": [0x2D],
    "Home": [0x24],
    "End": [0x23],
    "Page Up": [0x21],
    "Page Down": [0x22],
    "Caps Lock": [0x14],
    "Up": [0x26],
    "Down": [0x28],
    "Left": [0x25],
    "Right": [0x27],
    "Win": [0x5B, 0x5C],
    "Menu": [0x5D],
    "Print": [0x2C],
    "Scroll Lock": [0x91],
    "Pause": [0x13],
    "Num Lock": [0x90],
    ";": [0xBA], "=": [0xBB], ",": [0xBC], "-": [0xBD], ".": [0xBE], "/": [0xBF],
    "`": [0xC0], "[": [0xDB], "\\": [0xDC], "]": [0xDD], "'": [0xDE],
    "Num *": [0x6A], "Num +": [0x6B], "Num -": [0x6D], "Num .": [0x6E], "Num /": [0x6F],
    "Mouse Left": [0x01], "Mouse Right": [0x02], "Mouse Middle": [0x04],
    "Mouse 4": [0x05], "Mouse 5": [0x06],
    # Scroll ticks have no release, so they are pseudo keys (above the real VK range)
    # that the overlay holds for WHEEL_HOLD_S after each tick.
    "Wheel Up": [WHEEL_UP], "Wheel Down": [WHEEL_DOWN],
}
VK_BY_LABEL.update({f"F{n}": [0x6F + n] for n in range(1, 25)})
VK_BY_LABEL.update({f"Num {n}": [0x60 + n] for n in range(10)})
_LOWER = {k.lower(): v for k, v in VK_BY_LABEL.items()}

LABEL_BY_VK = {}
for _label, _vks in VK_BY_LABEL.items():
    for _vk in _vks:
        LABEL_BY_VK.setdefault(_vk, _label)
for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    LABEL_BY_VK[ord(_ch)] = _ch

CTRL_VKS = {0x11, 0xA2, 0xA3}
ALT_VKS = {0x12, 0xA4, 0xA5}

GAMEPAD_LABELS = {
    "gp:a": "A", "gp:b": "B", "gp:x": "X", "gp:y": "Y", "gp:back": "View", "gp:start": "Menu",
    "gp:guide": "Guide", "gp:leftstick": "LS", "gp:rightstick": "RS", "gp:leftshoulder": "LB",
    "gp:rightshoulder": "RB", "gp:dpup": "▲", "gp:dpdown": "▼", "gp:dpleft": "◀",
    "gp:dpright": "▶", "gp:misc1": "Share", "gp:touchpad": "Touchpad",
    "gp:lefttrigger": "LT", "gp:righttrigger": "RT",
    "gp:paddle1": "P1", "gp:paddle2": "P2", "gp:paddle3": "P3", "gp:paddle4": "P4",
}


def _token_for_name(name):
    """One key name -> set of tokens. Raises ValueError for unknown names."""
    key = name.strip()
    if not key:
        return set()
    if is_gamepad_input(key):
        if key in GAMEPAD_LABELS:
            return {key}
        raise ValueError(f"Unknown controller input: {key!r}")
    if key.lower() in _LOWER:
        return set(_LOWER[key.lower()])
    if len(key) == 1 and key.isalnum():
        return {ord(key.upper())}  # VK_A..VK_Z / VK_0..VK_9 equal ASCII uppercase
    raise ValueError(f"Unknown key name: {name!r}")


def parse_input(text):
    """Input expression -> list of alternatives, each a list of token-sets.

    "F5"             lit while F5 is held
    "F5, F6"         lit while F5 or F6 is held (a macro that sends several keys)
    "Ctrl+Shift+K"   lit while all three are held (a chord)
    """
    alts = []
    for alt in text.split(","):
        chord = [_token_for_name(part) for part in alt.split("+") if part.strip()]
        chord = [c for c in chord if c]
        if chord:
            alts.append(chord)
    return alts


def vks_for_label(label):
    """Compatibility helper: the set of tokens that light a plain label."""
    tokens = set()
    for chord in parse_input(label):
        for group in chord:
            tokens |= group
    return tokens


def label_for_vk(vk):
    """Human label for a virtual-key code, or None if we don't know it."""
    return LABEL_BY_VK.get(vk)


def label_for_token(token):
    if is_gamepad_input(token):
        return GAMEPAD_LABELS.get(token, token)
    return label_for_vk(token)


def vk_of(key):
    """Extract the virtual-key code from a pynput key object."""
    vk = getattr(key, "vk", None)
    if vk is None:
        vk = getattr(getattr(key, "value", None), "vk", None)
    return vk


_MAPVK_VSC_TO_VK_EX = 3
_SC_FIXED = {0xE11D: {0x13}}  # Pause never round-trips through MapVirtualKey


def tokens_for_scancode(sc):
    """Physical key -> virtual-key(s) under the active Windows layout."""
    if sc in _SC_FIXED:
        return set(_SC_FIXED[sc])
    if os.name != "nt":
        return set()
    vk = ctypes.windll.user32.MapVirtualKeyW(sc, _MAPVK_VSC_TO_VK_EX)
    if not vk and sc > 0xFF:  # older Windows: strip the extended prefix
        vk = ctypes.windll.user32.MapVirtualKeyW(sc & 0xFF, _MAPVK_VSC_TO_VK_EX)
    if not vk:
        return set()
    out = {vk}
    # The hook reports left/right variants; also accept the generic code.
    if vk in (0xA0, 0xA1):
        out.add(0x10)
    elif vk in (0xA2, 0xA3):
        out.add(0x11)
    elif vk in (0xA4, 0xA5):
        out.add(0x12)
    return out


def pad_inputs(entry):
    """Resolve a key entry to its alternatives (see parse_input)."""
    if "sc" in entry and entry.get("input") is None:
        toks = tokens_for_scancode(entry["sc"])
        return [[toks]] if toks else []
    text = entry.get("input")
    if text is None:
        text = entry.get("label", "")
    return parse_input(text)


def input_matches(alts, pressed):
    for chord in alts:
        if all(group & pressed for group in chord):
            return True
    return False


DEFAULT_COLORS = {
    "idle_fill": "#1e1e1e",
    "idle_outline": "#c9d400",
    "idle_text": "#ffffff",
    "pressed_fill": "#c9d400",
    "pressed_outline": "#c9d400",
    "pressed_text": "#000000",
}
DEFAULT_FONT = {"family": "Segoe UI", "size": 13, "bold": True}


def migrate(cfg):
    """Bring older config / profile dicts up to the current shape (in place)."""
    cfg.setdefault("colors", {})
    for k, v in DEFAULT_COLORS.items():
        cfg["colors"].setdefault(k, v)
    cfg.setdefault("font", {})
    for k, v in DEFAULT_FONT.items():
        cfg["font"].setdefault(k, v)
    cfg.setdefault("shape", "rect")
    if cfg.get("pad_style") not in PAD_STYLES:
        cfg["pad_style"] = "classic"
    if cfg.get("stick_style") not in STICK_STYLES:
        cfg["stick_style"] = "classic"
    cfg["stick_box"] = bool(cfg.get("stick_box", True))
    cfg.setdefault("decor", [])  # silhouettes drawn behind the pads, e.g. a mouse body
    cfg["locked"] = bool(cfg.get("locked", False))  # fixed drawing: geometry and structure are not edited
    for k in cfg.get("keys", []):
        k.setdefault("w", 1)
        k.setdefault("h", 1)
    sticks = cfg.setdefault("sticks", [])
    if "joystick" in cfg:  # single thumbstick from the first versions
        j = cfg.pop("joystick")
        if j.get("enabled", True):
            sticks.insert(0, {
                "label": "Left Stick", "col": j.get("col", 6), "row": j.get("row", 3),
                "w": j.get("cols", 2), "h": j.get("rows", 2),
                "up": j.get("up", "W"), "down": j.get("down", "S"),
                "left": j.get("left", "A"), "right": j.get("right", "D"),
                "axes": ["gp:leftx", "gp:lefty"], "click": "gp:leftstick",
            })
    for s in sticks:
        s.setdefault("w", 2)
        s.setdefault("h", 2)
        s.setdefault("label", "")
    return cfg


DEFAULT_LAYOUT_NAME = "Cyborg 2 default"


def seed_default_layouts():
    """Put the bundled default layout(s) into PROFILE_DIR. Used on first run and
    whenever the user has deleted every layout: a layout must always exist."""
    os.makedirs(PROFILE_DIR, exist_ok=True)
    for src in (os.path.join(_HERE, "profiles"), os.path.join(_DEFAULTS, "profiles")):
        if os.path.isdir(src) and os.path.abspath(src) != os.path.abspath(PROFILE_DIR):
            copied = False
            for f in os.listdir(src):
                if f.lower().endswith(".json"):
                    shutil.copy(os.path.join(src, f), os.path.join(PROFILE_DIR, f))
                    copied = True
            if copied:
                return
    # No bundled files reachable (running from a source tree whose profiles/ is
    # empty): build the default from the template instead.
    import templates
    prof = templates.azeron_profile("Cyborg II")
    with open(os.path.join(_DEFAULTS, "config.json"), encoding="utf-8") as f:
        base = json.load(f)
    for key in ("colors", "font", "opacity", "x", "y", "scale"):
        if key in base:
            prof.setdefault(key, base[key])
    migrate(prof)
    save_profile(DEFAULT_LAYOUT_NAME, prof)


def load_config():
    """Globals from config.json plus the current layout from its file. A layout
    always exists: a missing one falls back to the first on disk, an empty
    layouts folder is re-seeded, and layout data left in an old config.json is
    recovered into its own layout once. Never writes config.json itself."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    stale = {k: raw[k] for k in PROFILE_KEYS if k in raw}
    cfg = {k: v for k, v in raw.items() if k not in PROFILE_KEYS}
    if cfg.get("theme") not in ("dark", "light"):
        cfg["theme"] = "dark"
    cfg.setdefault("hotkeys", {})
    cfg["hotkeys"].setdefault("toggle", "O")
    cfg["hotkeys"].setdefault("settings", "S")
    cfg["hotkeys"].setdefault("quit", "Q")
    cfg["hotkeys"].setdefault("edit", "E")
    if not list_profiles():
        if stale.get("keys"):
            migrate(stale)
            cfg["profile"] = save_profile("Recovered", stale)
        else:
            seed_default_layouts()
    names = list_profiles()
    current = cfg.get("profile", "")
    candidates = ([current] if current in names else []) + [n for n in names if n != current]
    cfg["profile"] = ""
    for name in candidates:
        try:
            data = load_profile(name)
        except (OSError, ValueError):
            continue
        cfg.update({key: data[key] for key in PROFILE_KEYS if key in data})
        cfg["profile"] = name
        break
    return cfg  # stale layout data in config.json is dropped by the next save


def save_config(cfg):
    """Write the current layout to its file and only globals to config.json."""
    data = {k: v for k, v in cfg.items() if k not in PROFILE_KEYS}
    if cfg.get("profile"):
        data["profile"] = save_profile(cfg["profile"], cfg)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG_PATH)


def sanitise_layout_name(name):
    """The file stem a layout name becomes: filename-illegal characters dropped, trimmed."""
    return "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip()


def _profile_path(name):
    safe = sanitise_layout_name(name)
    if not safe:
        raise ValueError("invalid layout name")
    return os.path.join(PROFILE_DIR, safe + ".json")


def list_profiles():
    if not os.path.isdir(PROFILE_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(PROFILE_DIR) if f.lower().endswith(".json"))


def load_profile(name):
    with open(_profile_path(name), encoding="utf-8") as f:
        return migrate(json.load(f))


def save_profile(name, cfg):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    data = {k: cfg[k] for k in PROFILE_KEYS if k in cfg}
    path = _profile_path(name)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(path + ".tmp", path)
    return os.path.splitext(os.path.basename(path))[0]


def delete_profile(name):
    try:
        os.remove(_profile_path(name))
    except FileNotFoundError:
        pass


def layout_name_key(name):
    """What makes two layout names the same: the sanitised file stem, case-folded.
    Empty when nothing legal is left, so such a name is never "taken"."""
    return sanitise_layout_name(name).casefold()


def layout_name_taken(name, exclude=None):
    """True if a layout with this name (by key) exists, ignoring `exclude`."""
    key = layout_name_key(name)
    skip = layout_name_key(exclude) if exclude else None
    return any(layout_name_key(n) == key for n in list_profiles() if layout_name_key(n) != skip)


def unique_layout_name(name):
    """`name`, or `name (2)`, `name (3)`, ... until it is free."""
    base = sanitise_layout_name(name) or name
    if not layout_name_taken(base):
        return base
    n = 2
    while layout_name_taken(f"{base} ({n})"):
        n += 1
    return f"{base} ({n})"


def create_profile(name, cfg):
    """Save `cfg` as a new layout, never overwriting an existing name."""
    return save_profile(unique_layout_name(name), cfg)


def rename_profile(old, new):
    """Rename a layout file. Raises ValueError when `new` is taken by another layout."""
    new = new.strip()
    if layout_name_taken(new, exclude=old):
        raise ValueError(f"A layout named '{new}' already exists")
    src, dst = _profile_path(old), _profile_path(new)
    if os.path.abspath(src) != os.path.abspath(dst):
        os.replace(src, dst)
    return os.path.splitext(os.path.basename(dst))[0]


KEY_TEXT_FLAGS = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
STICK_LABEL_FLAGS = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight


def key_text_rect(rect, shape="rect"):
    """Keep labels inside the border, including on circular buttons."""
    area = rect.adjusted(3, 2, -3, -2)
    if shape.startswith("mouse_"):  # the label sits under the domed top
        area.adjust(0, area.height() * 0.3, 0, 0)
    if shape in ("paddle_l", "paddle_r"):  # label sits in the pill's waist
        side = min(area.width(), area.height())
        return QRectF(area.center().x() - side / 2, area.center().y() - side / 2, side, side)
    if shape == "circle":
        inset_x = area.width() * (1 - 2 ** -0.5) / 2
        inset_y = area.height() * (1 - 2 ** -0.5) / 2
        area.adjust(inset_x, inset_y, -inset_x, -inset_y)
    return area


def fit_key_font(text, requested_font, rect, device=None):
    """Cap this label's font independently, using the same wrapping as drawing."""
    font = QFont(requested_font)
    if not text:
        return font
    low, high = 1, max(1, int(requested_font.pointSizeF()))
    best = 1
    while low <= high:
        size = (low + high) // 2
        font.setPointSize(size)
        bounds = QFontMetricsF(font, device).boundingRect(rect, KEY_TEXT_FLAGS, text)
        if bounds.width() <= rect.width() and bounds.height() <= rect.height():
            best = size
            low = size + 1
        else:
            high = size - 1
    font.setPointSize(best)
    return font


def mix(a, b, t):
    """Linear blend of two QColors, alpha included."""
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def mouse_button_path(rect, left, full=False):
    """A mouse button: straight inner edge, small bottom corners, and a wide arc over the
    outer top corner. The arc is a quarter of the ellipse that the whole mouse body would
    have (radius 1.25 x the button width, or the width itself for a two-button mouse), so
    left and right buttons meet the body outline drawn behind them."""
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    rb = min(w, h) * 0.18
    rx, ry = (w if full else w * 1.25), h * 0.55
    start = math.degrees(math.acos(max(-1.0, min(1.0, (w - rx) / rx))))  # where the arc meets the inner edge
    path = QPainterPath()
    path.moveTo(x + rb, y + h)
    path.lineTo(x + w - rb, y + h)
    path.arcTo(x + w - 2 * rb, y + h - 2 * rb, 2 * rb, 2 * rb, 270, 90)
    path.lineTo(x + w, y + ry - ry * math.sin(math.radians(start)))
    path.arcTo(x, y, 2 * rx, 2 * ry, start, 180 - start)
    path.lineTo(x, y + h - rb)
    path.arcTo(x, y + h - 2 * rb, 2 * rb, 2 * rb, 180, 90)
    path.closeSubpath()
    if not left:
        path = QTransform().translate(2 * x + w, 0).scale(-1, 1).map(path)
    return path


def shape_path(rect, shape, radius):
    path = QPainterPath()
    if shape in ("circle", "dot"):
        path.addEllipse(rect)
    elif shape.startswith("mouse_"):
        path = mouse_button_path(rect, left=shape.startswith("mouse_left"), full=shape.endswith("_full"))
    elif shape in ("paddle_l", "paddle_r"):  # pill tilted 18° away from the controller's centre line
        r = min(rect.width(), rect.height()) / 2
        pill = QPainterPath()
        pill.addRoundedRect(rect, r, r)
        cx, cy = rect.center().x(), rect.center().y()
        t = QTransform().translate(cx, cy).rotate(-18 if shape == "paddle_l" else 18).translate(-cx, -cy)
        path = t.map(pill)
    else:
        path.addRoundedRect(rect, radius, radius)
    return path


# Xbox body outline, authored in a 400 x 372 unit frame
# (docs/superpowers/specs/2026-09-13-xbox-silhouette-design.md).
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
    """The body path scaled into rect, plus the unit -> pixel factors."""
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


def draw_pad(p, rect, shape, style, radius, c, t):
    """Paint the glow and body of one key at lit level t (0..1) in the given pad style.
    Shared by the overlay and the settings preview. Returns the color for its label."""
    if style == "pill" and shape != "circle":
        radius = min(rect.width(), rect.height()) / 2
    outline = mix(c["idle_outline"], c["pressed_outline"], t)
    text = mix(c["idle_text"], c["pressed_text"], t)
    body = shape_path(rect, shape, radius)
    if t > 0.02 and style != "underline":  # soft glow behind lit keys
        glow = QColor(c["pressed_outline"])
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i, spread in enumerate((6, 3)):
            glow.setAlphaF(0.18 * t / (i + 1))
            p.setPen(QPen(glow, spread * 2))
            p.drawPath(body)
    if style == "outline":  # see-through until pressed
        fill = QColor(c["pressed_fill"])
        fill.setAlphaF(t)
        p.setBrush(QBrush(fill))
        p.setPen(QPen(outline, 1.2 + t))
        p.drawPath(body)
    elif style == "keycap":  # dark rim with a raised, lighter face
        p.setBrush(QBrush(mix(c["idle_fill"].darker(150), c["pressed_fill"].darker(130), t)))
        p.setPen(QPen(outline, 1.2 + t))
        p.drawPath(body)
        inset = max(3.0, min(rect.width(), rect.height()) * 0.10)
        face = rect.adjusted(inset, inset * 0.6, -inset, -inset * 1.6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(mix(c["idle_fill"].lighter(140), c["pressed_fill"], t)))
        p.drawPath(shape_path(face, shape, max(1.0, radius * 0.7)))
    elif style == "underline":  # flat tile, no border; the fill and a bar along the bottom carry the state
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(mix(c["idle_fill"], c["pressed_fill"], t)))
        p.drawPath(body)
        bar_h = max(2.0, rect.height() * 0.08)
        faint = QColor(c["idle_outline"])
        faint.setAlpha(110)
        p.save()
        p.setClipPath(body)
        p.setBrush(QBrush(mix(faint, c["pressed_outline"], t)))
        p.drawRect(QRectF(rect.x(), rect.bottom() - bar_h, rect.width(), bar_h))
        p.restore()
    else:  # classic, pill
        p.setBrush(QBrush(mix(c["idle_fill"], c["pressed_fill"], t)))
        p.setPen(QPen(outline, 1.2 + t))
        p.drawPath(body)
    return text


class Pad:
    """One drawable element: a key, a controller button, or a stick direction."""

    def __init__(self, label, rect, alts, shape="rect", source=None, axis=None):
        self.label = label
        self.rect = rect
        self.alts = alts  # from parse_input
        self.shape = shape  # "rect" | "circle" | "key" | "dot" | "letter" | "petal"
        self.path = None  # QPainterPath for non-rectangular pads (petals)
        self.source = source  # ("key", index) or ("stick", index, "up"|"down"|"left"|"right")
        self.axis = axis  # analog input id whose value drives level (triggers)
        self.level = 0.0  # 0 idle .. 1 fully lit
        self.text_pos = None

    def bound(self):
        return bool(self.alts)


class Stick:
    """Thumbstick / d-pad: ring, knob (moved by axes), optional direction dots."""

    def __init__(self, rect, spec, index):
        self.rect = rect
        self.spec = spec
        self.index = index
        self.axes = spec.get("axes") or []
        self.click = parse_input(spec.get("click", "")) if spec.get("click") else []
        self.offset = QPointF(0, 0)
        self.level = 0.0


class Overlay(QWidget):
    FADE_MS = 140
    SCALE_MIN, SCALE_MAX = 0.2, 3.0

    config_changed = Signal()  # emitted when the overlay itself edits cfg (drag / wheel / rebind)
    edit_mode_changed = Signal(bool)  # edit mode entered / left, by button, tray, hotkey, Esc, or focus loss
    key_captured = Signal(object)  # token of the next input pressed while capturing
    open_settings = Signal()

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.pressed = set()
        self.axes = {}
        self.events = queue.Queue()
        self.pads = []
        self.sticks = []
        self.edit_mode = False
        self.capturing = False
        self.capture_pad = None  # pad being rebound by clicking it in edit mode
        self._drag_origin = None
        self._press_pos = None
        self._scene = None  # offscreen image the scene is painted into (see paintEvent)
        self.gamepad = Gamepad()
        self._gp_pressed = set()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.apply()

        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.daemon = True
        self.listener.start()
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        self._pulses = {}  # pseudo key -> time it releases (scroll ticks)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

        self.last_tick = time.monotonic()
        self.tick = QTimer(self)
        self.tick.setInterval(16)
        self.tick.timeout.connect(self.pump)
        self.tick.start()

        self.top_timer = QTimer(self)
        self.top_timer.setInterval(2000)
        self.top_timer.timeout.connect(self.keep_on_top)
        self.top_timer.start()

    # ---- config -> geometry -------------------------------------------
    def apply(self):
        """Rebuild everything from self.cfg. Call after any config edit."""
        cfg = self.cfg
        s = cfg.get("scale", 1.0)
        self.cw = cfg["cell_w"] * s
        self.ch = cfg["cell_h"] * s
        self.gap = cfg["gap"] * s
        self.radius = min(10 * s, self.cw * 0.2, self.ch * 0.2)
        fnt = cfg.get("font", DEFAULT_FONT)
        self.font = QFont(fnt.get("family", "Segoe UI"), max(4, int(fnt.get("size", 13) * s)),
                          QFont.Weight.Bold if fnt.get("bold", True) else QFont.Weight.Normal)
        self.col = {k: QColor(v) for k, v in cfg["colors"].items()}

        old = {p.source: p.level for p in self.pads}
        self.pads, self.sticks, self.decor = [], [], []
        self.build()
        for p in self.pads:
            p.level = old.get(p.source, 0.0)
            if p.shape not in TEXT_SHAPES:
                p.text_rect = key_text_rect(p.rect, p.shape)
                p.font = fit_key_font(p.label, self.font, p.text_rect, self)
                p.capture_font = fit_key_font("press\na key", self.font, p.text_rect, self)
        self.layout_stick_labels()

        self.hotkeys = {name: vks_for_label(cfg["hotkeys"].get(name, ""))
                        for name in ("toggle", "quit", "settings", "edit")}
        self.setWindowOpacity(1.0)  # opacity is painted per pad (see paintEvent), never on the window
        w, h = self.extent()
        pulled = visible_position(cfg["x"], cfg["y"], int(w), int(h), screen_rects())
        moved = pulled != (cfg["x"], cfg["y"])
        cfg["x"], cfg["y"] = pulled
        self.setGeometry(cfg["x"], cfg["y"], int(w), int(h))
        self.update()
        if moved:
            self.config_changed.emit()  # settings shows the pulled-back position, not the typed one

    def cell_rect(self, col, row, w=1, h=1):
        x0 = col * (self.cw + self.gap) + 2
        y0 = row * (self.ch + self.gap) + 2
        return QRectF(x0, y0, w * (self.cw + self.gap) - self.gap, h * (self.ch + self.gap) - self.gap)

    def extent(self):
        rects = ([p.rect for p in self.pads if p.source and p.source[0] == "key"] + [s.rect for s in self.sticks]
                 + [r for _kind, r in self.decor])
        if not rects:
            return 40, 40
        return max(r.right() for r in rects) + 4, max(r.bottom() for r in rects) + 4

    def build(self):
        default_shape = self.cfg.get("shape", "rect")
        for d in self.cfg.get("decor", []):
            self.decor.append((d.get("kind", "mouse"), self.cell_rect(d["col"], d["row"], d.get("w", 1), d.get("h", 1))))
        for i, k in enumerate(self.cfg["keys"]):
            try:
                alts = pad_inputs(k)
            except ValueError:
                alts = []
            rect = self.cell_rect(k["col"], k["row"], k.get("w", 1), k.get("h", 1))
            self.pads.append(Pad(k["label"], rect, alts, shape=k.get("shape", default_shape),
                                 source=("key", i), axis=k.get("axis")))

        style = self.cfg.get("stick_style", "classic")
        for i, spec in enumerate(self.cfg.get("sticks", [])):
            rect = self.cell_rect(spec["col"], spec["row"], spec.get("w", 2), spec.get("h", 2))
            stick = Stick(rect, spec, i)
            self.sticks.append(stick)
            for name, dx, dy in STICK_DIRS:
                inp = spec.get(name)
                if not inp:
                    continue
                try:
                    alts = parse_input(inp)
                except ValueError:
                    alts = []
                label = spec.get(name + "_label") or (GAMEPAD_LABELS.get(inp, inp) if is_gamepad_input(inp) else inp)
                pad = self.direction_pad(style, stick, label, alts, dx, dy)
                pad.source = ("stick", i, name)
                self.pads.append(pad)

    @staticmethod
    def stick_radius(st):
        """Radius of the ring / pad area that the direction pads are laid out around."""
        return min(st.rect.width(), st.rect.height()) * 0.30

    def direction_pad(self, style, st, label, alts, dx, dy):
        """One direction of a stick, shaped for the chosen style. Sizes are relative to the
        stick's shorter side so every style stays inside its cell at any scale."""
        cx, cy = st.rect.center().x(), st.rect.center().y()
        m = min(st.rect.width(), st.rect.height())
        rad = self.stick_radius(st)
        if style == "petals":  # wedge keys around a small analog dot
            r0, r1, half = m * 0.10, rad, math.radians(36)
            ang = math.atan2(dy, dx)
            path = QPainterPath()
            corners = ((ang - half, r0), (ang - half, r1), (ang, r1 + m * 0.04), (ang + half, r1), (ang + half, r0))
            for j, (a, r) in enumerate(corners):
                pt = QPointF(cx + r * math.cos(a), cy + r * math.sin(a))
                if j == 0:
                    path.moveTo(pt)
                else:
                    path.lineTo(pt)
            path.closeSubpath()
            pad = Pad(label, path.boundingRect(), alts, shape="petal")
            pad.path = path
            pad.text_pos = QPointF(cx + dx * m * 0.22, cy + dy * m * 0.22)
        elif style == "keys":  # the bindings drawn as real keys in a cross
            kw, kh, off = m * 0.26, m * 0.19, m * 0.24
            pad = Pad(label, QRectF(cx + dx * off - kw / 2, cy + dy * off - kh / 2, kw, kh), alts, shape="key")
        elif style in ("ring", "vector"):  # letters outside the ring; the rect is only the hit area
            side = m * 0.18
            px, py = cx + dx * (rad + m * 0.10), cy + dy * (rad + m * 0.10)
            pad = Pad(label, QRectF(px - side / 2, py - side / 2, side, side), alts, shape="letter")
            pad.text_pos = QPointF(px, py)
        else:  # classic: dots inside the ring, letters beyond it
            dot_r = rad * 0.30
            px, py = cx + dx * rad * 0.62, cy + dy * rad * 0.62
            pad = Pad(label, QRectF(px - dot_r, py - dot_r, 2 * dot_r, 2 * dot_r), alts, shape="dot")
            pad.text_pos = QPointF(cx + dx * rad * 1.4, cy + dy * rad * 1.4)
        return pad

    def stick_heading(self, st):
        """Where a stick points: (degrees, 0 = right and 90 = down on screen; strength 0..1).
        Analog axes win; otherwise the most-lit direction pad of that stick."""
        ox, oy = st.offset.x(), st.offset.y()
        mag = math.hypot(ox, oy)
        if mag > 0.15:
            return math.degrees(math.atan2(oy, ox)), min(1.0, mag)
        best, level = None, 0.0
        for pad in self.pads:
            if pad.source and pad.source[0] == "stick" and pad.source[1] == st.index and pad.level > level:
                best, level = pad.source[2], pad.level
        if best is None:
            return 0.0, 0.0
        dx, dy = STICK_VECTORS[best]
        return math.degrees(math.atan2(dy, dx)), level

    def layout_stick_labels(self):
        """Hide stick names when their rendered text would cover an input."""
        self.stick_label_font = QFont(self.font.family(), max(4, int(self.font.pointSize() * 0.75)))
        label_metrics = QFontMetricsF(self.stick_label_font, self)
        input_metrics = QFontMetrics(self.font, self)
        obstacles = [pad.rect for pad in self.pads]
        for pad in self.pads:
            if pad.shape in TEXT_SHAPES:
                # Cache the same baseline used to paint direction labels.
                pad.text_origin = QPointF(
                    pad.text_pos.x() - input_metrics.horizontalAdvance(pad.label) / 2,
                    pad.text_pos.y() + input_metrics.ascent() / 2 - 1,
                )
                if pad.label:
                    obstacles.append(QRectF(input_metrics.boundingRect(pad.label)).translated(pad.text_origin))
        for st in self.sticks:
            rad = self.stick_radius(st)
            # Include the full travel of an analog knob, so moving it cannot
            # make a visible name collide or flicker.
            reach = rad * (1.02 if st.axes else 1)
            center = st.rect.center()
            obstacles.append(QRectF(center.x() - reach, center.y() - reach, 2 * reach, 2 * reach))
        for st in self.sticks:
            st.label_rect = st.rect.adjusted(6, 4, -6, -4)
            label = st.spec.get("label", "")
            bounds = label_metrics.boundingRect(st.label_rect, STICK_LABEL_FLAGS, label)
            st.label_visible = bool(label) and st.label_rect.contains(bounds) and not any(
                bounds.adjusted(-2, -2, 2, 2).intersects(obstacle) for obstacle in obstacles
            )

    # ---- painting -----------------------------------------------------
    mix = staticmethod(mix)

    def _draw_shape(self, p, pad):
        p.drawPath(pad.path if pad.path is not None else shape_path(pad.rect, pad.shape, self.radius))

    def element_opacity(self, level=0.0):
        """Idle elements sit at the chosen opacity; a lit one rises to solid so a pressed key
        always shows at full strength whatever the slider says. Editing paints everything solid."""
        base = 1.0 if self.edit_mode else float(self.cfg.get("opacity", 0.85))
        return base + (1.0 - base) * max(0.0, min(1.0, level))

    def paintEvent(self, _event):
        """Two passes: the scene is painted solid into an image, drawn at the idle opacity,
        then every lit pad or stick region is drawn again at its level. Drawing a region at
        opacity a and then b composes to 1-(1-a)(1-b), so a second pass at `level` lands
        exactly on element_opacity(level) with no layer compounding inside a pad."""
        dpr = self.devicePixelRatio()
        size = self.size() * dpr
        if self._scene is None or self._scene.size() != size:
            self._scene = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
            self._scene.setDevicePixelRatio(dpr)
        self._scene.fill(Qt.GlobalColor.transparent)
        sp = QPainter(self._scene)
        self._paint_scene(sp)
        sp.end()
        p = QPainter(self)
        base = self.element_opacity()
        p.setOpacity(base)
        p.drawImage(QPointF(0, 0), self._scene)
        if base < 1.0:
            lit = [(pad.rect, pad.level) for pad in self.pads if pad.level > 0.01]
            lit += [(st.rect, max(st.level, min(1.0, math.hypot(st.offset.x(), st.offset.y()))))
                    for st in self.sticks if max(st.level, math.hypot(st.offset.x(), st.offset.y())) > 0.01]
            for rect, level in lit:
                area = rect.adjusted(-8, -8, 8, 8)  # glow spills a few px past the pad
                source = QRectF(area.x() * dpr, area.y() * dpr, area.width() * dpr, area.height() * dpr)
                p.setOpacity(min(1.0, level))
                p.drawImage(area, self._scene, source)
        p.end()

    def _paint_scene(self, p):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self.font)
        c = self.col

        style = self.cfg.get("stick_style", "classic")
        box = self.cfg.get("stick_box", True)
        pad_style = self.cfg.get("pad_style", "classic")

        for kind, rect in self.decor:  # silhouettes sit behind everything, outlined faintly
            faint = QColor(c["idle_outline"])
            faint.setAlpha(120)
            p.setBrush(QBrush(c["idle_fill"]))
            p.setPen(QPen(faint, 1.2))
            p.drawPath(decor_path(kind, rect))

        for st in self.sticks:
            cx, cy = st.rect.center().x(), st.rect.center().y()
            m = min(st.rect.width(), st.rect.height())
            rad = self.stick_radius(st)
            ox, oy = st.offset.x(), st.offset.y()
            mag = min(1.0, math.hypot(ox, oy))
            if box:
                p.setBrush(QBrush(c["idle_fill"]))
                p.setPen(QPen(c["idle_outline"], 1.2))
                p.drawRoundedRect(st.rect, self.radius, self.radius)
            if style == "classic":
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(c["idle_outline"], 1.2))
                p.drawEllipse(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad))
                if st.axes:  # analog knob
                    kx, ky = cx + ox * rad * 0.6, cy + oy * rad * 0.6
                    kr = rad * 0.42
                    p.setBrush(QBrush(self.mix(c["idle_outline"], c["pressed_fill"], st.level)))
                    p.setPen(QPen(self.mix(c["idle_outline"], c["pressed_outline"], st.level), 1.2))
                    p.drawEllipse(QRectF(kx - kr, ky - kr, 2 * kr, 2 * kr))
            elif style == "ring":  # faint ring with ticks; deflection lights an arc and trails the knob
                ring = QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad)
                faint = QColor(c["idle_outline"])
                faint.setAlpha(100)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(faint, 1.2))
                p.drawEllipse(ring)
                faint.setAlpha(150)
                p.setPen(QPen(faint, 1.2))
                for _name, dx, dy in STICK_DIRS:
                    p.drawLine(QPointF(cx + dx * (rad - m * 0.03), cy + dy * (rad - m * 0.03)),
                               QPointF(cx + dx * (rad + m * 0.03), cy + dy * (rad + m * 0.03)))
                heading, strength = self.stick_heading(st)
                if strength > 0.02:
                    start, span = int((-heading - 35) * 16), 70 * 16
                    lit = QColor(c["pressed_outline"])
                    lit.setAlphaF(0.25 * strength)
                    p.setPen(QPen(lit, m * 0.09, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    p.drawArc(ring, start, span)
                    lit.setAlphaF(strength)
                    p.setPen(QPen(lit, m * 0.032, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    p.drawArc(ring, start, span)
                kx, ky = cx + ox * rad * 0.55, cy + oy * rad * 0.55
                if mag > 0.05:
                    trail = QColor(c["pressed_outline"])
                    trail.setAlpha(150)
                    p.setPen(QPen(trail, 2))
                    p.drawLine(QPointF(cx, cy), QPointF(kx, ky))
                kr = m * 0.07
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(self.mix(c["idle_outline"], c["pressed_fill"], max(st.level, mag))))
                p.drawEllipse(QRectF(kx - kr, ky - kr, 2 * kr, 2 * kr))
            elif style == "vector":  # round pad with a crosshair; the knob drags a line from the centre
                p.setBrush(QBrush(c["idle_fill"]))
                p.setPen(QPen(c["idle_outline"], 1.2))
                p.drawEllipse(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad))
                faint = QColor(c["idle_outline"])
                faint.setAlpha(75)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(faint, 1))
                p.drawLine(QPointF(cx - rad, cy), QPointF(cx + rad, cy))
                p.drawLine(QPointF(cx, cy - rad), QPointF(cx, cy + rad))
                p.drawEllipse(QRectF(cx - rad / 2, cy - rad / 2, rad, rad))
                kx, ky = cx + ox * rad * 0.7, cy + oy * rad * 0.7
                if mag > 0.05:
                    p.setPen(QPen(c["pressed_outline"], 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                    p.drawLine(QPointF(cx, cy), QPointF(kx, ky))
                t = max(st.level, mag)
                kr = m * 0.085
                p.setBrush(QBrush(self.mix(c["idle_fill"], c["pressed_fill"], t)))
                p.setPen(QPen(self.mix(c["idle_outline"], c["pressed_outline"], t), 1.2 + t))
                p.drawEllipse(QRectF(kx - kr, ky - kr, 2 * kr, 2 * kr))
            else:  # petals / keys: the direction pads carry the shapes; a small analog dot sits in the middle
                reach = m * (0.05 if style == "petals" else 0.04)
                kr = m * (0.06 if style == "petals" else 0.05)
                kx, ky = cx + ox * reach, cy + oy * reach
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(self.mix(c["idle_outline"], c["pressed_fill"], max(st.level, mag))))
                p.drawEllipse(QRectF(kx - kr, ky - kr, 2 * kr, 2 * kr))
            if st.label_visible:
                p.setPen(c["idle_text"])
                p.setFont(self.stick_label_font)
                p.drawText(st.label_rect, STICK_LABEL_FLAGS, st.spec["label"])
                p.setFont(self.font)

        for pad in self.pads:
            if pad is self.capture_pad:
                hot = QColor(c["pressed_outline"])
                p.setBrush(QBrush(QColor(hot.red(), hot.green(), hot.blue(), 60)))
                p.setPen(QPen(hot, 2, Qt.PenStyle.DashLine))
                self._draw_shape(p, pad)
                if pad.shape not in TEXT_SHAPES:
                    p.setPen(hot)
                    p.setFont(pad.capture_font)
                    p.drawText(pad.text_rect, KEY_TEXT_FLAGS, "press\na key")
                continue
            if not pad.label and not pad.bound():
                if self.edit_mode:  # show unassigned pads faintly so they can be clicked and bound
                    ghost = QColor(c["idle_outline"])
                    ghost.setAlpha(90)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(ghost, 1, Qt.PenStyle.DashLine))
                    self._draw_shape(p, pad)
                continue

            t = pad.level
            if pad.shape not in TEXT_SHAPES:  # keys, buttons and the key-cross directions
                p.setPen(draw_pad(p, pad.rect, pad.shape, pad_style, self.radius, c, t))
                p.setFont(pad.font)
                p.drawText(pad.text_rect, KEY_TEXT_FLAGS, pad.label)
                continue
            fill = self.mix(c["idle_fill"], c["pressed_fill"], t)
            outline = self.mix(c["idle_outline"], c["pressed_outline"], t)
            text = self.mix(c["idle_text"], c["pressed_text"], t)

            if t > 0.02 and pad.shape != "letter":  # soft glow behind lit keys
                glow = QColor(c["pressed_outline"])
                for i, spread in enumerate((6, 3)):
                    glow.setAlphaF(0.18 * t / (i + 1))
                    p.setPen(QPen(glow, spread * 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    self._draw_shape(p, pad)

            if pad.shape != "letter":  # a letter pad is only its label
                p.setBrush(QBrush(fill))
                p.setPen(QPen(outline, 1.2 + t))
                self._draw_shape(p, pad)
            if pad.shape in ("dot", "letter"):
                p.setFont(self.font)
                p.setPen(self.mix(c["idle_text"], c["pressed_outline"], t))
                p.drawText(pad.text_origin, pad.label)
            elif pad.shape == "petal":
                p.setFont(self.font)
                p.setPen(text)
                p.drawText(pad.text_origin, pad.label)
            else:
                p.setPen(text)
                p.setFont(pad.font)
                p.drawText(pad.text_rect, KEY_TEXT_FLAGS, pad.label)

        if self.edit_mode:
            frame = QColor(c["pressed_outline"])
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(frame, 2, Qt.PenStyle.DashLine))
            p.drawRect(self.rect().adjusted(1, 1, -2, -2))
            hint = self.edit_hint()
            p.setFont(QFont("Segoe UI", 9))
            flags = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap
            avail = QRectF(6, 8, self.width() - 12, self.height() - 12)
            need = p.boundingRect(avail, flags, hint)
            bar = QRectF(need.x() - 8, need.y() - 3, need.width() + 16, need.height() + 6)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 190))
            p.drawRoundedRect(bar, 5, 5)
            p.setPen(frame)
            p.drawText(need, flags, hint)

    # ---- edit mode: drag to move, wheel to scale, click to rebind -------
    def edit_hint(self):
        key = self.cfg.get("hotkeys", {}).get("edit", "E")
        return (f"drag: move  ·  wheel: resize  ·  click a key, then press its button: rebind  "
                f"·  right-click: clear  ·  done: Ctrl+Alt+{key} or Esc")

    def toggle_edit_mode(self):
        """Hotkey / tray entry point: enter edit mode (showing the overlay first) or leave it."""
        if self.edit_mode:
            self.set_edit_mode(False)
        else:
            self.show()
            self.set_edit_mode(True)

    def keyPressEvent(self, e):
        if self.edit_mode and e.key() == Qt.Key.Key_Escape:
            self.set_edit_mode(False)
            return
        super().keyPressEvent(e)

    def set_edit_mode(self, on):
        if on == self.edit_mode:
            return
        self.edit_mode = on
        if not on:
            self.capture_pad = None
            self.capturing = False
            self._drag_origin = None  # a drag cut short by leaving edit mode must not resume later
            self._press_pos = None
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not on)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, not on)
        if was_visible:
            self.show()
        self.setCursor(Qt.CursorShape.SizeAllCursor if on else Qt.CursorShape.ArrowCursor)
        self.update()
        self.edit_mode_changed.emit(on)

    def pad_at(self, pos):
        for pad in self.pads:
            if pad.rect.contains(pos):
                return pad
        return None

    def pad_editable(self, pad):
        """Clicking this pad in edit mode may rebind it: every pad on a free layout, flagged pads on a locked one."""
        if pad is None or not pad.source:
            return False
        if not self.cfg.get("locked"):
            return True
        return pad.source[0] == "key" and bool(self.cfg["keys"][pad.source[1]].get("editable"))

    def mousePressEvent(self, e):
        if not self.edit_mode:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            # Global, not local: while dragging the window follows the cursor, so the
            # local point is the same on press and release even after a long drag.
            self._press_pos = e.globalPosition()
            self._drag_origin = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif e.button() == Qt.MouseButton.RightButton:
            pad = self.pad_at(e.position())
            self.capture_pad = None
            self.capturing = False
            if self.pad_editable(pad) and pad.source[0] == "key":
                self.set_pad_input(pad, "", clear_label=True)
            self.update()

    def mouseMoveEvent(self, e):
        if self.edit_mode and self._drag_origin is not None:
            self.move(e.globalPosition().toPoint() - self._drag_origin)
            # Keep cfg current mid-drag so an apply() from elsewhere (settings
            # edits, rescale) rebuilds at the dragged spot, not the old one.
            self.cfg["x"], self.cfg["y"] = self.x(), self.y()

    def mouseReleaseEvent(self, e):
        if not self.edit_mode or self._drag_origin is None:
            return
        self._drag_origin = None
        moved = (e.globalPosition() - self._press_pos).manhattanLength() if self._press_pos else 99
        if moved < 4:
            pad = self.pad_at(e.position())
            if self.pad_editable(pad):
                self.capture_pad = pad
                self.capturing = True
            else:
                self.capture_pad = None
                self.capturing = False
            self.update()
        else:
            self.cfg["x"], self.cfg["y"] = self.x(), self.y()
            self.config_changed.emit()

    def wheelEvent(self, e):
        if not self.edit_mode:
            return
        factor = 1.08 if e.angleDelta().y() > 0 else 1 / 1.08
        s = min(self.SCALE_MAX, max(self.SCALE_MIN, self.cfg.get("scale", 1.0) * factor))
        self.cfg["scale"] = round(s, 3)
        self.apply()
        self.config_changed.emit()

    def set_pad_input(self, pad, text, clear_label=False):
        """Bind a pad to an input name. Keeps a custom (macro) label if one is set."""
        src = pad.source
        if src[0] == "key":
            k = self.cfg["keys"][src[1]]
            old_input = k.get("input", k.get("label", ""))
            k.pop("sc", None)
            k.pop("axis", None)
            k["input"] = text
            if clear_label or not k.get("label") or k.get("label") == old_input:
                k["label"] = text if not is_gamepad_input(text) else GAMEPAD_LABELS.get(text, text)
        else:
            self.cfg["sticks"][src[1]][src[2]] = text
        self.apply()
        self.config_changed.emit()

    # ---- window plumbing ----------------------------------------------
    def keep_on_top(self):
        if self.isVisible() and not self.edit_mode:
            self.raise_()

    # ---- input --------------------------------------------------------
    def on_press(self, key):
        self.events.put(("down", vk_of(key)))

    def on_release(self, key):
        self.events.put(("up", vk_of(key)))

    _MOUSE_VK = {"left": 0x01, "right": 0x02, "middle": 0x04, "x1": 0x05, "x2": 0x06}

    def on_click(self, _x, _y, button, pressed):
        vk = self._MOUSE_VK.get(getattr(button, "name", ""))
        if vk is not None:
            self.events.put(("down" if pressed else "up", vk))

    def on_scroll(self, _x, _y, _dx, dy):
        if dy:
            self.events.put(("pulse", WHEEL_UP if dy > 0 else WHEEL_DOWN))

    def _on_new_press(self, token):
        if self.capturing:
            self.capturing = False
            if self.capture_pad is not None:
                pad, self.capture_pad = self.capture_pad, None
                name = label_for_token(token) if not is_gamepad_input(token) else token
                if name is not None:
                    self.set_pad_input(pad, name)
                self.update()
            else:
                self.key_captured.emit(token)
        elif not is_gamepad_input(token):
            self.check_hotkeys(token)

    def pump(self):
        now = time.monotonic()
        dt = now - self.last_tick
        self.last_tick = now

        while True:
            try:
                kind, vk = self.events.get_nowait()
            except queue.Empty:
                break
            if vk is None:
                continue
            if kind == "down":
                if vk not in self.pressed:
                    self.pressed.add(vk)
                    self._on_new_press(vk)
            elif kind == "pulse":  # a scroll tick: held briefly, extended by further ticks
                self._pulses[vk] = now + WHEEL_HOLD_S
                if vk not in self.pressed:
                    self.pressed.add(vk)
                    self._on_new_press(vk)
            else:
                self.pressed.discard(vk)
        for vk, until in list(self._pulses.items()):
            if now >= until:
                del self._pulses[vk]
                self.pressed.discard(vk)

        gp_pressed, axes = self.gamepad.poll()
        for tok in gp_pressed - self._gp_pressed:
            self._on_new_press(tok)
        self.pressed -= self._gp_pressed
        self.pressed |= gp_pressed
        self._gp_pressed = gp_pressed
        self.axes = axes

        step = dt * 1000 / self.FADE_MS
        dirty = False
        for pad in self.pads:
            if pad.axis:
                target = max(0.0, min(1.0, self.axes.get(pad.axis, 0.0)))
                if abs(pad.level - target) > 0.01:
                    pad.level = target
                    dirty = True
                continue
            down = input_matches(pad.alts, self.pressed)
            if down and pad.level < 1.0:
                pad.level = 1.0  # instant on
                dirty = True
            elif not down and pad.level > 0.0:
                pad.level = max(0.0, pad.level - step)  # smooth off
                dirty = True
        for st in self.sticks:
            if st.axes:
                ox = self.axes.get(st.axes[0], 0.0)
                oy = self.axes.get(st.axes[1], 0.0) if len(st.axes) > 1 else 0.0
                if abs(ox - st.offset.x()) > 0.005 or abs(oy - st.offset.y()) > 0.005:
                    st.offset = QPointF(ox, oy)
                    dirty = True
            down = input_matches(st.click, self.pressed)
            if down and st.level < 1.0:
                st.level = 1.0
                dirty = True
            elif not down and st.level > 0.0:
                st.level = max(0.0, st.level - step)
                dirty = True
        if dirty:
            self.update()

    def check_hotkeys(self, vk):
        if not (self.pressed & CTRL_VKS and self.pressed & ALT_VKS):
            return
        if vk in self.hotkeys["quit"]:
            self.shutdown()
        elif vk in self.hotkeys["toggle"]:
            self.setVisible(not self.isVisible())
        elif vk in self.hotkeys["settings"]:
            self.open_settings.emit()
        elif vk in self.hotkeys["edit"]:
            self.toggle_edit_mode()

    def shutdown(self):
        self.listener.stop()
        self.mouse_listener.stop()
        QApplication.quit()


VISIBLE_MARGIN = 40  # logical px of the overlay that must stay on some screen


def screen_rects():
    return [s.geometry() for s in QGuiApplication.screens()]


def visible_position(x, y, w, h, screens, margin=VISIBLE_MARGIN):
    """(x, y) unchanged while the overlay touches any screen; otherwise the nearest
    position on the closest screen where at least `margin` px of it is visible.
    Partial off-screen placement is deliberate and left alone."""
    if not screens:
        return x, y
    rect = QRect(x, y, w, h)
    if any(rect.intersects(scr) for scr in screens):
        return x, y
    centre = rect.center()

    def distance(scr):
        dx = max(scr.left() - centre.x(), 0, centre.x() - scr.right())
        dy = max(scr.top() - centre.y(), 0, centre.y() - scr.bottom())
        return dx * dx + dy * dy

    scr = min(screens, key=distance)
    x = min(max(x, scr.left() - w + margin), scr.right() + 1 - margin)
    y = min(max(y, scr.top() - h + margin), scr.bottom() + 1 - margin)
    return x, y


def pads_in_row_or_column(keys, selected, axis):
    """Indices of every pad in the row ("row") or column ("col") of each selected pad.
    A pad belongs to a selected pad's line when its centre on that axis lies within
    the selected pad's span there, so staggered keyboard keys are not caught by a
    quarter-unit overlap while a wide pad still sweeps its whole span."""
    size = "w" if axis == "col" else "h"
    spans = [(keys[i][axis], keys[i][axis] + keys[i].get(size, 1)) for i in selected if 0 <= i < len(keys)]
    members = set()
    for i, k in enumerate(keys):
        centre = k[axis] + k.get(size, 1) / 2
        if any(lo <= centre < hi for lo, hi in spans):
            members.add(i)
    return members


def tray_menu(overlay, open_settings):
    """Tray context menu. The "Edit on screen" item mirrors the overlay's edit mode."""
    menu = QMenu()
    act_settings = QAction("Settings…", menu)
    act_settings.triggered.connect(open_settings)
    act_toggle = QAction("Show / hide overlay", menu)
    act_toggle.triggered.connect(lambda: overlay.setVisible(not overlay.isVisible()))
    act_edit = QAction("Edit on screen", menu)
    act_edit.setCheckable(True)
    act_edit.setChecked(overlay.edit_mode)
    act_edit.triggered.connect(lambda _checked: overlay.toggle_edit_mode())
    overlay.edit_mode_changed.connect(act_edit.setChecked)
    act_quit = QAction("Quit", menu)
    act_quit.triggered.connect(overlay.shutdown)
    menu.addAction(act_settings)
    menu.addAction(act_toggle)
    menu.addAction(act_edit)
    menu.addSeparator()
    menu.addAction(act_quit)
    return menu


def app_icon(color="#c9d400"):
    """The AZ logo from assets, or a drawn stand-in if the asset is missing."""
    if os.path.exists(LOGO_PATH):
        return QIcon(LOGO_PATH)
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1e1e1e"))
    p.setPen(QPen(QColor(color), 5))
    p.drawRoundedRect(6, 6, 52, 52, 12, 12)
    p.setPen(QPen(QColor(color), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolyline([QPointF(14, 44), QPointF(24, 20), QPointF(34, 44)])
    p.drawPolyline([QPointF(36, 22), QPointF(50, 22), QPointF(36, 44), QPointF(50, 44)])
    p.end()
    return QIcon(pm)


def main():
    ensure_user_data()
    try:
        cfg = load_config()
    except (OSError, ValueError) as e:
        print(f"Could not load {CONFIG_PATH}: {e}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # consistent widget rendering; stylesheet in settings_ui relies on it
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    icon = app_icon()
    app.setWindowIcon(icon)

    overlay = Overlay(cfg)
    overlay.show()

    from settings_ui import SettingsWindow  # local import keeps overlay importable in tests

    settings = SettingsWindow(overlay)
    app.aboutToQuit.connect(settings._save_now)
    overlay.open_settings.connect(settings.present)

    tray = QSystemTrayIcon(icon)
    tray.setToolTip(f"{APP_NAME} — right-click for settings")
    tray.setContextMenu(tray_menu(overlay, settings.present))
    tray.activated.connect(lambda r: settings.present() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()
    tray.showMessage(f"{APP_NAME} running", "Double-click the tray icon or press Ctrl+Alt+S for settings.",
                     icon, 3000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

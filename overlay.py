"""AZ-Overlay: transparent, click-through input overlay for the Azeron Cyborg 2,
keyboards, and Xbox / PlayStation controllers.

Qt (PySide6) window: frameless, always on top, transparent background, mouse
events pass through to the game. A global keyboard hook (pynput) plus SDL
game-controller polling light pads while they are held; releases fade out.

A tray icon opens the Settings window (see settings_ui.py) where layout, keys,
colors, position and scale are edited live and saved to config.json.

Hotkeys: Ctrl+Alt+O toggles visibility, Ctrl+Alt+S opens settings,
Ctrl+Alt+Q quits (editable in config).
"""

import ctypes
import json
import os
import queue
import shutil
import sys
import time

from pynput import keyboard, mouse
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QFontMetricsF, QIcon, QPainter, QPen, QPixmap
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
                "colors", "font", "keys", "sticks")

# ---------------------------------------------------------------------------
# Input tokens. A pad is lit when its input is held. Tokens are either Windows
# virtual-key codes (int) or gamepad ids ("gp:a"). Keyboard keys can be given
# by name ("Page Up"), or physically by scancode (templates do this so the
# highlight follows the key position on any Windows layout).
# ---------------------------------------------------------------------------
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


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    migrate(cfg)
    if cfg.get("theme") not in ("dark", "light"):
        cfg["theme"] = "dark"
    cfg.setdefault("hotkeys", {})
    cfg["hotkeys"].setdefault("toggle", "O")
    cfg["hotkeys"].setdefault("settings", "S")
    cfg["hotkeys"].setdefault("quit", "Q")
    return cfg


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG_PATH)


def _profile_path(name):
    safe = "".join(ch for ch in name if ch not in '\\/:*?"<>|').strip()
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
    with open(_profile_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def delete_profile(name):
    try:
        os.remove(_profile_path(name))
    except FileNotFoundError:
        pass


KEY_TEXT_FLAGS = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap


def key_text_rect(rect, shape="rect"):
    """Keep labels inside the border, including on circular buttons."""
    area = rect.adjusted(3, 2, -3, -2)
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


class Pad:
    """One drawable element: a key, a controller button, or a stick direction."""

    def __init__(self, label, rect, alts, shape="rect", source=None, axis=None):
        self.label = label
        self.rect = rect
        self.alts = alts  # from parse_input
        self.shape = shape  # "rect" | "circle" | "dot"
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
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
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
        self.pads, self.sticks = [], []
        self.build()
        for p in self.pads:
            p.level = old.get(p.source, 0.0)
            if p.shape != "dot":
                p.text_rect = key_text_rect(p.rect, p.shape)
                p.font = fit_key_font(p.label, self.font, p.text_rect, self)
                p.capture_font = fit_key_font("press\na key", self.font, p.text_rect, self)

        self.hotkeys = {name: vks_for_label(cfg["hotkeys"].get(name, ""))
                        for name in ("toggle", "quit", "settings")}
        if not self.edit_mode:
            self.setWindowOpacity(cfg.get("opacity", 0.85))
        w, h = self.extent()
        self.setGeometry(cfg["x"], cfg["y"], int(w), int(h))
        self.update()

    def cell_rect(self, col, row, w=1, h=1):
        x0 = col * (self.cw + self.gap) + 2
        y0 = row * (self.ch + self.gap) + 2
        return QRectF(x0, y0, w * (self.cw + self.gap) - self.gap, h * (self.ch + self.gap) - self.gap)

    def extent(self):
        rects = [p.rect for p in self.pads if p.source and p.source[0] == "key"] + [s.rect for s in self.sticks]
        if not rects:
            return 40, 40
        return max(r.right() for r in rects) + 4, max(r.bottom() for r in rects) + 4

    def build(self):
        default_shape = self.cfg.get("shape", "rect")
        for i, k in enumerate(self.cfg["keys"]):
            try:
                alts = pad_inputs(k)
            except ValueError:
                alts = []
            rect = self.cell_rect(k["col"], k["row"], k.get("w", 1), k.get("h", 1))
            self.pads.append(Pad(k["label"], rect, alts, shape=k.get("shape", default_shape),
                                 source=("key", i), axis=k.get("axis")))

        for i, spec in enumerate(self.cfg.get("sticks", [])):
            rect = self.cell_rect(spec["col"], spec["row"], spec.get("w", 2), spec.get("h", 2))
            stick = Stick(rect, spec, i)
            self.sticks.append(stick)
            cx, cy = rect.center().x(), rect.center().y()
            rad = min(rect.width(), rect.height()) * 0.30
            dot_r = rad * 0.30
            for name, dx, dy in (("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0)):
                inp = spec.get(name)
                if not inp:
                    continue
                try:
                    alts = parse_input(inp)
                except ValueError:
                    alts = []
                px, py = cx + dx * rad * 0.62, cy + dy * rad * 0.62
                label = spec.get(name + "_label") or (GAMEPAD_LABELS.get(inp, inp) if is_gamepad_input(inp) else inp)
                pad = Pad(label, QRectF(px - dot_r, py - dot_r, 2 * dot_r, 2 * dot_r), alts,
                          shape="dot", source=("stick", i, name))
                pad.text_pos = QPointF(cx + dx * rad * 1.4, cy + dy * rad * 1.4)
                self.pads.append(pad)

    # ---- painting -----------------------------------------------------
    @staticmethod
    def mix(a, b, t):
        return QColor(
            int(a.red() + (b.red() - a.red()) * t),
            int(a.green() + (b.green() - a.green()) * t),
            int(a.blue() + (b.blue() - a.blue()) * t),
            int(a.alpha() + (b.alpha() - a.alpha()) * t),
        )

    def _draw_shape(self, p, pad):
        if pad.shape == "rect":
            p.drawRoundedRect(pad.rect, self.radius, self.radius)
        else:
            p.drawEllipse(pad.rect)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self.font)
        c = self.col

        for st in self.sticks:
            p.setBrush(QBrush(c["idle_fill"]))
            p.setPen(QPen(c["idle_outline"], 1.2))
            p.drawRoundedRect(st.rect, self.radius, self.radius)
            cx, cy = st.rect.center().x(), st.rect.center().y()
            rad = min(st.rect.width(), st.rect.height()) * 0.30
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad))
            if st.axes:  # analog knob
                kx, ky = cx + st.offset.x() * rad * 0.6, cy + st.offset.y() * rad * 0.6
                kr = rad * 0.42
                p.setBrush(QBrush(self.mix(c["idle_outline"], c["pressed_fill"], st.level)))
                p.setPen(QPen(self.mix(c["idle_outline"], c["pressed_outline"], st.level), 1.2))
                p.drawEllipse(QRectF(kx - kr, ky - kr, 2 * kr, 2 * kr))
            if st.spec.get("label"):
                p.setPen(c["idle_text"])
                p.setFont(QFont(self.font.family(), max(4, int(self.font.pointSize() * 0.75))))
                p.drawText(st.rect.adjusted(6, 4, -6, -4), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                           st.spec["label"])
                p.setFont(self.font)

        for pad in self.pads:
            if pad is self.capture_pad:
                hot = QColor(c["pressed_outline"])
                p.setBrush(QBrush(QColor(hot.red(), hot.green(), hot.blue(), 60)))
                p.setPen(QPen(hot, 2, Qt.PenStyle.DashLine))
                self._draw_shape(p, pad)
                if pad.shape != "dot":
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
            fill = self.mix(c["idle_fill"], c["pressed_fill"], t)
            outline = self.mix(c["idle_outline"], c["pressed_outline"], t)
            text = self.mix(c["idle_text"], c["pressed_text"], t)

            if t > 0.02:  # soft glow behind lit keys
                glow = QColor(c["pressed_outline"])
                for i, spread in enumerate((6, 3)):
                    glow.setAlphaF(0.18 * t / (i + 1))
                    p.setPen(QPen(glow, spread * 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    self._draw_shape(p, pad)

            p.setBrush(QBrush(fill))
            p.setPen(QPen(outline, 1.2 + t))
            self._draw_shape(p, pad)
            if pad.shape == "dot":
                p.setFont(self.font)
                p.setPen(self.mix(c["idle_text"], c["pressed_outline"], t))
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(pad.label)
                p.drawText(QPointF(pad.text_pos.x() - tw / 2, pad.text_pos.y() + fm.ascent() / 2 - 1), pad.label)
            else:
                p.setPen(text)
                p.setFont(pad.font)
                p.drawText(pad.text_rect, KEY_TEXT_FLAGS, pad.label)

        if self.edit_mode:
            frame = QColor(c["pressed_outline"])
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(frame, 2, Qt.PenStyle.DashLine))
            p.drawRect(self.rect().adjusted(1, 1, -2, -2))
            hint = ("drag: move  ·  wheel: resize  ·  click a key, then press its button: rebind  "
                    "·  right-click: clear")
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
        p.end()

    # ---- edit mode: drag to move, wheel to scale, click to rebind -------
    def set_edit_mode(self, on):
        if on == self.edit_mode:
            return
        self.edit_mode = on
        if not on:
            self.capture_pad = None
            self.capturing = False
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not on)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, not on)
        self.setWindowOpacity(1.0 if on else self.cfg.get("opacity", 0.85))  # solid while editing
        if was_visible:
            self.show()
        self.setCursor(Qt.CursorShape.SizeAllCursor if on else Qt.CursorShape.ArrowCursor)
        self.update()

    def pad_at(self, pos):
        for pad in self.pads:
            if pad.rect.contains(pos):
                return pad
        return None

    def mousePressEvent(self, e):
        if not self.edit_mode:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_pos = e.position()
            self._drag_origin = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif e.button() == Qt.MouseButton.RightButton:
            pad = self.pad_at(e.position())
            self.capture_pad = None
            self.capturing = False
            if pad is not None and pad.source and pad.source[0] == "key":
                self.set_pad_input(pad, "", clear_label=True)
            self.update()

    def mouseMoveEvent(self, e):
        if self.edit_mode and self._drag_origin is not None:
            self.move(e.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, e):
        if not self.edit_mode or self._drag_origin is None:
            return
        self._drag_origin = None
        moved = (e.position() - self._press_pos).manhattanLength() if self._press_pos else 99
        if moved < 4:
            pad = self.pad_at(e.position())
            if pad is not None and pad.source:
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
            else:
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

    def shutdown(self):
        self.listener.stop()
        self.mouse_listener.stop()
        QApplication.quit()


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
    overlay.open_settings.connect(settings.present)

    tray = QSystemTrayIcon(icon)
    tray.setToolTip(f"{APP_NAME} — right-click for settings")
    menu = QMenu()
    act_settings = QAction("Settings…", menu)
    act_settings.triggered.connect(settings.present)
    act_toggle = QAction("Show / hide overlay", menu)
    act_toggle.triggered.connect(lambda: overlay.setVisible(not overlay.isVisible()))
    act_quit = QAction("Quit", menu)
    act_quit.triggered.connect(overlay.shutdown)
    menu.addAction(act_settings)
    menu.addAction(act_toggle)
    menu.addSeparator()
    menu.addAction(act_quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda r: settings.present() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()
    tray.showMessage(f"{APP_NAME} running", "Double-click the tray icon or press Ctrl+Alt+S for settings.",
                     icon, 3000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

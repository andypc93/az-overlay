"""Transparent, click-through key overlay for the Azeron Cyborg 2.

Qt (PySide6) window: frameless, always on top, transparent background, mouse
events pass through to the game. A global keyboard hook (pynput) lights keys
while held; releases fade out smoothly.

A tray icon opens the Settings window (see settings_ui.py) where layout, keys,
colors, position and scale are edited live and saved to config.json.

Hotkeys: Ctrl+Alt+O toggles visibility, Ctrl+Alt+S opens settings,
Ctrl+Alt+Q quits (editable in config).
"""

import json
import os
import queue
import sys
import time

from pynput import keyboard
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

# Frozen exe: config.json sits next to the .exe so users can edit it.
_BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_BASE, "config.json")

# Canonical label -> Windows virtual-key codes. First entry is the one shown
# when a key is captured from the keyboard.
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


def vks_for_label(label):
    """Return the set of virtual-key codes that light up a given label."""
    key = label.strip()
    if not key:
        return set()
    if key.lower() in _LOWER:
        return set(_LOWER[key.lower()])
    if len(key) == 1 and key.isalnum():
        return {ord(key.upper())}  # VK_A..VK_Z / VK_0..VK_9 equal ASCII uppercase
    raise ValueError(f"Unknown key label: {label!r}")


def label_for_vk(vk):
    """Human label for a virtual-key code, or None if we don't know it."""
    return LABEL_BY_VK.get(vk)


def vk_of(key):
    """Extract the virtual-key code from a pynput key object."""
    vk = getattr(key, "vk", None)
    if vk is None:
        vk = getattr(getattr(key, "value", None), "vk", None)
    return vk


DEFAULT_COLORS = {
    "idle_fill": "#1e1e1e",
    "idle_outline": "#c9d400",
    "idle_text": "#ffffff",
    "pressed_fill": "#c9d400",
    "pressed_outline": "#c9d400",
    "pressed_text": "#000000",
}


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("colors", {})
    for k, v in DEFAULT_COLORS.items():
        cfg["colors"].setdefault(k, v)
    cfg.setdefault("hotkeys", {}).setdefault("settings", "S")
    return cfg


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.replace(tmp, CONFIG_PATH)


class Pad:
    """One drawable element: a key cell or a joystick direction."""

    def __init__(self, label, rect, vks, shape="rect"):
        self.label = label
        self.rect = rect
        self.vks = vks
        self.shape = shape
        self.level = 0.0  # 0 idle .. 1 fully lit
        self.text_pos = None


class Overlay(QWidget):
    FADE_MS = 140
    SCALE_MIN, SCALE_MAX = 0.2, 3.0

    config_changed = Signal()  # emitted when the overlay itself edits cfg (drag / wheel)
    key_captured = Signal(int)  # vk of the next key pressed while capturing
    open_settings = Signal()

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.pressed = set()
        self.events = queue.Queue()
        self.pads = []
        self.static = []
        self.edit_mode = False
        self.capturing = False
        self._drag_origin = None

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
        self.radius = 10 * s
        self.font = QFont("Segoe UI", max(6, int(13 * s)), QFont.Weight.DemiBold)

        c = cfg["colors"]
        self.col = {k: QColor(v) for k, v in c.items()}

        old = {p.label: p.level for p in self.pads}
        self.pads, self.static = [], []
        self.build()
        for p in self.pads:
            p.level = old.get(p.label, 0.0)

        self.hotkeys = {
            name: vks_for_label(cfg["hotkeys"].get(name, ""))
            for name in ("toggle", "quit", "settings")
        }
        self.setWindowOpacity(cfg.get("opacity", 0.85))
        w, h = self.extent()
        self.setGeometry(cfg["x"], cfg["y"], int(w), int(h))
        self.update()

    def cell_rect(self, col, row, cols=1, rows=1):
        x0 = col * (self.cw + self.gap) + 2
        y0 = row * (self.ch + self.gap) + 2
        w = cols * self.cw + (cols - 1) * self.gap
        h = rows * self.ch + (rows - 1) * self.gap
        return QRectF(x0, y0, w, h)

    def extent(self):
        rects = [p.rect for p in self.pads] + [r for r, _ in self.static]
        if not rects:
            return 40, 40
        return max(r.right() for r in rects) + 4, max(r.bottom() for r in rects) + 4

    def build(self):
        for k in self.cfg["keys"]:
            try:
                vks = vks_for_label(k["label"])
            except ValueError:
                vks = set()
            self.pads.append(Pad(k["label"], self.cell_rect(k["col"], k["row"]), vks))

        j = self.cfg.get("joystick")
        if j and j.get("enabled", True):
            box = self.cell_rect(j["col"], j["row"], j.get("cols", 2), j.get("rows", 2))
            self.static.append((box, "box"))
            cx, cy = box.center().x(), box.center().y()
            rad = min(box.width(), box.height()) * 0.30
            self.static.append((QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), "ring"))
            dot_r = rad * 0.30
            for name, dx, dy in (("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0)):
                label = j.get(name, "")
                try:
                    vks = vks_for_label(label)
                except ValueError:
                    vks = set()
                px, py = cx + dx * rad * 0.62, cy + dy * rad * 0.62
                pad = Pad(label, QRectF(px - dot_r, py - dot_r, 2 * dot_r, 2 * dot_r), vks, shape="dot")
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

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self.font)
        c = self.col

        for rect, kind in self.static:
            p.setBrush(QBrush(c["idle_fill"]) if kind == "box" else Qt.BrushStyle.NoBrush)
            p.setPen(QPen(c["idle_outline"], 1.2))
            if kind == "box":
                p.drawRoundedRect(rect, self.radius, self.radius)
            else:
                p.drawEllipse(rect)

        for pad in self.pads:
            if not pad.label:
                if self.edit_mode:  # show unassigned pads faintly so they can be placed
                    ghost = QColor(c["idle_outline"])
                    ghost.setAlpha(70)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.setPen(QPen(ghost, 1, Qt.PenStyle.DashLine))
                    p.drawRoundedRect(pad.rect, self.radius, self.radius)
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
                    if pad.shape == "rect":
                        p.drawRoundedRect(pad.rect, self.radius, self.radius)
                    else:
                        p.drawEllipse(pad.rect)

            p.setBrush(QBrush(fill))
            p.setPen(QPen(outline, 1.2 + t))
            if pad.shape == "rect":
                p.drawRoundedRect(pad.rect, self.radius, self.radius)
                p.setPen(text)
                p.drawText(pad.rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, pad.label)
            else:
                p.drawEllipse(pad.rect)
                p.setPen(self.mix(c["idle_text"], c["pressed_outline"], t))
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(pad.label)
                p.drawText(QPointF(pad.text_pos.x() - tw / 2, pad.text_pos.y() + fm.ascent() / 2 - 1), pad.label)

        if self.edit_mode:
            frame = QColor(c["pressed_outline"])
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(frame, 2, Qt.PenStyle.DashLine))
            p.drawRect(self.rect().adjusted(1, 1, -2, -2))
            hint = "drag to move  ·  scroll to resize"
            p.setFont(QFont("Segoe UI", 9))
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(hint) + 16
            bar = QRectF(self.width() - tw - 4, 4, tw, fm.height() + 6)
            bg = QColor(0, 0, 0, 170)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(bar, 5, 5)
            p.setPen(frame)
            p.drawText(bar, Qt.AlignmentFlag.AlignCenter, hint)
        p.end()

    # ---- edit mode: drag to move, wheel to scale -----------------------
    def set_edit_mode(self, on):
        if on == self.edit_mode:
            return
        self.edit_mode = on
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, not on)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, not on)
        if was_visible:
            self.show()
        self.setCursor(Qt.CursorShape.SizeAllCursor if on else Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, e):
        if self.edit_mode and e.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.edit_mode and self._drag_origin is not None:
            self.move(e.globalPosition().toPoint() - self._drag_origin)

    def mouseReleaseEvent(self, e):
        if self.edit_mode and self._drag_origin is not None:
            self._drag_origin = None
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

    # ---- window plumbing ----------------------------------------------
    def keep_on_top(self):
        if self.isVisible() and not self.edit_mode:
            self.raise_()

    # ---- input --------------------------------------------------------
    def on_press(self, key):
        self.events.put(("down", vk_of(key)))

    def on_release(self, key):
        self.events.put(("up", vk_of(key)))

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
                    if self.capturing:
                        self.capturing = False
                        self.key_captured.emit(vk)
                    else:
                        self.check_hotkeys(vk)
            else:
                self.pressed.discard(vk)

        step = dt * 1000 / self.FADE_MS
        dirty = False
        for pad in self.pads:
            down = bool(pad.vks & self.pressed)
            if down and pad.level < 1.0:
                pad.level = 1.0  # instant on
                dirty = True
            elif not down and pad.level > 0.0:
                pad.level = max(0.0, pad.level - step)  # smooth off
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
        QApplication.quit()


def make_icon(color="#c9d400"):
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#1e1e1e"))
    p.setPen(QPen(QColor(color), 5))
    p.drawRoundedRect(6, 6, 52, 52, 12, 12)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(20, 20, 24, 24, 5, 5)
    p.end()
    return QIcon(pm)


def main():
    try:
        cfg = load_config()
    except (OSError, ValueError) as e:
        print(f"Could not load {CONFIG_PATH}: {e}", file=sys.stderr)
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("az-overlay")
    icon = make_icon()
    app.setWindowIcon(icon)

    overlay = Overlay(cfg)
    overlay.show()

    from settings_ui import SettingsWindow  # local import keeps overlay importable in tests

    settings = SettingsWindow(overlay)
    overlay.open_settings.connect(settings.present)

    tray = QSystemTrayIcon(icon)
    tray.setToolTip("az-overlay — right-click for settings")
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
    tray.showMessage("az-overlay running", "Double-click the tray icon or press Ctrl+Alt+S for settings.",
                     icon, 3000)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

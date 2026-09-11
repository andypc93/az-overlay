"""Transparent, click-through key overlay for the Azeron Cyborg 2.

Qt (PySide6) window: frameless, always on top, transparent background, mouse
events pass through to the game. A global keyboard hook (pynput) lights keys
while held; releases fade out smoothly.

Hotkeys: Ctrl+Alt+O toggles visibility, Ctrl+Alt+Q quits (editable in config).
"""

import json
import os
import queue
import sys
import time

from pynput import keyboard
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

# Frozen exe: config.json sits next to the .exe so users can edit it.
_BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_BASE, "config.json")

# Windows virtual-key codes for the non-character labels the Cyborg can emit.
VK_BY_LABEL = {
    "alt": [0x12, 0xA4, 0xA5],
    "shift": [0x10, 0xA0, 0xA1],
    "ctrl": [0x11, 0xA2, 0xA3],
    "space": [0x20],
    "esc": [0x1B],
    "escape": [0x1B],
    "tab": [0x09],
    "enter": [0x0D],
    "backspace": [0x08],
    "delete": [0x2E],
    "insert": [0x2D],
    "home": [0x24],
    "end": [0x23],
    "page up": [0x21],
    "page down": [0x22],
    "caps lock": [0x14],
    "up": [0x26],
    "down": [0x28],
    "left": [0x25],
    "right": [0x27],
    "win": [0x5B, 0x5C],
}
VK_BY_LABEL.update({f"f{n}": [0x6F + n] for n in range(1, 25)})

CTRL_VKS = {0x11, 0xA2, 0xA3}
ALT_VKS = {0x12, 0xA4, 0xA5}


def vks_for_label(label):
    """Return the set of virtual-key codes that light up a given label."""
    key = label.strip().lower()
    if not key:
        return set()
    if key in VK_BY_LABEL:
        return set(VK_BY_LABEL[key])
    if len(key) == 1 and key.isalnum():
        return {ord(key.upper())}  # VK_A..VK_Z / VK_0..VK_9 equal ASCII uppercase
    raise ValueError(f"Unknown key label: {label!r}")


def vk_of(key):
    """Extract the virtual-key code from a pynput key object."""
    vk = getattr(key, "vk", None)
    if vk is None:
        vk = getattr(getattr(key, "value", None), "vk", None)
    return vk


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


class Pad:
    """One drawable element: a key cell or a joystick direction."""

    def __init__(self, label, rect, vks, shape="rect"):
        self.label = label
        self.rect = rect
        self.vks = vks
        self.shape = shape
        self.level = 0.0  # 0 idle .. 1 fully lit
        self.down = False


class Overlay(QWidget):
    FADE_MS = 140

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.pressed = set()
        self.events = queue.Queue()
        self.pads = []
        self.static = []  # (path, pen, brush) drawn once, never animated

        s = cfg.get("scale", 1.0)
        self.cw = cfg["cell_w"] * s
        self.ch = cfg["cell_h"] * s
        self.gap = cfg["gap"] * s
        self.radius = 10 * s
        self.font = QFont("Segoe UI", max(6, int(13 * s)), QFont.Weight.DemiBold)

        c = cfg["colors"]
        self.idle_fill = QColor(c["idle_fill"])
        self.idle_outline = QColor(c["idle_outline"])
        self.pressed_fill = QColor(c["pressed_fill"])
        self.idle_text = QColor(c["idle_text"])
        self.pressed_text = QColor(c["pressed_text"])

        self.build()
        w, h = self.extent()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowOpacity(cfg.get("opacity", 0.85))
        self.setGeometry(cfg["x"], cfg["y"], int(w), int(h))

        self.hotkeys = {
            "toggle": vks_for_label(cfg["hotkeys"]["toggle"]),
            "quit": vks_for_label(cfg["hotkeys"]["quit"]),
        }
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

    # ---- geometry -----------------------------------------------------
    def cell_rect(self, col, row, cols=1, rows=1):
        x0 = col * (self.cw + self.gap) + 2
        y0 = row * (self.ch + self.gap) + 2
        w = cols * self.cw + (cols - 1) * self.gap
        h = rows * self.ch + (rows - 1) * self.gap
        return QRectF(x0, y0, w, h)

    def extent(self):
        rects = [p.rect for p in self.pads] + [r for r, _ in self.static]
        return max(r.right() for r in rects) + 4, max(r.bottom() for r in rects) + 4

    def build(self):
        for k in self.cfg["keys"]:
            self.pads.append(Pad(k["label"], self.cell_rect(k["col"], k["row"]), vks_for_label(k["label"])))

        j = self.cfg.get("joystick")
        if j:
            box = self.cell_rect(j["col"], j["row"], j["cols"], j["rows"])
            self.static.append((box, "box"))
            cx, cy = box.center().x(), box.center().y()
            rad = min(box.width(), box.height()) * 0.30
            self.static.append((QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), "ring"))
            dot_r = rad * 0.30
            for name, dx, dy in (("up", 0, -1), ("down", 0, 1), ("left", -1, 0), ("right", 1, 0)):
                label = j[name]
                px, py = cx + dx * rad * 0.62, cy + dy * rad * 0.62
                pad = Pad(label, QRectF(px - dot_r, py - dot_r, 2 * dot_r, 2 * dot_r),
                          vks_for_label(label), shape="dot")
                pad.text_pos = QPointF(cx + dx * rad * 1.4, cy + dy * rad * 1.4)
                self.pads.append(pad)

    # ---- painting -----------------------------------------------------
    @staticmethod
    def mix(a, b, t):
        return QColor(
            int(a.red() + (b.red() - a.red()) * t),
            int(a.green() + (b.green() - a.green()) * t),
            int(a.blue() + (b.blue() - a.blue()) * t),
        )

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(self.font)

        for rect, kind in self.static:
            p.setBrush(QBrush(self.idle_fill) if kind == "box" else Qt.BrushStyle.NoBrush)
            p.setPen(QPen(self.idle_outline, 1.2))
            if kind == "box":
                p.drawRoundedRect(rect, self.radius, self.radius)
            else:
                p.drawEllipse(rect)

        for pad in self.pads:
            t = pad.level
            fill = self.mix(self.idle_fill, self.pressed_fill, t)
            text = self.mix(self.idle_text, self.pressed_text, t)

            if t > 0.02:  # soft glow behind lit keys
                glow = QColor(self.pressed_fill)
                for i, spread in enumerate((6, 3)):
                    glow.setAlphaF(0.18 * t / (i + 1))
                    p.setPen(QPen(glow, spread * 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    if pad.shape == "rect":
                        p.drawRoundedRect(pad.rect, self.radius, self.radius)
                    else:
                        p.drawEllipse(pad.rect)

            p.setBrush(QBrush(fill))
            p.setPen(QPen(self.mix(self.idle_outline, self.pressed_fill, t), 1.2 + t))
            if pad.shape == "rect":
                p.drawRoundedRect(pad.rect, self.radius, self.radius)
                p.setPen(text)
                p.drawText(pad.rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, pad.label)
            else:
                p.drawEllipse(pad.rect)
                p.setPen(self.mix(self.idle_text, self.pressed_fill, t))
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(pad.label)
                p.drawText(QPointF(pad.text_pos.x() - tw / 2, pad.text_pos.y() + fm.ascent() / 2 - 1), pad.label)
        p.end()

    # ---- window plumbing ----------------------------------------------
    def keep_on_top(self):
        if self.isVisible():
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
                    self.check_hotkeys(vk)
            else:
                self.pressed.discard(vk)

        step = dt * 1000 / self.FADE_MS
        dirty = False
        for pad in self.pads:
            pad.down = bool(pad.vks & self.pressed)
            target = 1.0 if pad.down else 0.0
            if pad.down and pad.level < 1.0:
                pad.level = 1.0  # instant on
                dirty = True
            elif not pad.down and pad.level > 0.0:
                pad.level = max(0.0, pad.level - step)  # smooth off
                dirty = True
            elif pad.level != target:
                pad.level = target
                dirty = True
        if dirty:
            self.update()

    def check_hotkeys(self, vk):
        if not (self.pressed & CTRL_VKS and self.pressed & ALT_VKS):
            return
        if vk in self.hotkeys["quit"]:
            self.listener.stop()
            QApplication.quit()
        elif vk in self.hotkeys["toggle"]:
            self.setVisible(not self.isVisible())


def main():
    try:
        cfg = load_config()
    except (OSError, ValueError) as e:
        print(f"Could not load {CONFIG_PATH}: {e}", file=sys.stderr)
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = Overlay(cfg)
    overlay.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

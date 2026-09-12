"""Feedback loop: does game input reach the overlay after the user alt-tabs
away from Settings with "Edit on screen" still active?

Steps (real Win32 input, so keep hands off the mouse for ~10 s):
  1. Start overlay + SettingsWindow, press "Edit on screen".
  2. A throwaway "FakeGame" window (separate process) takes the foreground,
     the way a game does after alt-tab.
  3. SendInput: left-click-drag across the overlay, then 3 wheel ticks.
  4. RED if the overlay moved or resized (or cfg x/y/scale changed).

  python debug/edit_mode_game_loop.py
"""
import ctypes
import ctypes.wintypes as w
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import overlay  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

u32 = ctypes.windll.user32

MOUSEEVENTF_MOVE, MOUSEEVENTF_ABSOLUTE = 0x0001, 0x8000
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, MOUSEEVENTF_WHEEL = 0x0002, 0x0004, 0x0800


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class INPUT(ctypes.Structure):
    _fields_ = [("type", w.DWORD), ("mi", MOUSEINPUT), ("pad", ctypes.c_ubyte * 8)]


def send_mouse(flags, dx=0, dy=0, data=0):
    u32.mouse_event(flags, dx, dy, data, 0)


def move_abs(x, y):
    """Move the real cursor to physical pixel (x, y) on the primary screen."""
    u32.SetCursorPos(int(x), int(y))
    send_mouse(MOUSEEVENTF_MOVE, 0, 0)  # a zero-delta move so hooks/apps see a WM_MOUSEMOVE
    pt = w.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    assert abs(pt.x - x) <= 1 and abs(pt.y - y) <= 1, f"cursor at {(pt.x, pt.y)}, wanted {(x, y)}"


def win_rect(hwnd):
    r = w.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


class _NoListener:
    daemon = True

    def __init__(self, *a, **k):
        pass

    def start(self):
        pass

    def stop(self):
        pass


FAKE_GAME = """
import tkinter as tk, time
r = tk.Tk(); r.title('FakeGame'); r.geometry('1000x900+0+0'); r.configure(bg='#224')
r.after(300, lambda: (r.lift(), r.focus_force()))
r.mainloop()
"""


HITS = []


class ProbeOverlay(overlay.Overlay):
    def mousePressEvent(self, e):
        HITS.append("press")
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        HITS.append("move")
        super().mouseMoveEvent(e)

    def wheelEvent(self, e):
        HITS.append("wheel")
        super().wheelEvent(e)

    def nativeEvent(self, et, msg):
        m = w.MSG.from_address(int(msg))
        if m.message in (0x201, 0x20A, 0x202):
            HITS.append(f"WM_{m.message:x}")
        return super().nativeEvent(et, msg)


def main():
    overlay.keyboard.Listener = _NoListener
    overlay.mouse.Listener = _NoListener
    app = QApplication.instance() or QApplication(sys.argv)
    cfg = overlay.load_config()
    cfg["x"], cfg["y"], cfg["scale"] = 40, 40, 0.5
    ov = ProbeOverlay(cfg)
    ov.show()
    from settings_ui import SettingsWindow
    settings = SettingsWindow(ov)
    settings.save_timer.stop()
    settings._schedule_save = lambda: None  # never write the repo config from a probe
    settings.show()
    QTest.qWait(500)
    settings.btn_move.setChecked(True)  # "Edit on screen"
    QTest.qWait(500)
    assert ov.edit_mode, "edit mode did not turn on"

    hwnd = int(ov.winId())
    base_rect, base_cfg = win_rect(hwnd), (cfg["x"], cfg["y"], cfg["scale"])
    print("baseline rect", base_rect, "cfg", base_cfg)
    # Aim at a drawn pad: the layered window is click-through on alpha-0 pixels (gaps).
    pad = next(p for p in ov.pads if p.source and p.source[0] == "key")
    g = ov.mapToGlobal(pad.rect.center().toPoint())
    dpr = ov.devicePixelRatio()
    cx, cy = int(g.x() * dpr), int(g.y() * dpr)
    move_abs(cx, cy)
    QTest.qWait(100)
    pt = w.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    under = u32.WindowFromPoint(pt)
    print(f"edit mode on, cursor ({pt.x},{pt.y}) over hwnd={under} (overlay hwnd={hwnd})")
    assert under == hwnd, "precondition: in edit mode the overlay must be clickable under the cursor"

    game = subprocess.Popen([sys.executable, "-c", FAKE_GAME])
    try:
        QTest.qWait(1500)
        fake = u32.FindWindowW(None, "FakeGame")
        u32.keybd_event(0x12, 0, 0, 0)  # tap Alt: unlocks SetForegroundWindow for us
        u32.keybd_event(0x12, 0, 2, 0)
        u32.SetForegroundWindow(fake)
        QTest.qWait(1000)
        fg = ctypes.create_unicode_buffer(64)
        u32.GetWindowTextW(u32.GetForegroundWindow(), fg, 64)
        print("foreground now:", repr(fg.value), "| overlay edit_mode:", ov.edit_mode)
        hwnd = int(ov.winId())

        # Game-like input: fire (click) with the cursor over the overlay, mouse-look, weapon scroll.
        hits = HITS
        hits.clear()
        move_abs(cx, cy)
        QTest.qWait(100)
        u32.GetCursorPos(ctypes.byref(pt))
        under = u32.WindowFromPoint(pt)
        print(f"cursor ({pt.x},{pt.y}) now over hwnd={under} (overlay hwnd={hwnd})")
        send_mouse(MOUSEEVENTF_LEFTDOWN)
        for i in range(1, 11):
            move_abs(cx + 30 * i, cy + 20 * i)
            QTest.qWait(30)
        send_mouse(MOUSEEVENTF_LEFTUP)
        QTest.qWait(200)
        for _ in range(3):
            send_mouse(MOUSEEVENTF_WHEEL, data=(-120) & 0xFFFFFFFF)
            QTest.qWait(80)
        QTest.qWait(400)

        end_rect, end_cfg = win_rect(hwnd), (cfg["x"], cfg["y"], cfg["scale"])
        u32.GetWindowTextW(u32.GetForegroundWindow(), fg, 64)
        print("events hit overlay:", hits, "| foreground after input:", repr(fg.value))
        print("after input rect", end_rect, "cfg", end_cfg, "| edit_mode:", ov.edit_mode)
        red = end_rect != base_rect or end_cfg != base_cfg
        print("RED: game input moved/resized the overlay" if red else "GREEN: overlay untouched by game input")
        return 1 if red else 0
    finally:
        game.terminate()
        ov.tick.stop()
        ov.top_timer.stop()


if __name__ == "__main__":
    sys.exit(main())

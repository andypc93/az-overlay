"""Wayfinder ticket 06: can the overlay be dragged to every screen edge and
partially off-screen, and does the dropped position survive Done editing,
apply(), and a restart? Real Win32 input: keep hands off the mouse ~20 s.

  python debug/drag_reach_probe.py

Never touches the repo config: works on temp copies of config.json / profiles.
"""
import ctypes
import ctypes.wintypes as w
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import overlay  # noqa: E402
from PySide6.QtCore import QCoreApplication, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

u32 = ctypes.windll.user32
MOUSEEVENTF_MOVE, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0001, 0x0002, 0x0004


class _NoListener:
    daemon = True

    def __init__(self, *a, **k):
        pass

    def start(self):
        pass

    def stop(self):
        pass


def move_abs(x, y):
    u32.SetCursorPos(int(x), int(y))
    u32.mouse_event(MOUSEEVENTF_MOVE, 0, 0, 0, 0)


def cursor():
    pt = w.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def win_rect(hwnd):
    r = w.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def drag(ov, pad, to_logical):
    """Grab `pad` (real click) and drag until the window's top-left is at to_logical."""
    dpr = ov.devicePixelRatio()
    g = ov.mapToGlobal(pad.rect.center().toPoint())
    sx, sy = int(g.x() * dpr), int(g.y() * dpr)
    dx, dy = (to_logical[0] - ov.x()) * dpr, (to_logical[1] - ov.y()) * dpr
    move_abs(sx, sy)
    QTest.qWait(80)
    u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    steps = 12
    for i in range(1, steps + 1):
        move_abs(sx + dx * i / steps, sy + dy * i / steps)
        QTest.qWait(25)
    u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    QTest.qWait(250)
    return cursor()


def main():
    overlay.keyboard.Listener = _NoListener
    overlay.mouse.Listener = _NoListener
    tmp = tempfile.mkdtemp(prefix="az-drag-probe-")
    shutil.copy(overlay.CONFIG_PATH, os.path.join(tmp, "config.json"))
    shutil.copytree(overlay.PROFILE_DIR, os.path.join(tmp, "profiles"))
    overlay.CONFIG_PATH = os.path.join(tmp, "config.json")
    overlay.PROFILE_DIR = os.path.join(tmp, "profiles")

    app = QApplication.instance() or QApplication(sys.argv)
    cfg = overlay.load_config()
    cfg["x"], cfg["y"], cfg["scale"] = 200, 200, 0.5
    ov = overlay.Overlay(cfg)
    ov.show()
    from settings_ui import SettingsWindow
    settings = SettingsWindow(ov)
    settings.show()
    QTest.qWait(400)
    settings.btn_move.setChecked(True)
    QTest.qWait(400)
    assert ov.edit_mode, "edit mode did not turn on"
    hwnd = int(ov.winId())
    dpr = ov.devicePixelRatio()
    scr = ov.screen()
    avail = scr.availableGeometry().getRect()
    full = scr.geometry().getRect()
    ow, oh = ov.width(), ov.height()
    print(f"screen logical={full} available={avail} dpr={dpr} overlay size=({ow},{oh}) "
          f"win32 rect={win_rect(hwnd)}")

    pads = [p for p in ov.pads if p.source and p.source[0] == "key"]
    left_pad = min(pads, key=lambda p: p.rect.center().x())
    right_pad = max(pads, key=lambda p: p.rect.center().x())
    top_pad = min(pads, key=lambda p: p.rect.center().y())
    bottom_pad = max(pads, key=lambda p: p.rect.center().y())
    sw, sh = full[2], full[3]
    targets = [
        ("top-left corner", (0, 0), right_pad),
        ("top-right corner", (sw - ow, 0), left_pad),
        ("bottom-right corner", (sw - ow, sh - oh), left_pad),
        ("bottom-left corner", (0, sh - oh), right_pad),
        ("half off left edge", (-ow // 2, 300), right_pad),
        ("half off bottom-right", (sw - ow // 2, sh - oh // 2), left_pad),
        ("half off top", (400, -oh // 2), bottom_pad),
    ]
    results = []
    for name, target, pad in targets:
        cur = drag(ov, pad, target)
        after_release = (ov.x(), ov.y(), cfg["x"], cfg["y"], win_rect(hwnd))
        QTest.qWait(2600)  # a keep_on_top tick (2 s) must pass
        after_tick = (ov.x(), ov.y(), cfg["x"], cfg["y"], win_rect(hwnd))
        reached = abs(ov.x() - target[0]) <= 2 and abs(ov.y() - target[1]) <= 2
        stable = after_release[:4] == after_tick[:4]
        results.append((name, target, after_release[:2], reached, stable))
        print(f"{name:24} want={target} got=({ov.x()},{ov.y()}) cfg=({cfg['x']},{cfg['y']}) "
              f"cursor={cur} win32={after_tick[4]} reached={reached} stable_after_2s={stable}")

    # Persistence: Done editing, an apply() from a settings edit, close settings, restart from disk.
    drop = (ov.x(), ov.y())
    settings.btn_move.setChecked(False)
    QTest.qWait(400)
    after_done = (ov.x(), ov.y())
    settings._apply()
    QTest.qWait(300)
    after_apply = (ov.x(), ov.y())
    settings.close()
    QTest.qWait(600)  # flushes the debounced save
    reloaded = overlay.load_config()
    print(f"drop={drop} after Done editing={after_done} after apply()={after_apply} "
          f"reloaded from disk=({reloaded['x']},{reloaded['y']}) profile={reloaded.get('profile')!r}")
    ov.tick.stop()
    ov.top_timer.stop()
    bad = [r for r in results if not (r[3] and r[4])]
    print("GREEN: every target reached and stable; position survives Done/apply/restart"
          if not bad and after_done == drop == after_apply == (reloaded["x"], reloaded["y"])
          else f"RED: {bad or 'persistence mismatch'}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

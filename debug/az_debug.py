"""Run the real overlay with every window move/resize logged, plus the native
Windows messages that cause them. Throwaway diagnostic harness.

  python az_debug.py [--config PATH]

Log: moves.log next to this file (also stdout).
"""
import ctypes
import ctypes.wintypes as w
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import overlay  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moves.log")
u32 = ctypes.windll.user32
u32.SetProcessDpiAwarenessContext  # noqa: B018 (exists on win10+)

WM_NAMES = {0x0047: "WM_WINDOWPOSCHANGED", 0x007E: "WM_DISPLAYCHANGE", 0x02E0: "WM_DPICHANGED",
            0x001A: "WM_SETTINGCHANGE", 0x0005: "WM_SIZE", 0x0003: "WM_MOVE"}
SWP_NOSIZE, SWP_NOMOVE = 0x0001, 0x0002


class WINDOWPOS(ctypes.Structure):
    _fields_ = [("hwnd", w.HWND), ("hwndInsertAfter", w.HWND), ("x", ctypes.c_int), ("y", ctypes.c_int),
                ("cx", ctypes.c_int), ("cy", ctypes.c_int), ("flags", w.UINT)]


def fg_title():
    hwnd = u32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    u32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def buttons():
    return "".join(n for n, vk in (("L", 1), ("R", 2), ("M", 4)) if u32.GetAsyncKeyState(vk) & 0x8000) or "-"


def log(msg):
    line = f"{time.strftime('%H:%M:%S')}.{int(time.time() * 1000) % 1000:03d} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class DebugOverlay(overlay.Overlay):
    def _state(self):
        scr = self.screen()
        g = scr.geometry().getRect() if scr else None
        return (f"spont? edit={self.edit_mode} drag={self._drag_origin} btn={buttons()} "
                f"fg={fg_title()!r} screen={g} dpr={self.devicePixelRatio()} "
                f"cfg=({self.cfg['x']},{self.cfg['y']}) vis={self.isVisible()}")

    def moveEvent(self, e):
        log(f"[DEBUG-mv01] MOVE {e.oldPos().toTuple()} -> {e.pos().toTuple()} "
            + self._state().replace("spont?", f"spont={e.spontaneous()}"))
        if not e.spontaneous():
            log("[DEBUG-mv01] stack:\n" + "".join(traceback.format_stack(limit=10)))
        super().moveEvent(e)

    def resizeEvent(self, e):
        log(f"[DEBUG-mv01] RESIZE {e.oldSize().toTuple()} -> {e.size().toTuple()} "
            + self._state().replace("spont?", f"spont={e.spontaneous()}"))
        super().resizeEvent(e)

    def showEvent(self, e):
        log(f"[DEBUG-mv01] SHOW geom={self.geometry().getRect()} " + self._state())
        super().showEvent(e)

    def hideEvent(self, e):
        log("[DEBUG-mv01] HIDE " + self._state())
        super().hideEvent(e)

    def nativeEvent(self, event_type, message):
        try:
            m = w.MSG.from_address(int(message))
            name = WM_NAMES.get(m.message)
            if name == "WM_WINDOWPOSCHANGED":
                wp = WINDOWPOS.from_address(m.lParam)
                if wp.flags & SWP_NOMOVE and wp.flags & SWP_NOSIZE:
                    name = None  # z-order only (keep_on_top raise_), too chatty
                else:
                    name += f" x={wp.x} y={wp.y} cx={wp.cx} cy={wp.cy} flags=0x{wp.flags:x}"
            elif name == "WM_DPICHANGED":
                r = w.RECT.from_address(m.lParam)
                name += f" dpi={m.wParam & 0xFFFF} suggested=({r.left},{r.top},{r.right},{r.bottom})"
            elif name == "WM_DISPLAYCHANGE":
                name += f" bpp={m.wParam} res={m.lParam & 0xFFFF}x{m.lParam >> 16}"
            elif name in ("WM_SIZE", "WM_MOVE"):
                name = None
            if name:
                log(f"[DEBUG-mv01] NATIVE {name}")
        except Exception as ex:  # never break the app from the probe
            log(f"[DEBUG-mv01] nativeEvent probe error {ex!r}")
        return super().nativeEvent(event_type, message)


def install_sampler(ov):
    """Poll the real Win32 rect once a second; catches anything Qt didn't report."""
    hwnd = int(ov.winId())
    last = [None]

    def sample():
        r = w.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        cur = (r.left, r.top, r.right, r.bottom)
        if cur != last[0]:
            log(f"[DEBUG-mv01] WIN32RECT {last[0]} -> {cur} qt={ov.geometry().getRect()} " + ov._state())
            last[0] = cur

    t = QTimer(ov)
    t.setInterval(1000)
    t.timeout.connect(sample)
    t.start()
    ov._dbg_sampler = t
    sample()


def main():
    if "--config" in sys.argv:
        overlay.CONFIG_PATH = sys.argv[sys.argv.index("--config") + 1]
    log(f"[DEBUG-mv01] START pid={os.getpid()} config={overlay.CONFIG_PATH} "
        f"sysdpi={u32.GetDpiForSystem()} argv={sys.argv[1:]}")
    overlay.Overlay = DebugOverlay
    orig_show = DebugOverlay.show

    def show(self):
        orig_show(self)
        if not getattr(self, "_dbg_sampler", None):
            install_sampler(self)

    DebugOverlay.show = show
    overlay.main()


if __name__ == "__main__":
    main()

"""Regenerate the README screenshots of the settings pages (docs/layout.png,
docs/keys.png, docs/appearance.png) and the overlay itself (docs/overlay.png,
with a few inputs lit) from the real widgets at the screen's DPR.

  python debug/screenshots.py

Uses the repo config and layouts read-only (saving is disabled), no input hooks.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import Qt, Signal  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPainter  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

import overlay  # noqa: E402
import settings_ui  # noqa: E402

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


class StubOverlay(QWidget):
    config_changed = Signal()
    key_captured = Signal(object)
    edit_mode_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.cfg = overlay.load_config()
        self.capturing = False
        self.edit_mode = False

    def apply(self):
        pass

    def set_edit_mode(self, on):
        pass

    def shutdown(self):
        pass


LIT = ("X", "Space", "W")  # inputs shown held in docs/overlay.png
PAD = 24  # px of dark background around the overlay


def grab_overlay(name="overlay"):
    """Real overlay with LIT inputs injected as key-down events, over a dark backdrop."""
    ov = overlay.Overlay(overlay.load_config())
    ov.show()
    QTest.qWait(200)
    for label in LIT:
        for vk in overlay.vks_for_label(label):
            ov.events.put(("down", vk))
    QTest.qWait(250)  # pump() drains the queue and lights the pads
    shot = ov.grab().toImage()
    dpr = shot.devicePixelRatio()
    out = QImage(shot.width() + int(2 * PAD * dpr), shot.height() + int(2 * PAD * dpr), QImage.Format.Format_ARGB32)
    out.setDevicePixelRatio(dpr)
    out.fill(QColor("#0b0b0b"))
    p = QPainter(out)
    p.drawImage(PAD, PAD, shot)
    p.end()
    path = os.path.join(DOCS, f"{name}.png")
    out.save(path)
    print("wrote", path)
    ov.tick.stop()
    ov.close()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    grab_overlay()
    settings_ui.save_config = lambda cfg: None  # never write the repo config from here
    window = settings_ui.SettingsWindow(StubOverlay())
    window.resize(1040, 860)
    window.show()
    QTest.qWait(300)

    def grab(name, height=860):
        window.resize(1040, height)
        QTest.qWait(200)
        path = os.path.join(DOCS, f"{name}.png")
        window.grab().save(path)
        print("wrote", path)

    window.nav.setCurrentRow(0)
    grab("layout")

    window.nav.setCurrentRow(1)
    window.show_all_pads.setChecked(True)
    QTest.qWait(100)
    rows = [i for i, k in enumerate(window.cfg["keys"]) if k["col"] == 3][:3]
    window._set_selected_pads(rows)
    QTest.qWait(100)
    grab("keys", 1100)

    window.nav.setCurrentRow(2)
    grab("appearance", 1320)
    window.close()


if __name__ == "__main__":
    main()

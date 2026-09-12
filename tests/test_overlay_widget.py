"""Overlay window behaviour (edit-mode drag) without keyboard or mouse hooks."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import overlay


class _NoListener:
    daemon = True

    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass


@pytest.fixture
def window(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(overlay.keyboard, "Listener", _NoListener)
    monkeypatch.setattr(overlay.mouse, "Listener", _NoListener)
    cfg = overlay.load_config()
    cfg["x"], cfg["y"] = 300, 300
    ov = overlay.Overlay(cfg)
    ov.show()
    QTest.qWait(100)
    ov.set_edit_mode(True)
    QTest.qWait(100)
    yield ov
    ov.tick.stop()
    ov.top_timer.stop()
    ov.close()
    ov.deleteLater()
    app.processEvents()


def drag(ov, grab, delta):
    """Drag the window by `delta`. The cursor keeps the same offset inside the
    window, so press and release land on the same local point (as they do for a
    real drag)."""
    QTest.mousePress(ov, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, grab)
    QTest.mouseMove(ov, grab + delta)
    QApplication.processEvents()
    QTest.mouseRelease(ov, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, grab)
    QTest.qWait(50)


def test_drag_release_saves_position_and_survives_apply(window):
    changed = []
    window.config_changed.connect(lambda: changed.append((window.cfg["x"], window.cfg["y"])))

    drag(window, QPoint(20, 20), QPoint(100, 50))

    assert (window.x(), window.y()) == (400, 350)
    assert (window.cfg["x"], window.cfg["y"]) == (400, 350)
    assert changed == [(400, 350)]
    assert not window.capturing

    window.cfg["scale"] = 1.2
    window.apply()
    window.set_edit_mode(False)
    QTest.qWait(100)
    assert (window.x(), window.y()) == (400, 350)


def test_click_without_drag_starts_capture_and_keeps_position(window):
    pad = window.pads[0]
    inside = pad.rect.center().toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, inside)
    QTest.qWait(50)
    assert window.capturing
    assert window.capture_pad is pad
    assert (window.x(), window.y()) == (300, 300)

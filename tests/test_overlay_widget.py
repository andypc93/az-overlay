"""Overlay window behaviour (edit-mode drag) without keyboard or mouse hooks."""

import pytest
from PySide6.QtCore import QPoint, QRect, Qt
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


def _hotkey(ov, key):
    ov.pressed = set(overlay.CTRL_VKS) | set(overlay.ALT_VKS)
    ov.check_hotkeys(ord(key))
    ov.pressed = set()
    QTest.qWait(50)


def test_edit_hotkey_shows_the_overlay_and_toggles_edit_mode(window):
    window.set_edit_mode(False)
    window.hide()
    states = []
    window.edit_mode_changed.connect(states.append)
    _hotkey(window, "E")
    assert window.isVisible() and window.edit_mode
    _hotkey(window, "E")
    assert not window.edit_mode
    assert states == [True, False]


def test_escape_ends_edit_mode(window):
    assert window.edit_mode
    QTest.keyClick(window, Qt.Key.Key_Escape)
    QTest.qWait(50)
    assert not window.edit_mode


def test_tray_edit_action_mirrors_edit_mode(window):
    window.set_edit_mode(False)
    menu = overlay.tray_menu(window, lambda: None)
    action = next(a for a in menu.actions() if a.text() == "Edit on screen")
    assert action.isCheckable() and not action.isChecked()
    action.trigger()
    QTest.qWait(50)
    assert window.edit_mode and action.isChecked()
    window.set_edit_mode(False)
    assert not action.isChecked()


def test_edit_hint_names_hotkey_and_escape(window):
    hint = window.edit_hint()
    assert "Ctrl+Alt+E" in hint and "Esc" in hint


@pytest.fixture
def one_screen(monkeypatch):
    monkeypatch.setattr(overlay, "screen_rects", lambda: [QRect(0, 0, 2560, 1440)])


def test_overlay_on_no_screen_is_pulled_back_into_view(window, one_screen):
    window.cfg["x"], window.cfg["y"] = -5000, 200
    window.apply()
    assert window.cfg["x"] == 40 - window.width() and window.cfg["y"] == 200
    assert window.x() == window.cfg["x"]
    window.cfg["x"], window.cfg["y"] = 100, 9000
    window.apply()
    assert window.cfg["x"] == 100 and window.cfg["y"] == 1440 - 40


@pytest.mark.parametrize("pos", [(-200, 300), (300, -200), (2400, 300), (300, 1300)])
def test_overlay_half_off_an_edge_stays_put(window, one_screen, pos):
    window.cfg["x"], window.cfg["y"] = pos
    window.apply()
    assert (window.cfg["x"], window.cfg["y"]) == pos and (window.x(), window.y()) == pos

"""Stick rendering styles and the optional box behind them."""

import json

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

import overlay
import settings_ui
from tests.test_settings_ui import editor  # noqa: F401  (fixture)


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
    QApplication.instance() or QApplication([])
    monkeypatch.setattr(overlay.keyboard, "Listener", _NoListener)
    monkeypatch.setattr(overlay.mouse, "Listener", _NoListener)
    cfg = overlay.load_config()
    cfg["sticks"] = [{"label": "Left Stick", "col": 0, "row": 0, "w": 2, "h": 2,
                      "up": "W", "down": "S", "left": "A", "right": "D",
                      "axes": ["gp:leftx", "gp:lefty"], "click": "gp:leftstick"}]
    cfg["keys"] = []
    ov = overlay.Overlay(cfg)
    yield ov
    ov.tick.stop()
    ov.top_timer.stop()
    ov.close()
    ov.deleteLater()


def test_migrate_defaults_and_validates_stick_style():
    cfg = {"keys": []}
    overlay.migrate(cfg)
    assert cfg["stick_style"] == "classic" and cfg["stick_box"] is True
    cfg["stick_style"] = "bogus"
    overlay.migrate(cfg)
    assert cfg["stick_style"] == "classic"


def test_stick_style_is_part_of_saved_layouts(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    cfg = overlay.load_config()
    cfg["stick_style"], cfg["stick_box"] = "vector", False
    overlay.save_profile("styled", cfg)
    saved = json.loads((tmp_path / "styled.json").read_text(encoding="utf-8"))
    assert saved["stick_style"] == "vector" and saved["stick_box"] is False


@pytest.mark.parametrize("style", overlay.STICK_STYLES)
@pytest.mark.parametrize("box", (True, False))
def test_every_style_builds_and_paints(window, style, box):
    window.cfg["stick_style"], window.cfg["stick_box"] = style, box
    window.apply()
    directions = [p for p in window.pads if p.source and p.source[0] == "stick"]
    assert {p.source[2] for p in directions} == {"up", "down", "left", "right"}
    assert all(p.rect.width() > 0 and p.rect.height() > 0 for p in directions)
    # a lit direction plus a deflected knob must paint without error in every style
    directions[0].level = 1.0
    window.sticks[0].offset = QPointF(0.6, -0.7)
    window.sticks[0].level = 1.0
    assert not window.grab().isNull()


def test_direction_pads_stay_inside_their_stick(window):
    for style in overlay.STICK_STYLES:
        window.cfg["stick_style"] = style
        window.apply()
        st = window.sticks[0]
        for pad in window.pads:
            if pad.source and pad.source[0] == "stick":
                assert st.rect.contains(pad.rect), (style, pad.source[2])


def test_settings_expose_style_and_box(editor):
    combo = editor.stick_style_combo
    assert [combo.itemData(i) for i in range(combo.count())] == list(overlay.STICK_STYLES)
    combo.setCurrentIndex(list(overlay.STICK_STYLES).index("petals"))
    assert editor.cfg["stick_style"] == "petals"
    editor.stick_box.setChecked(False)
    assert editor.cfg["stick_box"] is False

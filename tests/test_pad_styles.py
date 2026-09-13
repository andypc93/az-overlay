"""Pad (key / button) rendering styles."""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

import overlay
import settings_ui
from tests.test_settings_ui import editor  # noqa: F401  (fixture)
from tests.test_stick_styles import window  # noqa: F401  (fixture)


def test_migrate_defaults_and_validates_pad_style():
    cfg = {"keys": []}
    overlay.migrate(cfg)
    assert cfg["pad_style"] == "classic"
    cfg["pad_style"] = "neon"
    overlay.migrate(cfg)
    assert cfg["pad_style"] == "classic"
    assert "pad_style" in overlay.PROFILE_KEYS


@pytest.mark.parametrize("style", overlay.PAD_STYLES)
@pytest.mark.parametrize("shape", ("rect", "circle"))
def test_every_pad_style_paints(window, style, shape):  # noqa: F811
    window.cfg["keys"] = [{"label": "Space", "col": 2, "row": 0, "w": 1, "h": 1},
                          {"label": "F", "col": 3, "row": 0, "w": 1, "h": 1}]
    window.cfg["stick_style"] = "keys"  # the key-cross directions use the pad style too
    window.cfg["pad_style"], window.cfg["shape"] = style, shape
    window.apply()
    keys = [p for p in window.pads if p.source and p.source[0] == "key"]
    assert len(keys) == 2
    keys[0].level = 1.0
    keys[1].level = 0.4
    assert not window.grab().isNull()


@pytest.mark.parametrize("style", overlay.PAD_STYLES)
def test_preview_follows_pad_style(editor, style):  # noqa: F811
    editor.cfg["pad_style"] = style
    editor.preview.resize(600, 160)
    assert not editor.preview.grab().isNull()


def test_settings_expose_pad_shape_and_style(editor):  # noqa: F811
    combo = editor.pad_style_combo
    assert [combo.itemData(i) for i in range(combo.count())] == list(overlay.PAD_STYLES)
    combo.setCurrentIndex(list(overlay.PAD_STYLES).index("keycap"))
    assert editor.cfg["pad_style"] == "keycap"
    editor.pad_shape_combo.setCurrentIndex(1)
    assert editor.cfg["shape"] == "circle"


def _paint_pad(style, t, colors):
    img = QImage(120, 90, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor("#203020"))
    p = QPainter(img)
    overlay.draw_pad(p, QRectF(0, 0, 120, 90), "rect", style, 8, {k: QColor(v) for k, v in colors.items()}, t)
    p.end()
    return img


def _close(a, b, tol=10):
    return all(abs(x - y) <= tol for x, y in zip(a.getRgb()[:3], b.getRgb()[:3]))


def test_underline_pressed_tile_takes_the_pressed_fill():
    colors = dict(overlay.DEFAULT_COLORS, pressed_fill="#ff0000", pressed_outline="#c9d400", pressed_text="#000000")
    img = _paint_pad("underline", 1.0, colors)
    assert _close(img.pixelColor(60, 40), QColor("#ff0000")), img.pixelColor(60, 40).name()
    assert _close(img.pixelColor(60, 87), QColor("#c9d400")), img.pixelColor(60, 87).name()  # the bar still carries the outline color


def test_pressed_pads_paint_solid_while_idle_pads_follow_opacity(window):  # noqa: F811
    window.cfg["keys"] = [{"label": "A", "col": 0, "row": 0, "w": 1, "h": 1},
                          {"label": "B", "col": 1, "row": 0, "w": 1, "h": 1}]
    window.cfg["opacity"] = 0.35
    window.cfg["pad_style"] = "classic"
    window.set_edit_mode(False)
    window.apply()
    assert window.windowOpacity() == 1.0  # opacity is painted per pad, not applied to the window
    keys = [p for p in window.pads if p.source and p.source[0] == "key"]
    keys[0].level = 1.0
    img = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))
    window.render(img)
    pressed = img.pixelColor(keys[0].rect.center().toPoint())
    idle = img.pixelColor(keys[1].rect.center().toPoint())
    assert pressed.alpha() >= 250
    assert abs(idle.alpha() - round(0.35 * 255)) <= 8

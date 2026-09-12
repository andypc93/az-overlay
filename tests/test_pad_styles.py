"""Pad (key / button) rendering styles."""

import pytest
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

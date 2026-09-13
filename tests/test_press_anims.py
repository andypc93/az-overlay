"""Press animations: what a pad does the moment it is pressed and released."""

import json

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter

import overlay
import settings_ui
from tests.test_settings_ui import editor  # noqa: F401  (fixture)
from tests.test_stick_styles import window  # noqa: F401  (fixture)

MID = {  # a point in the middle of each animation, as (down, press_t, release_t)
    "classic": (False, 0.1, 0.05),
    "spring": (False, 0.9, overlay.SPRING_S / 2),
    "ripple": (True, overlay.RIPPLE_S / 2, None),
    "burst": (True, overlay.BURST_S / 2, None),
    "ember": (False, 0.9, overlay.EMBER_S / 2),
    "strike": (True, overlay.STRIKE_S / 2, None),
}


def _paint(anim, t=1.0, down=False, press_t=None, release_t=None, style="classic", size=(120, 90)):
    img = QImage(size[0], size[1], QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor("#203020"))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = {k: QColor(v) for k, v in overlay.DEFAULT_COLORS.items()}
    rect = QRectF(size[0] * 0.2, size[1] * 0.2, size[0] * 0.6, size[1] * 0.6)
    overlay.draw_pad(p, rect, "rect", style, 8, c, t, anim, down, press_t, release_t)
    p.end()
    return img


def _lightness(img, x, y):
    return sum(img.pixelColor(x, y).getRgb()[:3])


# ---- config ---------------------------------------------------------------
def test_migrate_defaults_and_validates_press_anim():
    cfg = {"keys": []}
    overlay.migrate(cfg)
    assert cfg["press_anim"] == "classic"
    cfg["press_anim"] = "sparkle"
    overlay.migrate(cfg)
    assert cfg["press_anim"] == "classic"
    assert "press_anim" in overlay.PROFILE_KEYS


def test_press_anim_is_part_of_saved_layouts(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    cfg = overlay.load_config()
    cfg["press_anim"] = "ember"
    overlay.save_profile("bouncy", cfg)
    saved = json.loads((tmp_path / "bouncy.json").read_text(encoding="utf-8"))
    assert saved["press_anim"] == "ember"


# ---- the animation clock --------------------------------------------------
def test_press_and_release_start_the_clocks(window):  # noqa: F811
    window.cfg["keys"] = [{"label": "Space", "col": 0, "row": 0, "w": 1, "h": 1}]
    window.apply()
    pad = [p for p in window.pads if p.source and p.source[0] == "key"][0]
    assert pad.press_t is None and pad.release_t is None and pad.down is False

    window.pressed = set(overlay.vks_for_label("Space"))
    window.pump()
    assert pad.down is True and pad.press_t == 0.0 and pad.release_t is None
    window.pump()
    assert pad.press_t > 0.0  # the clock runs while the key is held

    window.pressed = set()
    window.pump()
    assert pad.down is False and pad.release_t == 0.0
    window.pump()
    assert pad.release_t > 0.0


def test_a_second_press_restarts_the_animation(window):  # noqa: F811
    window.cfg["keys"] = [{"label": "Space", "col": 0, "row": 0, "w": 1, "h": 1}]
    window.apply()
    pad = [p for p in window.pads if p.source and p.source[0] == "key"][0]
    for _ in range(2):
        window.pressed = set(overlay.vks_for_label("Space"))
        window.pump()
        window.pump()
        window.pressed = set()
        window.pump()
    assert pad.release_t == 0.0 and pad.press_t > 0.0


def test_clocks_survive_a_config_edit_mid_press(window):  # noqa: F811
    window.cfg["keys"] = [{"label": "Space", "col": 0, "row": 0, "w": 1, "h": 1}]
    window.apply()
    window.pressed = set(overlay.vks_for_label("Space"))
    window.pump()
    window.cfg["press_anim"] = "spring"
    window.apply()  # changing a setting must not strand a key that is still held
    pad = [p for p in window.pads if p.source and p.source[0] == "key"][0]
    assert pad.down is True and pad.press_t is not None


@pytest.mark.parametrize("anim", overlay.PRESS_ANIMS)
def test_running_only_while_there_is_something_to_draw(anim):
    down, press_t, release_t = MID[anim]
    running = overlay.press_anim_running(anim, press_t, release_t)
    assert running is (anim != "classic")
    assert overlay.press_anim_running(anim, None, None) is False
    assert overlay.press_anim_running(anim, 9.0, 9.0) is False  # long over


def test_ember_holds_the_color_longer_than_the_others():
    assert overlay.PRESS_FADE_MS["ember"] > overlay.Overlay.FADE_MS
    assert "classic" not in overlay.PRESS_FADE_MS  # the rest keep the original 140 ms fade


# ---- geometry -------------------------------------------------------------
def test_spring_squashes_while_held_and_overshoots_on_release():
    held = overlay.press_scale("spring", True, 0.5, None)
    assert held[0] < 1.0 and held[1] < held[0]  # squashed, more vertically than horizontally
    assert max(overlay.press_scale("spring", False, 0.9, overlay.SPRING_S * 0.45)) > 1.0  # overshoot
    assert overlay.press_scale("spring", False, 0.9, overlay.SPRING_S) == (1.0, 1.0)  # settles exactly


def test_only_the_moving_animations_scale_the_body():
    for anim in overlay.PRESS_ANIMS:
        down, press_t, release_t = MID[anim]
        scale = overlay.press_scale(anim, down, press_t, release_t)
        if anim in ("spring", "burst"):
            assert scale != (1.0, 1.0), anim
        else:
            assert scale == (1.0, 1.0), anim


@pytest.mark.parametrize("anim", overlay.PRESS_ANIMS)
def test_margin_covers_the_spill_and_stays_small(anim):
    rect = QRectF(0, 0, 100, 140)
    m = overlay.press_anim_margin(anim, rect)
    assert 8.0 <= m <= 20.0, m  # the window is only 4 px bigger than the pad grid


def test_keyframes_hit_their_ends():
    assert overlay._keyframes(overlay.BURST_KEYS, 0.0) == (1.0,)
    assert overlay._keyframes(overlay.BURST_KEYS, 1.0) == (1.0,)
    assert overlay._keyframes(overlay.BURST_KEYS, 2.0) == (1.0,)  # clamped past the end


# ---- painting -------------------------------------------------------------
@pytest.mark.parametrize("anim", overlay.PRESS_ANIMS)
@pytest.mark.parametrize("style", overlay.PAD_STYLES)
def test_every_animation_paints_in_every_pad_style(anim, style):
    down, press_t, release_t = MID[anim]
    assert not _paint(anim, 1.0, down, press_t, release_t, style).isNull()


@pytest.mark.parametrize("anim", overlay.PRESS_ANIMS)
@pytest.mark.parametrize("shape", ("rect", "circle"))
def test_every_animation_paints_on_the_overlay(window, anim, shape):  # noqa: F811
    window.cfg["keys"] = [{"label": "Space", "col": 0, "row": 0, "w": 1, "h": 1},
                          {"label": "F", "col": 1, "row": 0, "w": 1, "h": 1}]
    window.cfg["press_anim"], window.cfg["shape"] = anim, shape
    window.cfg["stick_style"] = "keys"  # the key-cross directions animate too
    window.apply()
    keys = [p for p in window.pads if p.source and p.source[0] == "key"]
    keys[0].down, keys[0].level = MID[anim][0], 1.0
    keys[0].press_t, keys[0].release_t = MID[anim][1], MID[anim][2]
    keys[1].level = 0.4
    assert not window.grab().isNull()


def test_strike_flashes_brighter_than_the_settled_press():
    flash = _lightness(_paint("strike", 1.0, True, 0.0), 60, 45)
    settled = _lightness(_paint("strike", 1.0, True, overlay.STRIKE_S), 60, 45)
    plain = _lightness(_paint("classic", 1.0), 60, 45)
    assert flash > settled + 30
    assert abs(settled - plain) <= 6  # once settled it is the ordinary pressed pad


def test_ember_glow_outlives_the_color():
    late = overlay.EMBER_S * 0.6
    dark = _paint("classic", 0.0)  # fully idle, no halo
    lit = _paint("ember", 0.0, False, 0.9, late)  # color gone, bloom still going
    edge = (18, 45)  # just outside the pad body, where only the halo reaches
    assert _lightness(lit, *edge) > _lightness(dark, *edge)


def test_ripple_marks_the_pad_and_then_clears():
    during = _paint("ripple", 1.0, True, overlay.RIPPLE_S * 0.45)
    after = _paint("ripple", 1.0, True, overlay.RIPPLE_S + 0.1)
    plain = _paint("classic", 1.0)
    assert any(during.pixelColor(x, 45) != plain.pixelColor(x, 45) for x in range(24, 96))
    assert all(after.pixelColor(x, 45) == plain.pixelColor(x, 45) for x in range(24, 96))


def test_ripple_stays_inside_the_pad():
    # the ring is clipped to the body, so a pressed key never paints over its neighbour
    during = _paint("ripple", 1.0, True, overlay.RIPPLE_S * 0.9)
    plain = _paint("classic", 1.0)
    for x, y in ((4, 45), (115, 45), (60, 4), (60, 85)):
        assert during.pixelColor(x, y) == plain.pixelColor(x, y), (x, y)


def test_burst_throws_sparks_past_the_body():
    # the pad body is x 40..160 in a 200 px image; late in the animation sparks clear its rim
    late = _paint("burst", 1.0, True, overlay.BURST_S * 0.85, size=(200, 200))
    plain = _paint("classic", 1.0, size=(200, 200))
    band = [(x, y) for x in range(161, 178) for y in range(94, 107)]
    assert any(late.pixelColor(x, y) != plain.pixelColor(x, y) for x, y in band)


def test_burst_sparks_stay_within_the_declared_margin():
    rect = QRectF(0, 0, 100, 140)
    m = overlay.press_anim_margin("burst", rect)
    far = (0.30 + 0.80) * rect.width() / 2  # the furthest a spark ever travels from the centre
    assert far - rect.width() / 2 <= m


def test_classic_is_unchanged():
    for t in (0.0, 0.4, 1.0):
        assert _paint("classic", t) == _paint("classic", t, True, 0.3, 0.3)


# ---- settings -------------------------------------------------------------
def test_settings_expose_every_animation(editor):  # noqa: F811
    combo = editor.press_anim_combo
    assert [combo.itemData(i) for i in range(combo.count())] == list(overlay.PRESS_ANIMS)
    combo.setCurrentIndex(list(overlay.PRESS_ANIMS).index("burst"))
    assert editor.cfg["press_anim"] == "burst"
    assert "sparks" in editor.press_anim_hint.text()


def test_every_animation_has_a_name_and_a_hint():
    assert set(settings_ui.PRESS_ANIM_NAMES) == set(overlay.PRESS_ANIMS)
    assert set(settings_ui.PRESS_ANIM_HINTS) == set(overlay.PRESS_ANIMS)


@pytest.mark.parametrize("anim", overlay.PRESS_ANIMS)
def test_preview_follows_the_animation(editor, anim):  # noqa: F811
    editor.cfg["press_anim"] = anim
    editor.preview.resize(600, 160)
    editor.preview._phase = 0.9  # just after the demo key is released
    assert not editor.preview.grab().isNull()


def test_preview_loop_covers_press_hold_and_release():
    held = settings_ui.preview_press_state("spring", 0.2)
    assert held[0] == 1.0 and held[1] is True and held[3] is None
    released = settings_ui.preview_press_state("spring", settings_ui.PREVIEW_HOLD_S + 0.05)
    assert released[1] is False and released[3] == pytest.approx(0.05)
    assert settings_ui.preview_press_state("spring", settings_ui.PREVIEW_CYCLE_S - 0.01)[0] == 0.0
    # ember holds its color longer, so it is still lit where the others have gone out
    assert settings_ui.preview_press_state("ember", settings_ui.PREVIEW_HOLD_S + 0.3)[0] > 0.0

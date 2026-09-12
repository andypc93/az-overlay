"""Mouse layouts: two buttons up to an MMO thumb grid."""

import pytest
from PySide6.QtCore import QRectF

import overlay
import templates
from tests.test_stick_styles import window  # noqa: F401  (fixture)


def _rects(prof):
    return [QRectF(k["col"], k["row"], k["w"], k["h"]) for k in prof["keys"]]


def test_mouse_is_a_device_with_five_templates():
    assert "Mouse" in templates.DEVICES
    assert len(templates.templates_for("Mouse")) == 5
    assert templates.layouts_for("Mouse") == []
    assert templates.suggested_name("Mouse", "5 buttons") == "Mouse – 5 buttons"


@pytest.mark.parametrize("template, count", templates.MICE)
def test_mouse_templates_have_the_advertised_buttons(template, count):
    prof = templates.build("Mouse", template)
    expected = count if count != 12 else 3 + 12  # main buttons plus the thumb grid
    if count > 2:
        expected += 2  # wheel up / wheel down around the middle click
    assert len(prof["keys"]) == expected, template
    assert all(k["label"] for k in prof["keys"])
    for k in prof["keys"]:
        overlay.pad_inputs(k)  # must not raise, even for the unbound DPI / sniper pads


@pytest.mark.parametrize("template, _count", templates.MICE)
def test_mouse_keys_do_not_overlap(template, _count):
    rects = _rects(templates.build("Mouse", template))
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.intersects(b.adjusted(0.01, 0.01, -0.01, -0.01)), template


def test_main_mouse_buttons_send_real_mouse_buttons():
    prof = templates.build("Mouse", "MMO (12 side buttons)")
    by_label = {k["label"]: k["input"] for k in prof["keys"]}
    assert by_label["Left"] == "Mouse Left" and by_label["Right"] == "Mouse Right"
    assert by_label["Wheel"] == "Mouse Middle"
    assert [by_label[str(n)] for n in range(1, 10)] == [str(n) for n in range(1, 10)]
    assert by_label["0"] == "0" and by_label["-"] == "-" and by_label["="] == "="


def test_mouse_templates_carry_a_body_silhouette():
    for template, _n in templates.MICE:
        prof = templates.build("Mouse", template)
        assert prof["decor"] and prof["decor"][0]["kind"] == "mouse", template
        main = [k for k in prof["keys"] if k["label"] in ("Left", "Right")]
        assert all(k["shape"].startswith("mouse_") for k in main), template


@pytest.mark.parametrize("template, _count", templates.MICE)
def test_mouse_templates_paint_and_cover_the_body(window, template, _count):  # noqa: F811
    window.cfg.update(templates.build("Mouse", template))
    window.apply()
    assert window.decor and window.width() >= window.decor[0][1].right()
    for pad in window.pads:
        if pad.label == "Left":
            pad.level = 1.0
    assert not window.grab().isNull()


def test_wheel_ticks_light_and_release(window):  # noqa: F811
    import time
    window.cfg.update(templates.build("Mouse", "3 buttons"))
    window.apply()
    up = next(p for p in window.pads if p.label == "▲")
    down = next(p for p in window.pads if p.label == "▼")
    window.on_scroll(0, 0, 0, 1)
    window.pump()
    assert up.level == 1.0 and down.level == 0.0
    window.on_scroll(0, 0, 0, -1)
    window.pump()
    assert down.level == 1.0
    time.sleep(overlay.WHEEL_HOLD_S + 0.05)
    window.pump()
    assert overlay.WHEEL_UP not in window.pressed and overlay.WHEEL_DOWN not in window.pressed
    assert up.level < 1.0 and down.level < 1.0  # fading out


def test_wheel_labels_resolve_and_capture_by_name():
    assert overlay.vks_for_label("Wheel Up") == {overlay.WHEEL_UP}
    assert overlay.label_for_token(overlay.WHEEL_DOWN) == "Wheel Down"

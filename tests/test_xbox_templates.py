"""Xbox Wireless and Elite templates: fixed drawing, back silhouette, paddles."""

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

import overlay


@pytest.fixture(autouse=True)
def _app():
    QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", ["xbox_front", "xbox_back"])
def test_xbox_decor_paths_fill_their_rect(kind):
    rect = QRectF(10, 20, 400, 300)
    path = overlay.decor_path(kind, rect)
    box = path.boundingRect()
    assert not path.isEmpty()
    assert rect.contains(box)
    assert box.width() > rect.width() * 0.9 and box.height() > rect.height() * 0.75


def test_back_decor_is_the_same_outline():
    rect = QRectF(0, 0, 400, 300)
    front = overlay.decor_path("xbox_front", rect)
    back = overlay.decor_path("xbox_back", rect)
    assert back == front
    assert front.boundingRect().top() > rect.top() + 20  # room above the fins stays free


@pytest.mark.parametrize("shape, sign", [("paddle_l", -1), ("paddle_r", 1)])
def test_paddle_shapes_are_tilted_pills(shape, sign):
    rect = QRectF(100, 100, 20, 70)
    path = overlay.shape_path(rect, shape, 4)
    box = path.boundingRect()
    assert box.width() > rect.width() + 10  # tilted, so wider than the upright pill
    assert abs(box.center().x() - rect.center().x()) < 0.5
    assert abs(box.center().y() - rect.center().y()) < 0.5
    top = min((path.elementAt(i) for i in range(path.elementCount())), key=lambda e: e.y)
    assert (top.x - rect.center().x()) * sign > 0  # top end leans away from the crotch
    text = overlay.key_text_rect(rect, shape)
    assert rect.contains(text) and text.center() == rect.center()


import templates  # noqa: E402
from tests.test_stick_styles import window  # noqa: E402, F401  (fixture)


def _rect(k, default=1):
    return QRectF(k["col"], k["row"], k.get("w", default), k.get("h", default))


def test_xbox_device_offers_wireless_and_elite():
    assert templates.templates_for("Xbox controller") == ["Xbox Wireless", "Xbox Elite Series 2"]
    assert templates.suggested_name("Xbox controller", "Xbox Elite Series 2") == "Xbox Elite Series 2"
    assert templates.build("Xbox controller") == templates.xbox_profile(False)
    assert templates.build("Xbox controller", "Xbox Elite Series 2") == templates.xbox_profile(True)


@pytest.mark.parametrize("elite", [False, True])
def test_xbox_templates_are_locked_fixed_drawings(elite):
    prof = templates.xbox_profile(elite)
    assert prof["locked"] is True and prof["stick_box"] is False
    assert prof["decor"][0]["kind"] == "xbox_front"
    front = _rect(prof["decor"][0])
    for k in prof["keys"]:
        if k.get("shape", "").startswith("paddle"):
            continue
        assert front.contains(_rect(k)), k["label"]
        overlay.pad_inputs(k)  # must not raise
    for st in prof["sticks"]:
        assert front.contains(_rect(st, 2)), st["label"]
    labels = {k["label"] for k in prof["keys"]}
    assert {"LT", "RT", "LB", "RB", "View", "Menu", "Y", "X", "B", "A"} <= labels
    assert ("Profile" in labels) == elite and ("Share" in labels) != elite


def test_elite_back_body_holds_four_editable_paddles():
    prof = templates.xbox_profile(True)
    back = [d for d in prof["decor"] if d["kind"] == "xbox_back"]
    assert len(back) == 1
    back_rect = _rect(back[0])
    front_rect = _rect(prof["decor"][0])
    assert back_rect.left() > front_rect.right()
    paddles = [k for k in prof["keys"] if k.get("shape", "").startswith("paddle")]
    assert [k["label"] for k in paddles] == ["P1", "P2", "P3", "P4"]
    assert [k["input"] for k in paddles] == [f"gp:paddle{n}" for n in range(1, 5)]
    assert all(k["editable"] for k in paddles) and all(back_rect.contains(_rect(k)) for k in paddles)
    assert not any(k.get("editable") for k in prof["keys"] if k not in paddles)
    assert not any(k.get("editable") for k in templates.xbox_profile(False)["keys"])


@pytest.mark.parametrize("elite", [False, True])
def test_xbox_pads_do_not_overlap(elite):
    prof = templates.xbox_profile(elite)
    # A stick draws its ring at 0.3 of its box from the centre; only the ring must stay clear of the pads.
    rects = [_rect(k) for k in prof["keys"]]
    for s in prof["sticks"]:
        box = _rect(s, 2)
        inset = box.width() * 0.2
        rects.append(box.adjusted(inset, inset, -inset, -inset))
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.intersects(b.adjusted(0.01, 0.01, -0.01, -0.01))


def test_locked_travels_with_the_profile():
    assert "locked" in overlay.PROFILE_KEYS


def test_elite_paints_and_covers_the_back_body(window):  # noqa: F811
    window.cfg.update(templates.xbox_profile(True))
    window.apply()
    kinds = [kind for kind, _r in window.decor]
    assert kinds == ["xbox_front", "xbox_back"]
    assert window.width() >= window.decor[1][1].right()
    window.grab()  # paints every pad, paddle, and both silhouettes

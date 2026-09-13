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
    rect = QRectF(10, 20, 400, 372)
    path = overlay.decor_path(kind, rect)
    box = path.boundingRect()
    assert not path.isEmpty()
    assert rect.contains(box)
    assert box.width() > rect.width() * 0.9 and box.height() > rect.height() * 0.75


def test_back_decor_carries_trigger_ghosts():
    rect = QRectF(0, 0, 400, 372)
    front = overlay.decor_path("xbox_front", rect)
    back = overlay.decor_path("xbox_back", rect)
    assert back.elementCount() > front.elementCount()
    assert back.boundingRect().top() < front.boundingRect().top()  # ghosts sit above the body


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

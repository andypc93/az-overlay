import json
import os

import pytest

import overlay


def test_letters_and_digits_map_to_vk():
    assert overlay.vks_for_label("Q") == {0x51}
    assert overlay.vks_for_label("9") == {0x39}


def test_named_keys_map_to_all_variants():
    assert overlay.vks_for_label("Alt") == {0x12, 0xA4, 0xA5}
    assert overlay.vks_for_label("Page Down") == {0x22}
    assert overlay.vks_for_label("F2") == {0x71}


def test_blank_label_maps_to_nothing():
    assert overlay.vks_for_label("") == set()


def test_unknown_label_raises():
    with pytest.raises(ValueError):
        overlay.vks_for_label("Bogus Key")


def test_config_labels_are_all_resolvable():
    with open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    for k in cfg["keys"]:
        overlay.vks_for_label(k["label"])
    for d in ("up", "down", "left", "right"):
        assert overlay.vks_for_label(cfg["joystick"][d])


def test_label_roundtrip():
    for label in ("Q", "7", "Alt", "Page Up", "F12", "Space", "Caps Lock"):
        vk = sorted(overlay.vks_for_label(label))[0]
        assert overlay.label_for_vk(vk) == label


def test_label_case_insensitive():
    assert overlay.vks_for_label("page up") == overlay.vks_for_label("Page Up")

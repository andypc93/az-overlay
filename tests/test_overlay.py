import json
import os

import pytest

import overlay


@pytest.mark.parametrize("theme", [None, "unsupported", "light", "dark"])
def test_config_theme_default_and_validation(theme, tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({} if theme is None else {"theme": theme}), encoding="utf-8")
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(path))
    assert overlay.load_config()["theme"] == ("light" if theme == "light" else "dark")


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
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    for k in cfg["keys"]:
        overlay.pad_inputs(k)
    for d in ("up", "down", "left", "right"):
        assert overlay.vks_for_label(cfg["sticks"][0][d])


def test_label_roundtrip():
    for label in ("Q", "7", "Alt", "Page Up", "F12", "Space", "Caps Lock"):
        vk = sorted(overlay.vks_for_label(label))[0]
        assert overlay.label_for_vk(vk) == label


def test_label_case_insensitive():
    assert overlay.vks_for_label("page up") == overlay.vks_for_label("Page Up")


def test_profile_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    cfg = overlay.load_config()
    cfg["x"] = 999
    overlay.save_profile("my layout", cfg)
    assert overlay.list_profiles() == ["my layout"]
    assert overlay.load_profile("my layout")["x"] == 999
    assert "hotkeys" not in overlay.load_profile("my layout")
    overlay.delete_profile("my layout")
    assert overlay.list_profiles() == []


def test_profile_name_sanitised(tmp_path, monkeypatch):
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    overlay.save_profile("a/b:c", overlay.load_config())
    assert overlay.list_profiles() == ["abc"]
    with pytest.raises(ValueError):
        overlay.save_profile("///", overlay.load_config())


def test_parse_input_chord_and_alternatives():
    chord = overlay.parse_input("Ctrl+Shift+K")
    assert len(chord) == 1 and len(chord[0]) == 3
    assert overlay.input_matches(chord, {0xA2, 0xA0, ord("K")})
    assert not overlay.input_matches(chord, {0xA2, ord("K")})
    macro = overlay.parse_input("F5, F6")
    assert overlay.input_matches(macro, {0x75}) and overlay.input_matches(macro, {0x74})
    assert overlay.input_matches(overlay.parse_input("gp:a"), {"gp:a"})
    with pytest.raises(ValueError):
        overlay.parse_input("gp:nope")


def test_scancode_resolves_on_windows():
    assert overlay.tokens_for_scancode(0x1E) == {ord("A")}
    assert 0xA3 in overlay.tokens_for_scancode(0xE01D)
    assert overlay.tokens_for_scancode(0xE11D) == {0x13}


def test_macro_pad_uses_input_not_label():
    entry = {"label": "Heal macro", "input": "F5, F6", "col": 0, "row": 0}
    assert overlay.input_matches(overlay.pad_inputs(entry), {0x75})


def test_migrate_old_joystick():
    cfg = {"keys": [{"label": "Q", "col": 0, "row": 0}],
           "joystick": {"col": 6, "row": 3, "cols": 2, "rows": 2, "up": "W", "left": "A", "down": "S", "right": "D"}}
    overlay.migrate(cfg)
    assert "joystick" not in cfg and cfg["sticks"][0]["up"] == "W" and cfg["keys"][0]["w"] == 1


def test_templates_build_and_resolve():
    import templates
    for dev in templates.DEVICES:
        for tpl in templates.templates_for(dev):
            for lay in templates.layouts_for(dev) or [None]:
                prof = templates.build(dev, tpl, lay)
                assert prof["keys"], (dev, tpl, lay)
                for k in prof["keys"]:
                    overlay.pad_inputs(k)  # must not raise
                for st in prof["sticks"]:
                    for d in ("up", "down", "left", "right"):
                        if st.get(d):
                            overlay.parse_input(st[d])


def test_keyboard_key_counts():
    import templates
    counts = {name: len(templates.build("Keyboard", name, "US (ANSI)")["keys"]) for name, _ in templates.KEYBOARDS}
    assert counts["100% Full size"] == 104
    assert counts["80% TKL"] == 87
    assert counts["65% Compact"] == 68
    assert counts["75% Compact"] == 84
    assert len(templates.build("Keyboard", "100% Full size", "German (ISO)")["keys"]) == 105


def test_keyboard_keys_do_not_overlap():
    import templates
    for name, _ in templates.KEYBOARDS:
        keys = templates.build("Keyboard", name, "UK (ISO)")["keys"]
        boxes = [(k["col"], k["row"], k["col"] + k["w"], k["row"] + k["h"], k["label"]) for k in keys]
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                overlap = a[0] < b[2] - 1e-6 and b[0] < a[2] - 1e-6 and a[1] < b[3] - 1e-6 and b[1] < a[3] - 1e-6
                assert not overlap, (name, a, b)


def test_azeron_models_listed_and_build():
    import templates
    names = templates.templates_for("Azeron")
    assert names == ["Cyborg II", "Cyborg II Compact", "Cyborg", "Cyborg Compact", "Keyzen", "Cyro", "Classic", "Compact"]
    for n in names:
        prof = templates.build("Azeron", n)
        assert prof["sticks"] and prof["keys"]
        for k in prof["keys"]:
            overlay.pad_inputs(k)
    assert templates.suggested_name("Azeron", "Keyzen") == "Azeron Keyzen"
    assert len(templates.build("Azeron", "Cyborg II")["keys"]) == 30

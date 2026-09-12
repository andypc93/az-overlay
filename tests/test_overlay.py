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
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    cfg["x"] = 999
    overlay.save_profile("my layout", cfg)
    assert overlay.list_profiles() == ["my layout"]
    assert overlay.load_profile("my layout")["x"] == 999
    assert "hotkeys" not in overlay.load_profile("my layout")
    overlay.delete_profile("my layout")
    assert overlay.list_profiles() == []


def test_profile_name_sanitised(tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path))
    overlay.save_profile("a/b:c", cfg)
    assert overlay.list_profiles() == ["abc"]
    with pytest.raises(ValueError):
        overlay.save_profile("///", cfg)


@pytest.mark.parametrize("remembered, expected", [("Z layout", "Z layout"), ("Deleted layout", "A layout"), ("", "A layout")])
def test_startup_restores_saved_layout(remembered, expected, tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    for name, x in (("A layout", 100), ("Z layout", 200)):
        overlay.save_profile(name, dict(cfg, x=x))
    cfg.update(profile=remembered, x=999, theme="light")
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    restored = overlay.load_config()
    assert restored["profile"] == expected
    assert restored["x"] == (200 if expected == "Z layout" else 100)
    assert restored["theme"] == "light"


def _globals_only(cfg):
    return {k: v for k, v in cfg.items() if k not in overlay.PROFILE_KEYS}


def test_save_config_writes_layout_to_its_file_and_only_globals_to_config(tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    cfg["profile"] = overlay.save_profile("My layout", cfg)
    cfg["x"] = 777
    cfg["theme"] = "light"
    overlay.save_config(cfg)
    on_disk = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert set(on_disk) == {"hotkeys", "theme", "profile"}
    assert on_disk["profile"] == "My layout" and on_disk["theme"] == "light"
    assert overlay.load_profile("My layout")["x"] == 777


def test_startup_reseeds_bundled_default_when_no_layouts_exist(tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    (tmp_path / "config.json").write_text(json.dumps(_globals_only(cfg)), encoding="utf-8")
    restored = overlay.load_config()
    assert overlay.list_profiles() == ["Cyborg 2 default"]
    assert restored["profile"] == "Cyborg 2 default"
    assert restored["keys"]


def test_startup_recovers_layout_from_old_config_when_no_layouts_exist(tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    cfg["x"] = 4321
    cfg["profile"] = ""
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    restored = overlay.load_config()
    assert overlay.list_profiles() == ["Recovered"]
    assert restored["profile"] == "Recovered" and restored["x"] == 4321
    overlay.save_config(restored)
    on_disk = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert "keys" not in on_disk and on_disk["profile"] == "Recovered"


def test_startup_drops_stale_layout_keys_when_layouts_exist(tmp_path, monkeypatch):
    cfg = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    overlay.save_profile("A layout", dict(cfg, x=100))
    stale = dict(cfg, x=4321, profile="")
    (tmp_path / "config.json").write_text(json.dumps(stale), encoding="utf-8")
    restored = overlay.load_config()
    assert restored["profile"] == "A layout" and restored["x"] == 100
    assert overlay.list_profiles() == ["A layout"]
    overlay.save_config(restored)
    on_disk = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert "keys" not in on_disk


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

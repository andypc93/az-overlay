"""Settings interactions without keyboard hooks or writes to user settings."""

from copy import deepcopy
import json

import pytest
from PySide6.QtCore import QPoint, Signal, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

import overlay
import settings_ui
import templates


class PreviewOverlay(QWidget):
    config_changed = Signal()
    key_captured = Signal(object)
    edit_mode_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.cfg = overlay.load_config()
        self.capturing = False

    def apply(self):
        pass

    def set_edit_mode(self, enabled):
        pass

    def shutdown(self):
        pass


@pytest.fixture
def editor(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    initial = overlay.load_config()
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(overlay, "PROFILE_DIR", str(tmp_path / "profiles"))
    initial["profile"] = overlay.save_profile("Test saved layout", initial)
    (tmp_path / "config.json").write_text(json.dumps(initial), encoding="utf-8")
    monkeypatch.setattr(settings_ui, "save_config", lambda cfg: None)
    source = PreviewOverlay()
    source.cfg["theme"] = "dark"
    window = settings_ui.SettingsWindow(source)
    yield window
    window.close()
    window.deleteLater()
    source.deleteLater()
    app.processEvents()


def test_filter_cancels_capture_when_selected_pad_is_hidden(editor):
    editor.table.selectRow(0)
    editor.btn_capture.setChecked(True)
    assert editor.overlay.capturing
    editor.key_search.setText("no-matching-pad-12345")
    assert all(editor.table.isRowHidden(r) for r in range(editor.table.rowCount()))
    assert not editor.overlay.capturing
    assert not editor.btn_capture.isEnabled()
    assert not editor.btn_remove_pad.isEnabled()
    editor.key_search.clear()
    assert not any(editor.table.isRowHidden(r) for r in range(editor.table.rowCount()))


def test_add_pad_clears_filter_and_selects_new_pad(editor):
    count = len(editor.cfg["keys"])
    editor.key_search.setText("no-matching-pad-12345")
    editor._add_pad()
    assert not editor.key_search.text()
    assert editor.table.currentRow() == count
    assert editor.btn_remove_pad.isEnabled()
    editor._remove_pad()
    assert len(editor.cfg["keys"]) == count


def test_close_flushes_pending_save(editor, monkeypatch):
    saved = []
    monkeypatch.setattr(settings_ui, "save_config", lambda cfg: saved.append(cfg["x"]))
    editor.sp_x.setValue(1234)
    assert editor.save_timer.isActive()
    editor.close()
    assert saved == [1234]
    assert not editor.save_timer.isActive()


def test_size_controls_stay_in_sync_after_overlay_resize(editor):
    editor.sl_scale.setValue(125)
    assert editor.cfg["scale"] == 1.25
    assert editor.sp_scale.value() == 1.25
    editor.cfg["scale"] = 0.75
    editor.overlay.config_changed.emit()
    assert editor.sl_scale.value() == 75
    assert editor.lbl_scale.text() == "75%"


def test_switching_pages_cancels_input_recording(editor):
    editor.nav.setCurrentRow(1)
    editor.table.selectRow(0)
    editor.btn_capture.setChecked(True)
    editor.nav.setCurrentRow(2)
    assert not editor.overlay.capturing
    assert not editor.btn_capture.isChecked()


def test_geometry_can_be_revealed_without_changing_mapping(editor):
    original = [dict(pad) for pad in editor.cfg["keys"]]
    assert editor.table.isColumnHidden(2)
    editor.show_geometry.setChecked(True)
    assert all(not editor.table.isColumnHidden(c) for c in range(6))
    editor.show_geometry.setChecked(False)
    assert editor.cfg["keys"] == original


def test_theme_switch_preserves_layout_and_table_state(editor):
    editor.cfg["keys"][0]["sc"] = 0x1e
    editor.cfg["keys"][0].pop("input", None)
    editor._fill_table()
    original = deepcopy(editor.cfg)
    editor.nav.setCurrentRow(1)
    editor.table.selectRow(0)
    editor.key_search.setText(editor.table.item(0, 0).text())
    for theme in ("light", "dark"):
        editor.theme_combo.setCurrentIndex(editor.theme_combo.findData(theme))
        colors = settings_ui.THEMES[theme]
        assert editor.palette().color(QPalette.ColorRole.Window) == QColor(colors["bg"])
        assert editor.table.item(0, 1).foreground().color() == QColor(colors["muted"])
        assert editor.table.currentRow() == 0
        assert editor.key_search.text() == editor.table.item(0, 0).text()
        assert editor.nav.currentRow() == 1
        assert editor.save_timer.isActive()
        assert {k: v for k, v in editor.cfg.items() if k != "theme"} == {
            k: v for k, v in original.items() if k != "theme"
        }


def test_light_theme_survives_save_and_restart(editor, monkeypatch, tmp_path):
    monkeypatch.setattr(overlay, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    editor.theme_combo.setCurrentIndex(editor.theme_combo.findData("light"))
    editor.close()
    source = PreviewOverlay()
    reopened = settings_ui.SettingsWindow(source)
    try:
        assert reopened.cfg["theme"] == "light"
        assert reopened.theme_combo.currentData() == "light"
        assert reopened.palette().color(QPalette.ColorRole.Window).lightness() > 230
        dialog = settings_ui.TemplateDialog(reopened)
        assert dialog.palette().color(QPalette.ColorRole.Window) == reopened.palette().color(QPalette.ColorRole.Window)
        dialog.deleteLater()
    finally:
        reopened.close()
        reopened.deleteLater()
        source.deleteLater()


def test_loading_layout_keeps_app_theme(editor, monkeypatch):
    editor.theme_combo.setCurrentIndex(editor.theme_combo.findData("light"))
    profile = deepcopy(editor.cfg)
    profile["theme"] = "dark"
    profile["x"] = 987
    monkeypatch.setattr(settings_ui, "load_profile", lambda name: profile)
    editor.profile_combo.addItem("Test layout")
    editor._profile_selected(editor.profile_combo.count() - 1)
    assert editor.cfg["x"] == 987
    assert editor.cfg["theme"] == "light"
    assert editor.theme_combo.currentData() == "light"


def test_switch_supports_keyboard_and_label_click(editor):
    editor.nav.setCurrentRow(2)
    editor.show()
    switch = editor.chk_bold
    original = switch.isChecked()
    switch.setFocus()
    QTest.keyClick(switch, Qt.Key.Key_Space)
    assert switch.isChecked() != original
    assert editor.cfg["font"]["bold"] == switch.isChecked()
    QTest.mouseClick(switch, Qt.MouseButton.LeftButton, pos=switch.rect().center())
    assert switch.isChecked() == original
    assert editor.cfg["font"]["bold"] == original


def test_visibility_switch_syncs_when_signals_are_blocked(editor):
    editor.chk_visible.blockSignals(True)
    editor.chk_visible.setChecked(True)
    assert editor.chk_visible.position == 1.0
    editor.chk_visible.setChecked(False)
    assert editor.chk_visible.position == 0.0
    editor.chk_visible.blockSignals(False)


def test_visual_layout_selects_blank_pad_even_with_search(editor):
    editor.cfg["keys"] = [
        {"label": "A", "col": -1, "row": 0},
        {"label": "", "col": 1, "row": 0},
    ]
    editor.cfg["sticks"] = []
    editor._fill_table()
    original = deepcopy(editor.cfg)
    editor.nav.setCurrentRow(1)
    editor.show()
    editor.show_all_pads.setChecked(True)
    QApplication.processEvents()
    assert editor.pad_layout.isVisible()
    editor.key_search.setText("A")
    rects = editor.pad_layout.layout_rects()
    assert len(rects) == 2
    assert all(editor.pad_layout.rect().contains(r.toAlignedRect()) for r in rects)
    QTest.mouseClick(editor.pad_layout, Qt.MouseButton.LeftButton, pos=rects[1].center().toPoint())
    assert editor.table.currentRow() == 1
    assert editor.pad_layout.selected == {1}
    assert not editor.key_search.text()
    assert editor.btn_capture.isEnabled()
    editor.show_all_pads.setChecked(False)
    assert editor.pad_layout.isHidden()
    assert editor.cfg == original


@pytest.mark.parametrize("axis, count, edge", [("row", 4, 4), ("col", 3, 5)])
def test_add_line_respects_dimensions_and_sticks(editor, axis, count, edge):
    editor.cfg["keys"] = [
        {"label": "A", "input": "A", "col": -0.5, "row": 0.5, "w": 2, "h": 1},
        {"label": "B", "col": 2, "row": 2, "w": 1, "h": 1},
    ]
    editor.cfg["sticks"] = [{"col": 3, "row": 2, "w": 2, "h": 2}]
    editor._fill_table()
    original = deepcopy(editor.cfg["keys"])
    editor.table.selectRow(0)
    editor.btn_capture.setChecked(True)
    button = editor.btn_add_row if axis == "row" else editor.btn_add_column
    button.click()
    added = editor.cfg["keys"][2:]
    assert len(added) == count
    assert editor.cfg["keys"][:2] == original
    assert all(k[axis] == edge and not overlay.pad_inputs(k) for k in added)
    assert editor.show_all_pads.isChecked()
    assert editor.table.currentRow() == 2
    assert not editor.overlay.capturing
    assert editor.save_timer.isActive()


def test_add_row_and_column_to_empty_layout(editor):
    editor.cfg["keys"] = []
    editor.cfg["sticks"] = []
    editor._fill_table()
    editor.btn_add_row.click()
    editor.btn_add_column.click()
    assert [(k["col"], k["row"]) for k in editor.cfg["keys"]] == [(0, 0), (1, 0)]
    assert editor.table.rowCount() == 2


def test_switch_flushes_layout_edits_and_remembers_selection(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    other = deepcopy(editor.cfg)
    other["x"] = 432
    overlay.save_profile("Another layout", other)
    editor._refresh_profiles()
    assert editor.profile_combo.findText("Unsaved layout") == -1
    editor.sp_x.setValue(1234)
    assert editor.save_timer.isActive()
    # The first entry is a real saved layout, including for save/delete actions.
    editor._profile_selected(0)
    assert overlay.load_profile("Test saved layout")["x"] == 1234
    assert editor.cfg["x"] == 432
    assert editor.delete_layout_action.isEnabled()
    restored = overlay.load_config()
    assert restored["profile"] == "Another layout"
    assert restored["x"] == 432
    editor.sp_x.setValue(987)
    editor.close()
    assert overlay.load_profile("Another layout")["x"] == 987
    editor._profile_selected(editor.profile_combo.findText("Test saved layout"))
    assert editor.cfg["x"] == 1234


def _buttons(widget):
    return [b.text() for b in widget.findChildren(settings_ui.QPushButton)]


def test_header_has_no_save_button(editor):
    assert "Save layout" not in _buttons(editor)


def test_deleting_current_layout_switches_to_first_remaining(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    monkeypatch.setattr(settings_ui.QMessageBox, "question", lambda *args: settings_ui.QMessageBox.StandardButton.Yes)
    overlay.save_profile("Another layout", dict(editor.cfg, x=432))
    editor._refresh_profiles()
    editor._profile_delete()
    assert overlay.list_profiles() == ["Another layout"]
    assert editor.cfg["profile"] == "Another layout" and editor.cfg["x"] == 432
    assert editor.profile_combo.currentText() == "Another layout"
    assert overlay.load_config()["profile"] == "Another layout"


def test_deleting_last_layout_reseeds_the_default(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    monkeypatch.setattr(settings_ui.QMessageBox, "question", lambda *args: settings_ui.QMessageBox.StandardButton.Yes)
    editor.sp_x.setValue(1234)
    editor._profile_delete()
    editor.close()
    assert overlay.list_profiles() == ["Cyborg 2 default"]
    assert editor.cfg["profile"] == "Cyborg 2 default"
    assert editor.profile_combo.currentText() == "Cyborg 2 default"
    assert overlay.load_config()["profile"] == "Cyborg 2 default"
    assert overlay.load_config()["x"] != 1234


def _menu_actions(editor):
    return [a.text() for a in editor.findChildren(settings_ui.QMenu)[0].actions()]


def test_more_menu_offers_rename_and_duplicate_not_save_as(editor):
    actions = _menu_actions(editor)
    assert "Rename layout…" in actions and "Duplicate layout…" in actions
    assert not any(a.startswith("Save as") for a in actions)


def test_new_layout_with_blank_name_uses_template_suggestion(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)

    def accept(dlg):
        dlg.name.setText("   ")
        return settings_ui.QDialog.DialogCode.Accepted

    monkeypatch.setattr(settings_ui.TemplateDialog, "exec", accept)
    editor._new_from_template()
    assert editor.cfg["profile"] == "Azeron Cyborg II"
    assert "Azeron Cyborg II" in overlay.list_profiles()


def test_new_layout_with_taken_name_gets_a_suffix(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    before = overlay.load_profile("Test saved layout")

    def accept(dlg):
        dlg.name.setText("test saved layout")
        return settings_ui.QDialog.DialogCode.Accepted

    monkeypatch.setattr(settings_ui.TemplateDialog, "exec", accept)
    editor._new_from_template()
    assert editor.cfg["profile"] == "test saved layout (2)"
    assert overlay.load_profile("Test saved layout") == before


def test_rename_dialog_refuses_taken_names_inline(editor):
    overlay.save_profile("Other layout", editor.cfg)
    dlg = settings_ui.RenameLayoutDialog(editor, "Test saved layout")
    ok = dlg.buttons.button(settings_ui.QDialogButtonBox.StandardButton.Ok)
    assert dlg.name.text() == "Test saved layout" and ok.isEnabled()
    dlg.name.setText("other layout")
    assert not ok.isEnabled() and not dlg.hint.text() == ""
    dlg.name.setText("Fresh name")
    assert ok.isEnabled()
    dlg.name.setText("   ")
    assert not ok.isEnabled()


def test_rename_updates_file_and_current_layout(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)

    def accept(dlg):
        dlg.name.setText("Renamed layout")
        return settings_ui.QDialog.DialogCode.Accepted

    monkeypatch.setattr(settings_ui.RenameLayoutDialog, "exec", accept)
    editor.sp_x.setValue(555)
    editor._profile_rename()
    assert overlay.list_profiles() == ["Renamed layout"]
    assert editor.cfg["profile"] == "Renamed layout"
    assert editor.profile_combo.currentText() == "Renamed layout"
    assert overlay.load_config()["profile"] == "Renamed layout"
    assert overlay.load_profile("Renamed layout")["x"] == 555


def test_duplicate_defaults_to_copy_name_and_switches_to_it(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    seen = {}

    def get_text(parent, title, label, text=""):
        seen["default"] = text
        return text, True

    monkeypatch.setattr(settings_ui.QInputDialog, "getText", get_text)
    editor.sp_x.setValue(321)
    editor._profile_duplicate()
    assert seen["default"] == "Test saved layout copy"
    assert sorted(overlay.list_profiles()) == ["Test saved layout", "Test saved layout copy"]
    assert editor.cfg["profile"] == "Test saved layout copy"
    assert overlay.load_profile("Test saved layout")["x"] == 321
    editor.sp_x.setValue(654)
    QTest.qWait(600)
    assert overlay.load_profile("Test saved layout copy")["x"] == 654
    assert overlay.load_profile("Test saved layout")["x"] == 321


def test_named_layout_autosaves_without_closing(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    editor.sp_x.setValue(1234)
    QTest.qWait(600)
    assert not editor.save_timer.isActive()
    assert overlay.load_profile("Test saved layout")["x"] == 1234
    assert overlay.load_config()["x"] == 1234


def test_switching_to_another_app_ends_on_screen_editing(editor):
    """Alt-tabbing to a game must not leave the overlay draggable/scroll-resizable:
    game clicks and weapon-scroll would move and resize it."""
    calls = []
    editor.overlay.set_edit_mode = calls.append
    editor.btn_move.setChecked(True)
    assert calls == [True]

    QApplication.instance().applicationStateChanged.emit(Qt.ApplicationState.ApplicationInactive)
    QTest.qWait(50)

    assert calls == [True, False]
    assert not editor.btn_move.isChecked()


def test_keyboard_shortcuts_card_has_the_edit_hotkey(editor):
    assert editor.hotkey_edits["edit"].text() == "E"


def test_edit_mode_started_elsewhere_flips_the_layout_button(editor):
    calls = []
    editor.overlay.set_edit_mode = calls.append
    editor.overlay.edit_mode_changed.emit(True)
    assert editor.btn_move.isChecked() and editor.btn_move.text() == "Done editing"
    editor.overlay.edit_mode_changed.emit(False)
    assert not editor.btn_move.isChecked() and editor.btn_move.text() == "Edit on screen"


# ---- ticket 12: select many pads --------------------------------------------
def _row_centre(editor, row):
    return editor.table.visualItemRect(editor.table.item(row, 0)).center()


def _show_keys_page(editor):
    editor.show()
    editor.nav.setCurrentRow(1)
    editor.show_all_pads.setChecked(True)
    editor.pad_layout.resize(640, 320)
    QTest.qWait(50)


def test_ctrl_click_selects_several_rows_and_the_layout_mirrors_them(editor):
    _show_keys_page(editor)
    editor.table.selectRow(0)
    QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, _row_centre(editor, 2))
    assert editor.selected_pads() == [0, 2]
    assert editor.pad_layout.selected == {0, 2}
    editor.table.clearSelection()
    editor.table.selectRow(1)
    QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ShiftModifier, _row_centre(editor, 3))
    assert editor.selected_pads() == [1, 2, 3]
    assert editor.pad_layout.selected == {1, 2, 3}


def test_layout_ctrl_click_and_drag_box_drive_the_table(editor):
    _show_keys_page(editor)
    rects = editor.pad_layout.layout_rects()
    QTest.mouseClick(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, rects[0].center().toPoint())
    assert editor.selected_pads() == [0]
    QTest.mouseClick(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, rects[1].center().toPoint())
    assert editor.selected_pads() == [0, 1]
    QTest.mouseClick(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, rects[1].center().toPoint())
    assert editor.selected_pads() == [0]
    box = rects[0].united(rects[1]).united(rects[2]).adjusted(-2, -2, 2, 2)
    inside = {i for i, r in enumerate(rects[:len(editor.cfg["keys"])]) if box.intersects(r)}
    QTest.mousePress(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, box.topLeft().toPoint())
    QTest.mouseMove(editor.pad_layout, box.bottomRight().toPoint())
    QTest.mouseRelease(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, box.bottomRight().toPoint())
    assert set(editor.selected_pads()) == inside and len(inside) >= 3


def test_ctrl_a_under_a_search_filter_selects_only_matching_pads(editor):
    _show_keys_page(editor)
    editor.key_search.setText("F")
    visible = [r for r in range(editor.table.rowCount()) if not editor.table.isRowHidden(r)]
    assert 0 < len(visible) < editor.table.rowCount()
    QTest.keyClick(editor.table, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert editor.selected_pads() == visible


def test_remove_deletes_the_selection_and_keeps_every_other_pad_in_place(editor):
    _show_keys_page(editor)
    keys = [dict(k) for k in editor.cfg["keys"]]
    sticks = len(editor.cfg.get("sticks", []))
    editor.table.selectRow(1)
    QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, _row_centre(editor, 3))
    assert editor.btn_remove_pad.text() == "Remove 2 pads"
    editor.btn_remove_pad.click()
    assert editor.cfg["keys"] == [k for i, k in enumerate(keys) if i not in (1, 3)]
    assert len(editor.cfg.get("sticks", [])) == sticks
    assert editor.selected_pads() == []


def test_delete_key_removes_the_selection_except_while_recording(editor):
    _show_keys_page(editor)
    n = len(editor.cfg["keys"])
    editor.table.selectRow(0)
    editor.btn_capture.setChecked(True)
    QTest.keyClick(editor.table, Qt.Key.Key_Delete)
    assert len(editor.cfg["keys"]) == n
    editor.btn_capture.setChecked(False)
    editor.table.selectRow(0)
    QTest.keyClick(editor.table, Qt.Key.Key_Delete)
    assert len(editor.cfg["keys"]) == n - 1
    rects = editor.pad_layout.layout_rects()
    QTest.mouseClick(editor.pad_layout, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, rects[0].center().toPoint())
    QTest.keyClick(editor.pad_layout, Qt.Key.Key_Delete)
    assert len(editor.cfg["keys"]) == n - 2


def test_selection_toolbar_shows_only_with_a_selection(editor):
    _show_keys_page(editor)
    assert not editor.selection_bar.isVisible()
    editor.table.selectRow(0)
    QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, _row_centre(editor, 1))
    assert editor.selection_bar.isVisible() and editor.selection_count.text() == "2 selected"
    editor.btn_clear_selection.click()
    assert editor.selected_pads() == [] and not editor.selection_bar.isVisible()


def test_search_sits_directly_above_the_table(editor):
    layout = editor.pads_card_layout
    items = [layout.itemAt(i) for i in range(layout.count())]
    table_at = next(i for i, it in enumerate(items) if it.widget() is editor.table)
    search_at = next(i for i, it in enumerate(items) if it.layout() is editor.search_row)
    assert table_at == search_at + 1


# ---- ticket 13: delete row / delete column -----------------------------------
def _load_template(editor, prof):
    editor.cfg["keys"] = [dict(k) for k in prof["keys"]]
    editor.cfg["sticks"] = [dict(st) for st in prof.get("sticks", [])]
    editor._fill_table()
    _show_keys_page(editor)


def _labels(editor):
    return [k["label"] for k in editor.cfg["keys"]]


def _select_labels(editor, *labels):
    rows = [i for i, k in enumerate(editor.cfg["keys"]) if k["label"] in labels]
    editor.table.clearSelection()
    for r in rows:
        QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, _row_centre(editor, r))
    assert editor.selected_pads() == rows


def test_delete_column_uses_centre_in_span_on_a_staggered_keyboard(editor):
    _load_template(editor, templates.keyboard_profile("60%", "US (ANSI)"))
    before = [dict(k) for k in editor.cfg["keys"]]
    _select_labels(editor, "Q")
    editor.btn_delete_column.click()
    gone = [k["label"] for k in before if k not in editor.cfg["keys"]]
    assert sorted(gone) == ["1", "A", "Q", "Win"]  # Z (quarter-unit overlap) stays
    assert "Z" in _labels(editor)
    assert all(k in before for k in editor.cfg["keys"])  # nobody moved


def test_delete_column_on_a_wide_pad_sweeps_its_span(editor):
    _load_template(editor, templates.keyboard_profile("60%", "US (ANSI)"))
    _select_labels(editor, "Space")
    editor.btn_delete_column.click()
    labels = _labels(editor)
    assert "Space" not in labels and "E" not in labels and "R" not in labels
    assert "Q" in labels and "W" in labels


def test_delete_column_with_two_columns_selected_removes_both(editor):
    _load_template(editor, templates.keyboard_profile("60%", "US (ANSI)"))
    _select_labels(editor, "Q", "W")
    editor.btn_delete_column.click()
    labels = _labels(editor)
    assert not {"1", "Q", "A", "W", "S", "Z", "2"} & set(labels)
    assert {"3", "X"} <= set(labels)


def test_delete_row_removes_the_row_and_leaves_sticks(editor):
    _load_template(editor, templates.azeron_profile("Cyborg II"))
    sticks = [dict(st) for st in editor.cfg["sticks"]]
    target = next(k for k in editor.cfg["keys"] if k["row"] == 3)
    _select_labels(editor, target["label"])
    editor.btn_delete_row.click()
    assert all(k["row"] != 3 for k in editor.cfg["keys"])
    assert any(k["row"] == 2 for k in editor.cfg["keys"]) and any(k["row"] == 4 for k in editor.cfg["keys"])
    assert editor.cfg["sticks"] == sticks


def test_delete_row_and_column_buttons_follow_the_selection(editor):
    _show_keys_page(editor)
    editor.table.clearSelection()
    assert not editor.btn_delete_row.isEnabled() and not editor.btn_delete_column.isEnabled()
    editor.table.selectRow(0)
    assert editor.btn_delete_row.isEnabled() and editor.btn_delete_column.isEnabled()


# ---- ticket 14: undo delete ---------------------------------------------------
def test_undo_restores_removed_pads_at_their_original_places(editor):
    _show_keys_page(editor)
    original = [dict(k) for k in editor.cfg["keys"]]
    editor.table.selectRow(1)
    QTest.mouseClick(editor.table.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.ControlModifier, _row_centre(editor, 3))
    editor.btn_remove_pad.click()
    assert editor.undo_bar.isVisible() and editor.btn_undo.text() == "Undo delete · 2 pads"
    editor.btn_undo.click()
    assert editor.cfg["keys"] == original
    assert editor.table.rowCount() == len(original)
    assert not editor.undo_bar.isVisible()
    editor.btn_undo.click()  # single level: nothing left to undo
    assert editor.cfg["keys"] == original


def test_undo_covers_row_column_and_delete_key(editor):
    _show_keys_page(editor)
    original = [dict(k) for k in editor.cfg["keys"]]
    editor.table.selectRow(0)
    editor.btn_delete_column.click()
    assert editor.undo_bar.isVisible() and len(editor.cfg["keys"]) < len(original)
    editor.btn_undo.click()
    assert editor.cfg["keys"] == original
    editor.table.selectRow(0)
    editor.btn_delete_row.click()
    assert editor.undo_bar.isVisible()
    editor.btn_undo.click()
    assert editor.cfg["keys"] == original
    editor.table.clearSelection()  # undo re-selects the restored pads
    editor.table.selectRow(2)
    QTest.keyClick(editor.table, Qt.Key.Key_Delete)
    assert editor.btn_undo.text() == "Undo delete · 1 pad"
    editor.btn_undo.click()
    assert editor.cfg["keys"] == original


def test_ctrl_z_undoes_unless_recording(editor):
    _show_keys_page(editor)
    original = [dict(k) for k in editor.cfg["keys"]]
    editor.table.selectRow(0)
    editor.btn_remove_pad.click()
    editor.table.selectRow(0)
    editor.btn_capture.setChecked(True)
    QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert len(editor.cfg["keys"]) == len(original) - 1
    editor.btn_capture.setChecked(False)
    QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert editor.cfg["keys"] == original


def test_a_non_delete_edit_discards_the_undo(editor):
    _show_keys_page(editor)
    n = len(editor.cfg["keys"])
    editor.table.selectRow(0)
    editor.btn_remove_pad.click()
    assert editor.undo_bar.isVisible()
    editor.sp_x.setValue(editor.sp_x.value() + 5)
    assert not editor.undo_bar.isVisible()
    QTest.keyClick(editor, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert len(editor.cfg["keys"]) == n - 1

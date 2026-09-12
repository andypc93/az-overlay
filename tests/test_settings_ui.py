"""Settings interactions without keyboard hooks or writes to user settings."""

from copy import deepcopy
import json

import pytest
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

import overlay
import settings_ui


class PreviewOverlay(QWidget):
    config_changed = Signal()
    key_captured = Signal(object)

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
    assert editor.pad_layout.selected == 1
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


def test_unnamed_edits_are_not_saved_on_close(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    before = overlay.load_config()
    editor.cfg["profile"] = ""
    editor._refresh_profiles()
    assert editor.profile_combo.currentIndex() == -1
    assert not editor.delete_layout_action.isEnabled()
    editor.sp_x.setValue(1234)
    editor.theme_combo.setCurrentIndex(editor.theme_combo.findData("light"))
    editor.close()
    restored = overlay.load_config()
    assert restored["profile"] == before["profile"]
    assert restored["x"] == before["x"]
    assert restored["theme"] == "light"
    assert overlay.load_profile(before["profile"])["x"] == before["x"]


def test_delete_does_not_recreate_layout_from_pending_save(editor, monkeypatch):
    monkeypatch.setattr(settings_ui, "save_config", overlay.save_config)
    monkeypatch.setattr(settings_ui.QMessageBox, "question", lambda *args: settings_ui.QMessageBox.StandardButton.Yes)
    editor.sp_x.setValue(1234)
    editor._profile_delete()
    editor.close()
    assert overlay.list_profiles() == []
    assert editor.profile_combo.count() == 0
    assert editor.profile_combo.currentIndex() == -1
    assert overlay.load_config()["profile"] == ""
    assert overlay.load_config()["x"] != 1234


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

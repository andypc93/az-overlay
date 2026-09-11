"""Settings interactions without keyboard hooks or writes to user settings."""

from copy import deepcopy

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
def editor(monkeypatch):
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
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

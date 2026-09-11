"""Settings interactions without keyboard hooks or writes to user settings."""

import pytest
from PySide6.QtCore import Signal
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
    monkeypatch.setattr(settings_ui, "save_config", lambda cfg: None)
    source = PreviewOverlay()
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

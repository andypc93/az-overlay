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

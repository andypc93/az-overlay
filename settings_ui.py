"""Settings window for the overlay. Every edit applies live and autosaves."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QColorDialog, QDoubleSpinBox, QFontComboBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from overlay import label_for_vk, save_config, vks_for_label

COLOR_FIELDS = [
    ("idle_fill", "Fill"),
    ("idle_outline", "Border"),
    ("idle_text", "Text"),
    ("pressed_fill", "Fill"),
    ("pressed_outline", "Border"),
    ("pressed_text", "Text"),
]

STYLE = """
QWidget { background: #1b1b1b; color: #e8e8e8; font-family: 'Segoe UI'; font-size: 10pt; }
QGroupBox { border: 1px solid #333; border-radius: 6px; margin-top: 10px; padding: 8px 6px 6px 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #c9d400; }
QPushButton { background: #2a2a2a; border: 1px solid #444; border-radius: 5px; padding: 5px 12px; }
QPushButton:hover { border-color: #c9d400; }
QPushButton:checked { background: #c9d400; color: #000; border-color: #c9d400; }
QLineEdit, QSpinBox, QDoubleSpinBox { background: #262626; border: 1px solid #444; border-radius: 4px; padding: 3px; }
QTableWidget { background: #202020; gridline-color: #333; border: 1px solid #333; }
QHeaderView::section { background: #2a2a2a; padding: 4px; border: none; }
QTabWidget::pane { border: 1px solid #333; border-radius: 6px; }
QTabBar::tab { background: #242424; padding: 6px 14px; border-top-left-radius: 5px; border-top-right-radius: 5px; }
QTabBar::tab:selected { background: #c9d400; color: #000; }
QSlider::groove:horizontal { height: 4px; background: #444; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -6px 0; background: #c9d400; border-radius: 7px; }
"""


class ColorButton(QPushButton):
    def __init__(self, cfg, key, on_change):
        super().__init__()
        self.cfg, self.key, self.on_change = cfg, key, on_change
        self.setFixedWidth(120)
        self.clicked.connect(self.pick)
        self.refresh()

    def refresh(self):
        col = QColor(self.cfg["colors"][self.key])
        fg = "#000" if col.lightness() > 128 else "#fff"
        self.setText(col.name().upper())
        self.setStyleSheet(f"background:{col.name()}; color:{fg}; border:1px solid #666; border-radius:5px; padding:5px;")

    def pick(self):
        dlg = QColorDialog(QColor(self.cfg["colors"][self.key]), self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dlg.currentColorChanged.connect(self._live)
        start = self.cfg["colors"][self.key]
        if dlg.exec():
            self._live(dlg.selectedColor())
        else:
            self.cfg["colors"][self.key] = start
            self.refresh()
            self.on_change()

    def _live(self, col):
        if col.isValid():
            self.cfg["colors"][self.key] = col.name()
            self.refresh()
            self.on_change()


class SettingsWindow(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.cfg = overlay.cfg
        self.setWindowTitle("az-overlay settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet(STYLE)
        self.resize(560, 620)
        self._loading = False

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(self._save_now)

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)
        tabs.addTab(self._layout_tab(), "Layout")
        tabs.addTab(self._keys_tab(), "Keys")
        tabs.addTab(self._colors_tab(), "Text && Colors")

        bottom = QHBoxLayout()
        self.status = QLabel("")
        self.status.setStyleSheet("color:#8a8a8a;")
        bottom.addWidget(self.status, 1)
        self.chk_visible = QCheckBox("Overlay visible")
        self.chk_visible.setChecked(True)
        self.chk_visible.toggled.connect(self.overlay.setVisible)
        bottom.addWidget(self.chk_visible)
        quit_btn = QPushButton("Quit overlay")
        quit_btn.clicked.connect(self.overlay.shutdown)
        bottom.addWidget(quit_btn)
        root.addLayout(bottom)

        overlay.config_changed.connect(self._sync_from_overlay)
        overlay.key_captured.connect(self._on_key_captured)

    # ---- tabs ---------------------------------------------------------
    def _layout_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        self.btn_move = QPushButton("Move / resize with mouse")
        self.btn_move.setCheckable(True)
        self.btn_move.setToolTip("Drag the overlay to move it. Scroll wheel over it to resize.")
        self.btn_move.toggled.connect(self._toggle_move)
        v.addWidget(self.btn_move)
        tip = QLabel("While on: drag the overlay to move it, scroll over it to resize. Unassigned pads show as dashed ghosts.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#8a8a8a;")
        v.addWidget(tip)

        g = QGroupBox("Position && size")
        f = QFormLayout(g)
        self.sp_x = QSpinBox(); self.sp_x.setRange(-10000, 10000)
        self.sp_y = QSpinBox(); self.sp_y.setRange(-10000, 10000)
        self.sp_scale = QDoubleSpinBox(); self.sp_scale.setRange(0.2, 3.0); self.sp_scale.setSingleStep(0.05); self.sp_scale.setDecimals(2)
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal); self.sl_opacity.setRange(10, 100)
        self.lbl_opacity = QLabel()
        for sp, key in ((self.sp_x, "x"), (self.sp_y, "y")):
            sp.setValue(self.cfg[key])
            sp.valueChanged.connect(lambda val, k=key: self._set(k, val))
        self.sp_scale.setValue(self.cfg.get("scale", 1.0))
        self.sp_scale.valueChanged.connect(lambda val: self._set("scale", round(val, 3)))
        self.sl_opacity.setValue(int(self.cfg.get("opacity", 0.85) * 100))
        self.sl_opacity.valueChanged.connect(self._opacity)
        self.lbl_opacity.setText(f"{self.sl_opacity.value()}%")
        f.addRow("X", self.sp_x)
        f.addRow("Y", self.sp_y)
        f.addRow("Scale", self.sp_scale)
        row = QHBoxLayout(); row.addWidget(self.sl_opacity, 1); row.addWidget(self.lbl_opacity)
        f.addRow("Opacity", row)
        v.addWidget(g)

        g2 = QGroupBox("Pad shape")
        f2 = QFormLayout(g2)
        self.sp_cw = QSpinBox(); self.sp_cw.setRange(20, 400); self.sp_cw.setValue(self.cfg["cell_w"])
        self.sp_ch = QSpinBox(); self.sp_ch.setRange(20, 400); self.sp_ch.setValue(self.cfg["cell_h"])
        self.sp_gap = QSpinBox(); self.sp_gap.setRange(0, 100); self.sp_gap.setValue(self.cfg["gap"])
        for sp, key in ((self.sp_cw, "cell_w"), (self.sp_ch, "cell_h"), (self.sp_gap, "gap")):
            sp.valueChanged.connect(lambda val, k=key: self._set(k, val))
        f2.addRow("Pad width", self.sp_cw)
        f2.addRow("Pad height", self.sp_ch)
        f2.addRow("Gap", self.sp_gap)
        v.addWidget(g2)

        g3 = QGroupBox("Hotkeys (always with Ctrl+Alt)")
        f3 = QFormLayout(g3)
        for name, text in (("toggle", "Show / hide"), ("settings", "Open settings"), ("quit", "Quit")):
            le = QLineEdit(self.cfg["hotkeys"].get(name, ""))
            le.setMaximumWidth(120)
            le.editingFinished.connect(lambda le=le, n=name: self._hotkey(n, le))
            f3.addRow(text, le)
        v.addWidget(g3)
        v.addStretch(1)
        return w

    def _keys_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        tip = QLabel("Label = what the Cyborg sends for that pad (Q, 9, Alt, Page Up, F1…). "
                     "Empty label = pad is hidden. Col/Row place it on the grid.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#8a8a8a;")
        v.addWidget(tip)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Label", "Col", "Row"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemChanged.connect(self._table_edited)
        v.addWidget(self.table, 1)

        row = QHBoxLayout()
        self.btn_capture = QPushButton("Capture key for selected pad")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setToolTip("Select a row, click this, then press the Cyborg button.")
        self.btn_capture.toggled.connect(self._toggle_capture)
        btn_add = QPushButton("Add pad")
        btn_add.clicked.connect(self._add_pad)
        btn_del = QPushButton("Remove pad")
        btn_del.clicked.connect(self._remove_pad)
        row.addWidget(self.btn_capture, 1)
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        v.addLayout(row)

        g = QGroupBox("Thumbstick (keyboard mode)")
        grid = QGridLayout(g)
        j = self.cfg.setdefault("joystick", {"col": 6, "row": 3, "cols": 2, "rows": 2,
                                             "up": "W", "left": "A", "down": "S", "right": "D"})
        self.chk_joy = QCheckBox("Show thumbstick")
        self.chk_joy.setChecked(j.get("enabled", True))
        self.chk_joy.toggled.connect(lambda on: self._set_joy("enabled", on))
        grid.addWidget(self.chk_joy, 0, 0, 1, 4)
        self.joy_edits = {}
        for i, (name, text) in enumerate((("up", "Up"), ("left", "Left"), ("down", "Down"), ("right", "Right"))):
            le = QLineEdit(j.get(name, ""))
            le.setMaximumWidth(90)
            le.editingFinished.connect(lambda le=le, n=name: self._joy_label(n, le))
            self.joy_edits[name] = le
            grid.addWidget(QLabel(text), 1, i * 2)
            grid.addWidget(le, 1, i * 2 + 1)
        for i, (name, text) in enumerate((("col", "Col"), ("row", "Row"))):
            sp = QSpinBox(); sp.setRange(0, 40); sp.setValue(j.get(name, 0))
            sp.valueChanged.connect(lambda val, n=name: self._set_joy(n, val))
            grid.addWidget(QLabel(text), 2, i * 2)
            grid.addWidget(sp, 2, i * 2 + 1)
        v.addWidget(g)

        self._fill_table()
        return w

    def _colors_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)

        gf = QGroupBox("Key text")
        ff = QFormLayout(gf)
        fnt = self.cfg["font"]
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(fnt["family"]))
        self.font_combo.currentFontChanged.connect(lambda f: self._set_font("family", f.family()))
        self.sp_font = QSpinBox(); self.sp_font.setRange(4, 72); self.sp_font.setValue(int(fnt["size"]))
        self.sp_font.setSuffix(" pt (at scale 1.0)")
        self.sp_font.valueChanged.connect(lambda v: self._set_font("size", v))
        self.chk_bold = QCheckBox("Bold"); self.chk_bold.setChecked(bool(fnt["bold"]))
        self.chk_bold.toggled.connect(lambda on: self._set_font("bold", on))
        ff.addRow("Font", self.font_combo)
        ff.addRow("Size", self.sp_font)
        ff.addRow("", self.chk_bold)
        v.addWidget(gf)

        self.color_buttons = []
        for title, prefix in (("Idle (not pressed)", "idle_"), ("Pressed", "pressed_")):
            g = QGroupBox(title)
            f = QFormLayout(g)
            for key, text in COLOR_FIELDS:
                if key.startswith(prefix):
                    b = ColorButton(self.cfg, key, self._apply)
                    self.color_buttons.append(b)
                    f.addRow(text, b)
            v.addWidget(g)
        reset = QPushButton("Reset colors to default")
        reset.clicked.connect(self._reset_colors)
        v.addWidget(reset)
        v.addStretch(1)
        return w

    # ---- behaviour ----------------------------------------------------
    def present(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        self.btn_move.setChecked(False)
        self.btn_capture.setChecked(False)
        e.accept()

    def _apply(self):
        self.overlay.apply()
        self._schedule_save()

    def _set(self, key, val):
        if self._loading:
            return
        self.cfg[key] = val
        self._apply()

    def _opacity(self, val):
        self.lbl_opacity.setText(f"{val}%")
        self._set("opacity", val / 100)

    def _hotkey(self, name, le):
        try:
            vks_for_label(le.text())
        except ValueError:
            le.setText(self.cfg["hotkeys"].get(name, ""))
            self._flash("Unknown key name")
            return
        self.cfg["hotkeys"][name] = le.text().strip()
        self._apply()

    def _toggle_move(self, on):
        self.overlay.set_edit_mode(on)
        self.btn_move.setText("Done moving" if on else "Move / resize with mouse")
        if on:
            self.overlay.show()
            self.chk_visible.setChecked(True)

    def _sync_from_overlay(self):
        self._loading = True
        self.sp_x.setValue(self.cfg["x"])
        self.sp_y.setValue(self.cfg["y"])
        self.sp_scale.setValue(self.cfg.get("scale", 1.0))
        self._loading = False
        self._schedule_save()

    # keys table
    def _fill_table(self):
        self._loading = True
        self.table.setRowCount(0)
        for k in self.cfg["keys"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(k["label"]))
            for c, key in ((1, "col"), (2, "row")):
                it = QTableWidgetItem(str(k[key]))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, it)
        self._loading = False

    def _table_edited(self, item):
        if self._loading:
            return
        r, c = item.row(), item.column()
        k = self.cfg["keys"][r]
        text = item.text().strip()
        if c == 0:
            try:
                vks_for_label(text)
            except ValueError:
                self._loading = True
                item.setText(k["label"])
                self._loading = False
                self._flash(f"Unknown key name: {text}")
                return
            k["label"] = text
        else:
            try:
                k["col" if c == 1 else "row"] = max(0, int(text))
            except ValueError:
                self._loading = True
                item.setText(str(k["col" if c == 1 else "row"]))
                self._loading = False
                return
        self._apply()

    def _add_pad(self):
        used = {(k["col"], k["row"]) for k in self.cfg["keys"]}
        col = row = 0
        while (col, row) in used:
            col += 1
            if col > 12:
                col, row = 0, row + 1
        self.cfg["keys"].append({"label": "", "col": col, "row": row})
        self._fill_table()
        self.table.selectRow(self.table.rowCount() - 1)
        self._apply()

    def _remove_pad(self):
        r = self.table.currentRow()
        if r < 0:
            return
        del self.cfg["keys"][r]
        self._fill_table()
        self._apply()

    def _toggle_capture(self, on):
        if on and self.table.currentRow() < 0:
            self.btn_capture.setChecked(False)
            self._flash("Select a pad row first")
            return
        self.overlay.capturing = on
        self.btn_capture.setText("Press a button on the Cyborg…" if on else "Capture key for selected pad")

    def _on_key_captured(self, vk):
        self.btn_capture.setChecked(False)
        label = label_for_vk(vk)
        r = self.table.currentRow()
        if label is None or r < 0:
            self._flash(f"Unknown key (vk {vk})")
            return
        self.cfg["keys"][r]["label"] = label
        self._loading = True
        self.table.item(r, 0).setText(label)
        self._loading = False
        self._flash(f"Pad set to {label}")
        self._apply()

    def _set_joy(self, key, val):
        self.cfg["joystick"][key] = val
        self._apply()

    def _joy_label(self, name, le):
        try:
            vks_for_label(le.text())
        except ValueError:
            le.setText(self.cfg["joystick"].get(name, ""))
            self._flash("Unknown key name")
            return
        self._set_joy(name, le.text().strip())

    def _set_font(self, key, val):
        if self._loading:
            return
        self.cfg["font"][key] = val
        self._apply()

    def _reset_colors(self):
        from overlay import DEFAULT_COLORS
        self.cfg["colors"].update(DEFAULT_COLORS)
        for b in self.color_buttons:
            b.refresh()
        self._apply()

    # save
    def _schedule_save(self):
        self.save_timer.start()

    def _save_now(self):
        try:
            save_config(self.cfg)
            self._flash("Saved")
        except OSError as e:
            self._flash(f"Save failed: {e}")

    def _flash(self, text):
        self.status.setText(text)
        QTimer.singleShot(2500, lambda: self.status.setText("") if self.status.text() == text else None)

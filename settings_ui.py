"""Settings window for the overlay. Every edit applies live and autosaves."""

import os
import tempfile

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPalette, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QScrollArea, QSlider, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import templates
from gamepad import is_gamepad_input
from overlay import (APP_NAME, DEFAULT_COLORS, GAMEPAD_LABELS, PROFILE_KEYS, delete_profile,
                     label_for_token, list_profiles, load_profile, migrate, pad_inputs, parse_input,
                     save_config, save_profile, vks_for_label)

# Palette: graphite surfaces, one accent (the overlay's own yellow-green), used sparingly.
BG = "#17181b"
CARD = "#1f2126"
FIELD = "#26282e"
LINE = "#2e3138"
TEXT = "#e6e7ea"
MUTED = "#8b8f98"
ACCENT = "#c9d400"


def dark_palette():
    """Fusion draws arrows, checkmarks etc. from the palette, so make it dark."""
    pal = QPalette()
    for role, col in (
        (QPalette.ColorRole.Window, BG), (QPalette.ColorRole.WindowText, TEXT),
        (QPalette.ColorRole.Base, FIELD), (QPalette.ColorRole.AlternateBase, CARD),
        (QPalette.ColorRole.Text, TEXT), (QPalette.ColorRole.Button, FIELD),
        (QPalette.ColorRole.ButtonText, TEXT), (QPalette.ColorRole.Highlight, ACCENT),
        (QPalette.ColorRole.HighlightedText, "#000000"), (QPalette.ColorRole.ToolTipBase, CARD),
        (QPalette.ColorRole.ToolTipText, TEXT), (QPalette.ColorRole.PlaceholderText, MUTED),
    ):
        pal.setColor(role, QColor(col))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#5c6068"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#5c6068"))
    return pal


def _arrow_icon():
    """Qt stylesheets can't draw arrows in a chosen color; ship a tiny PNG instead."""
    path = os.path.join(tempfile.gettempdir(), "az-overlay-arrow.png")
    if not os.path.exists(path):
        pm = QPixmap(20, 20)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(TEXT))
        p.drawPolygon(QPolygonF([QPointF(4, 7), QPointF(16, 7), QPointF(10, 13)]))
        p.end()
        pm.save(path)
    return path.replace("\\", "/")


def style():
    """Stylesheet, built at runtime (needs a QApplication for the arrow icon)."""
    ARROW = _arrow_icon()
    return f"""
QWidget {{ background: {BG}; color: {TEXT}; font-family: 'Segoe UI'; font-size: 10pt; }}
QLabel {{ background: transparent; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#section {{ color: {MUTED}; font-size: 8.5pt; font-weight: 600; letter-spacing: 1px; }}
QLabel#brand {{ font-family: 'Segoe UI Variable Display', 'Segoe UI'; font-size: 13pt; font-weight: 600; }}
QFrame#header {{ background: {CARD}; border-bottom: 1px solid {LINE}; }}
QFrame#footer {{ background: {CARD}; border-top: 1px solid {LINE}; }}
QFrame#card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 8px; }}
QFrame#card QWidget {{ background: transparent; }}
QListWidget#nav {{ background: {BG}; border: none; border-right: 1px solid {LINE}; outline: 0; padding: 8px 0; }}
QListWidget#nav::item {{ padding: 9px 16px; margin: 2px 8px; border-radius: 6px; color: {MUTED}; }}
QListWidget#nav::item:hover {{ background: {CARD}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: {CARD}; color: {TEXT}; border-left: 3px solid {ACCENT}; padding-left: 13px; }}
QScrollArea {{ border: none; }}
QPushButton {{ background: {FIELD}; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: #4a4e58; background: #2c2f36; }}
QPushButton:pressed {{ background: #22242a; }}
QPushButton:checked {{ background: {ACCENT}; color: #000; border-color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; color: #000; border-color: {ACCENT}; font-weight: 600; }}
QPushButton#primary:hover {{ background: #d9e41a; }}
QPushButton#quiet {{ background: transparent; border-color: transparent; color: {MUTED}; }}
QPushButton#quiet:hover {{ color: {TEXT}; background: {FIELD}; }}
QPushButton#step {{ font-size: 13pt; padding: 0; min-width: 32px; max-width: 32px; min-height: 30px; max-height: 30px; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {{
    background: {FIELD}; border: 1px solid {LINE}; border-radius: 6px; padding: 5px 8px; min-height: 20px; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 26px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url({ARROW}); width: 10px; height: 10px; }}
QLineEdit, QSpinBox, QDoubleSpinBox {{ selection-background-color: {ACCENT}; selection-color: #000; }}
QComboBox QAbstractItemView {{ background: {CARD}; border: 1px solid {LINE}; selection-background-color: {FIELD}; selection-color: {TEXT}; }}
QTableWidget {{ background: {FIELD}; gridline-color: {LINE}; border: 1px solid {LINE}; border-radius: 6px; selection-background-color: #3a3d14; selection-color: {TEXT}; }}
QHeaderView::section {{ background: {CARD}; color: {MUTED}; padding: 6px; border: none; border-bottom: 1px solid {LINE}; font-size: 8.5pt; font-weight: 600; }}
QSlider {{ min-height: 26px; background: transparent; }}
QSlider::groove:horizontal {{ height: 4px; background: {LINE}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 14px; margin: -6px 0; background: {TEXT}; border-radius: 7px; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #4a4e58; border-radius: 4px; background: {FIELD}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QToolTip {{ background: {CARD}; color: {TEXT}; border: 1px solid {LINE}; padding: 4px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {LINE}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""



# ---- small building blocks ------------------------------------------------
def section(title):
    lbl = QLabel(title.upper())
    lbl.setObjectName("section")
    return lbl


def muted(text):
    lbl = QLabel(text)
    lbl.setObjectName("muted")
    lbl.setWordWrap(True)
    return lbl


def card():
    f = QFrame()
    f.setObjectName("card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    return f, lay


def form():
    f = QFormLayout()
    f.setHorizontalSpacing(16)
    f.setVerticalSpacing(8)
    f.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    return f


def stepper(spin):
    """Wrap a spinbox with big - / + buttons (the native arrows are tiny)."""
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(4)
    minus, plus = QPushButton("−"), QPushButton("+")
    for b in (minus, plus):
        b.setObjectName("step")
        b.setAutoRepeat(True)
        b.setAutoRepeatDelay(350)
        b.setAutoRepeatInterval(60)
        b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    minus.clicked.connect(spin.stepDown)
    plus.clicked.connect(spin.stepUp)
    h.addWidget(minus)
    h.addWidget(spin, 1)
    h.addWidget(plus)
    return w


class ColorButton(QPushButton):
    def __init__(self, cfg, key, on_change):
        super().__init__()
        self.cfg, self.key, self.on_change = cfg, key, on_change
        self.setFixedSize(112, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.pick)
        self.refresh()

    def refresh(self):
        col = QColor(self.cfg["colors"][self.key])
        fg = "#000" if col.lightness() > 128 else "#fff"
        self.setText(col.name().upper())
        self.setStyleSheet(f"background:{col.name()}; color:{fg}; border:1px solid {LINE}; "
                           f"border-radius:6px; font-family:Consolas,'Segoe UI'; font-size:9.5pt;")

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


class PadPreview(QWidget):
    """Two sample keys, idle and pressed, drawn with the live config."""

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setFixedHeight(150)

    def paintEvent(self, _e):
        c = {k: QColor(v) for k, v in self.cfg["colors"].items()}
        fnt = self.cfg["font"]
        font = QFont(fnt["family"], int(fnt["size"]),
                     QFont.Weight.Bold if fnt["bold"] else QFont.Weight.Normal)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.cfg["cell_w"] * 0.9
        h = min(self.cfg["cell_h"] * 0.9, self.height() - 24)
        gap = 28
        x0 = (self.width() - (2 * w + gap)) / 2
        y0 = (self.height() - h - 18) / 2
        r = 10
        circle = self.cfg.get("shape") == "circle"
        for x, state in ((x0, "idle"), (x0 + w + gap, "pressed")):
            rect = QRectF(x, y0, w, h)
            if state == "pressed":
                glow = QColor(c["pressed_outline"])
                for i, spread in enumerate((6, 3)):
                    glow.setAlphaF(0.18 / (i + 1))
                    p.setPen(QPen(glow, spread * 2))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(rect, r, r)
            p.setBrush(QBrush(c[f"{state}_fill"]))
            p.setPen(QPen(c[f"{state}_outline"], 1.2 if state == "idle" else 2.2))
            p.drawRoundedRect(rect, r, r)
            p.setFont(font)
            p.setPen(c[f"{state}_text"])
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, "Space")
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(MUTED))
            p.drawText(QRectF(x, y0 + h + 4, w, 16), Qt.AlignmentFlag.AlignCenter, state)
        p.end()


class TemplateDialog(QDialog):
    """Device -> template -> keyboard layout -> name."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("New layout from template")
        self.setPalette(parent.palette())
        self.setStyleSheet(parent.styleSheet())
        self.setMinimumWidth(420)
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(12)
        f = form()
        self.device = QComboBox()
        self.device.addItems(templates.DEVICES)
        self.template = QComboBox()
        self.layout_combo = QComboBox()
        self.name = QLineEdit()
        f.addRow("Device", self.device)
        f.addRow("Template", self.template)
        f.addRow("Keyboard layout", self.layout_combo)
        f.addRow("Name", self.name)
        v.addLayout(f)
        v.addWidget(muted("Creates a new saved layout and switches to it. "
                          "Keyboard keys are matched by physical position, so any Windows layout works."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primary")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        v.addWidget(buttons)
        self.device.currentTextChanged.connect(self._device_changed)
        self.template.currentTextChanged.connect(self._suggest)
        self.layout_combo.currentTextChanged.connect(self._suggest)
        self._device_changed(self.device.currentText())

    def _device_changed(self, device):
        self.template.blockSignals(True)
        self.template.clear()
        self.template.addItems(templates.templates_for(device))
        self.template.blockSignals(False)
        layouts = templates.layouts_for(device)
        self.layout_combo.blockSignals(True)
        self.layout_combo.clear()
        self.layout_combo.addItems(layouts)
        self.layout_combo.setEnabled(bool(layouts))
        self.layout_combo.blockSignals(False)
        self._suggest()

    def _suggest(self, *_):
        self.name.setText(templates.suggested_name(self.device.currentText(), self.template.currentText(),
                                                   self.layout_combo.currentText() or None))

    def result_profile(self):
        return templates.build(self.device.currentText(), self.template.currentText(),
                               self.layout_combo.currentText() or None)


# ---- the window ------------------------------------------------------------
class SettingsWindow(QWidget):
    PAGES = ("Layout", "Keys", "Appearance")

    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.cfg = overlay.cfg
        self.setWindowTitle(APP_NAME)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setPalette(dark_palette())
        self.setStyleSheet(style())
        self.resize(780, 660)
        self.setMinimumSize(600, 480)
        self._loading = False

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(self._save_now)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(150)
        for name in self.PAGES:
            QListWidgetItem(name, self.nav)
        self.stack = QStackedWidget()
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)
        root.addWidget(self._footer())

        self._build_pages()
        self.nav.setCurrentRow(0)

        overlay.config_changed.connect(self._sync_from_overlay)
        overlay.key_captured.connect(self._on_key_captured)

    # ---- chrome -------------------------------------------------------
    def _header(self):
        f = QFrame()
        f.setObjectName("header")
        h = QHBoxLayout(f)
        h.setContentsMargins(20, 12, 20, 12)
        h.setSpacing(10)
        brand = QLabel(APP_NAME)
        brand.setObjectName("brand")
        h.addWidget(brand)
        h.addStretch(1)
        b_tpl = QPushButton("+ New layout")
        b_tpl.setToolTip("Create a layout from a template: Azeron, keyboards, Xbox, PlayStation")
        b_tpl.clicked.connect(self._new_from_template)
        h.addWidget(b_tpl)
        h.addSpacing(12)
        h.addWidget(muted("Layout"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(200)
        self.profile_combo.activated.connect(self._profile_selected)
        h.addWidget(self.profile_combo)
        b_save = QPushButton("Save")
        b_save.setObjectName("primary")
        b_save.setToolTip("Save current settings into the selected layout")
        b_save.clicked.connect(self._profile_save)
        b_new = QPushButton("Save as…")
        b_new.clicked.connect(self._profile_save_as)
        b_del = QPushButton("Delete")
        b_del.setObjectName("quiet")
        b_del.clicked.connect(self._profile_delete)
        for b in (b_save, b_new, b_del):
            h.addWidget(b)
        self._refresh_profiles()
        return f

    def _footer(self):
        f = QFrame()
        f.setObjectName("footer")
        h = QHBoxLayout(f)
        h.setContentsMargins(20, 10, 20, 10)
        self.status = muted("")
        h.addWidget(self.status, 1)
        self.chk_visible = QCheckBox("Overlay visible")
        self.chk_visible.setChecked(True)
        self.chk_visible.toggled.connect(self.overlay.setVisible)
        h.addWidget(self.chk_visible)
        quit_btn = QPushButton("Quit overlay")
        quit_btn.setObjectName("quiet")
        quit_btn.clicked.connect(self.overlay.shutdown)
        h.addWidget(quit_btn)
        return f

    def _page(self, *cards):
        """Scrollable page holding a column of cards."""
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(14)
        for c in cards:
            v.addWidget(c)
        v.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)
        return scroll

    def _build_pages(self):
        self.stack.addWidget(self._layout_page())
        self.stack.addWidget(self._keys_page())
        self.stack.addWidget(self._appearance_page())

    def _rebuild_tabs(self):
        """Recreate every widget from cfg (after loading a profile)."""
        idx = self.stack.currentIndex()
        self.btn_move.setChecked(False)
        self.btn_capture.setChecked(False)
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self._build_pages()
        self.stack.setCurrentIndex(idx)

    # ---- pages --------------------------------------------------------
    def _layout_page(self):
        c1, l1 = card()
        l1.addWidget(section("Place it"))
        self.btn_move = QPushButton("Move / resize with mouse")
        self.btn_move.setCheckable(True)
        self.btn_move.setMinimumHeight(36)
        self.btn_move.toggled.connect(self._toggle_move)
        l1.addWidget(self.btn_move)
        l1.addWidget(muted("While on, the overlay turns solid: drag it to move, scroll to resize, "
                           "click a key then press its Cyborg button to rebind, right-click a key to clear it."))
        f = form()
        self.sp_x = QSpinBox(); self.sp_x.setRange(-10000, 10000)
        self.sp_y = QSpinBox(); self.sp_y.setRange(-10000, 10000)
        self.sp_scale = QDoubleSpinBox(); self.sp_scale.setRange(0.2, 3.0); self.sp_scale.setSingleStep(0.05); self.sp_scale.setDecimals(2)
        for sp, key in ((self.sp_x, "x"), (self.sp_y, "y")):
            sp.setValue(self.cfg[key])
            sp.valueChanged.connect(lambda val, k=key: self._set(k, val))
        self.sp_scale.setValue(self.cfg.get("scale", 1.0))
        self.sp_scale.valueChanged.connect(lambda val: self._set("scale", round(val, 3)))
        f.addRow("X", stepper(self.sp_x))
        f.addRow("Y", stepper(self.sp_y))
        f.addRow("Scale", stepper(self.sp_scale))
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal); self.sl_opacity.setRange(10, 100)
        self.sl_opacity.setValue(int(self.cfg.get("opacity", 0.85) * 100))
        self.lbl_opacity = muted(f"{self.sl_opacity.value()}%")
        self.lbl_opacity.setFixedWidth(40)
        self.sl_opacity.valueChanged.connect(self._opacity)
        row = QHBoxLayout(); row.addWidget(self.sl_opacity, 1); row.addWidget(self.lbl_opacity)
        f.addRow("Opacity", row)
        l1.addLayout(f)

        c2, l2 = card()
        l2.addWidget(section("Pad shape"))
        f2 = form()
        self.sp_cw = QSpinBox(); self.sp_cw.setRange(20, 400); self.sp_cw.setValue(self.cfg["cell_w"])
        self.sp_ch = QSpinBox(); self.sp_ch.setRange(20, 400); self.sp_ch.setValue(self.cfg["cell_h"])
        self.sp_gap = QSpinBox(); self.sp_gap.setRange(0, 100); self.sp_gap.setValue(self.cfg["gap"])
        for sp, key in ((self.sp_cw, "cell_w"), (self.sp_ch, "cell_h"), (self.sp_gap, "gap")):
            sp.valueChanged.connect(lambda val, k=key: self._set(k, val))
        f2.addRow("Width", stepper(self.sp_cw))
        f2.addRow("Height", stepper(self.sp_ch))
        f2.addRow("Gap", stepper(self.sp_gap))
        l2.addLayout(f2)

        c3, l3 = card()
        l3.addWidget(section("Hotkeys"))
        l3.addWidget(muted("Always pressed together with Ctrl + Alt."))
        f3 = form()
        for name, text in (("toggle", "Show / hide"), ("settings", "Open settings"), ("quit", "Quit")):
            le = QLineEdit(self.cfg["hotkeys"].get(name, ""))
            le.setFixedWidth(90)
            le.setAlignment(Qt.AlignmentFlag.AlignCenter)
            le.editingFinished.connect(lambda le=le, n=name: self._hotkey(n, le))
            f3.addRow(text, le)
        l3.addLayout(f3)
        return self._page(c1, c2, c3)

    def _keys_page(self):
        c1, l1 = card()
        l1.addWidget(section("Pads"))
        l1.addWidget(muted("Label is the text on the pad (a key name, or a macro name). Input is what lights it: "
                           "a key (F5), several keys for a macro (F5, F6), a chord (Ctrl+Shift+K) or a controller "
                           "button (gp:a). Leave Input empty to use the label. Col / Row / W / H place and size it."))
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Label", "Input", "Col", "Row", "W", "H"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in (2, 3, 4, 5):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(c, 56)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(260)
        self.table.itemChanged.connect(self._table_edited)
        l1.addWidget(self.table)
        row = QHBoxLayout()
        self.btn_capture = QPushButton("Capture key for selected pad")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setToolTip("Select a row, click this, then press the Cyborg button.")
        self.btn_capture.toggled.connect(self._toggle_capture)
        btn_add = QPushButton("Add pad")
        btn_add.clicked.connect(self._add_pad)
        btn_del = QPushButton("Remove")
        btn_del.setObjectName("quiet")
        btn_del.clicked.connect(self._remove_pad)
        row.addWidget(self.btn_capture, 1)
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        l1.addLayout(row)

        c2, l2 = card()
        l2.addWidget(section("Sticks & d-pads"))
        l2.addWidget(muted("Directions take a key name (W) or controller input (gp:dpup). "
                           "Axes (gp:leftx, gp:lefty) move the knob; Click lights it."))
        self.stick_table = QTableWidget(0, 9)
        self.stick_table.setHorizontalHeaderLabels(["Label", "Up", "Down", "Left", "Right", "Col", "Row", "W", "H"])
        sh = self.stick_table.horizontalHeader()
        sh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 9):
            sh.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.stick_table.setColumnWidth(c, 62 if c < 5 else 48)
        self.stick_table.verticalHeader().setVisible(False)
        self.stick_table.setShowGrid(False)
        self.stick_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.stick_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.stick_table.setMaximumHeight(140)
        self.stick_table.itemChanged.connect(self._stick_edited)
        l2.addWidget(self.stick_table)
        srow = QHBoxLayout()
        b_add_keys = QPushButton("Add WASD stick")
        b_add_keys.clicked.connect(lambda: self._add_stick("keys"))
        b_add_analog = QPushButton("Add analog stick")
        b_add_analog.clicked.connect(lambda: self._add_stick("analog"))
        b_add_dpad = QPushButton("Add d-pad")
        b_add_dpad.clicked.connect(lambda: self._add_stick("dpad"))
        b_del = QPushButton("Remove")
        b_del.setObjectName("quiet")
        b_del.clicked.connect(self._remove_stick)
        for b in (b_add_keys, b_add_analog, b_add_dpad):
            srow.addWidget(b)
        srow.addStretch(1)
        srow.addWidget(b_del)
        l2.addLayout(srow)
        self.joy_edits = {}  # kept for older callers; sticks are edited in the table now
        self._fill_sticks()
        self._fill_table()
        return self._page(c1, c2)

    def _appearance_page(self):
        c0, l0 = card()
        l0.addWidget(section("Preview"))
        self.preview = PadPreview(self.cfg)
        l0.addWidget(self.preview)

        c1, l1 = card()
        l1.addWidget(section("Key text"))
        f = form()
        fnt = self.cfg["font"]
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(fnt["family"]))
        self.font_combo.currentFontChanged.connect(lambda ft: self._set_font("family", ft.family()))
        self.sp_font = QSpinBox(); self.sp_font.setRange(4, 72); self.sp_font.setValue(int(fnt["size"]))
        self.sp_font.setSuffix(" pt")
        self.sp_font.valueChanged.connect(lambda v: self._set_font("size", v))
        self.chk_bold = QCheckBox("Bold"); self.chk_bold.setChecked(bool(fnt["bold"]))
        self.chk_bold.toggled.connect(lambda on: self._set_font("bold", on))
        f.addRow("Font", self.font_combo)
        f.addRow("Size", stepper(self.sp_font))
        f.addRow("", self.chk_bold)
        l1.addLayout(f)

        c2, l2 = card()
        l2.addWidget(section("Colors"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        grid.addWidget(muted("Idle"), 0, 1)
        grid.addWidget(muted("Pressed"), 0, 2)
        self.color_buttons = []
        for r, (part, text) in enumerate((("fill", "Fill"), ("outline", "Border"), ("text", "Text")), start=1):
            grid.addWidget(QLabel(text), r, 0)
            for col, state in enumerate(("idle", "pressed"), start=1):
                b = ColorButton(self.cfg, f"{state}_{part}", self._apply)
                self.color_buttons.append(b)
                grid.addWidget(b, r, col)
        grid.setColumnStretch(3, 1)
        l2.addLayout(grid)
        reset = QPushButton("Reset colors")
        reset.setObjectName("quiet")
        reset.clicked.connect(self._reset_colors)
        l2.addWidget(reset, 0, Qt.AlignmentFlag.AlignLeft)
        return self._page(c0, c1, c2)

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
        if hasattr(self, "preview"):
            self.preview.update()
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
        self.btn_move.setText("Done" if on else "Move / resize with mouse")
        if on:
            self.overlay.show()
            self.chk_visible.setChecked(True)

    def _sync_from_overlay(self):
        self._loading = True
        self.sp_x.setValue(self.cfg["x"])
        self.sp_y.setValue(self.cfg["y"])
        self.sp_scale.setValue(self.cfg.get("scale", 1.0))
        self._loading = False
        self._fill_table()
        self._fill_sticks()
        self._schedule_save()

    # keys table
    @staticmethod
    def _input_text(k):
        if k.get("input") is not None:
            return k["input"]
        if "sc" in k:
            return f"sc:{k['sc']:#x}"
        return ""

    @staticmethod
    def _num(v):
        return str(int(v)) if float(v).is_integer() else str(v)

    def _fill_table(self):
        self._loading = True
        self.table.setRowCount(0)
        for k in self.cfg["keys"]:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(k["label"]))
            inp = QTableWidgetItem(self._input_text(k))
            if "sc" in k and k.get("input") is None:
                inp.setForeground(QColor(MUTED))
                inp.setToolTip("Physical key (scancode). Type a key name to override.")
            self.table.setItem(r, 1, inp)
            for c, key in ((2, "col"), (3, "row"), (4, "w"), (5, "h")):
                it = QTableWidgetItem(self._num(k.get(key, 1)))
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
            k["label"] = text
        elif c == 1:
            if text.lower().startswith("sc:"):
                try:
                    k["sc"] = int(text[3:], 0)
                    k.pop("input", None)
                except ValueError:
                    self._revert(item, self._input_text(k), "Scancode must be a number, e.g. sc:0x1e")
                    return
            else:
                try:
                    parse_input(text)
                except ValueError as e:
                    self._revert(item, self._input_text(k), str(e))
                    return
                k.pop("sc", None)
                if text:
                    k["input"] = text
                else:
                    k.pop("input", None)
        else:
            field = {2: "col", 3: "row", 4: "w", 5: "h"}[c]
            try:
                val = float(text)
                if field in ("w", "h") and val <= 0:
                    raise ValueError
                k[field] = int(val) if val.is_integer() else round(val, 3)
            except ValueError:
                self._revert(item, self._num(k.get(field, 1)), "Enter a number")
                return
        self._apply()

    def _revert(self, item, text, msg):
        self._loading = True
        item.setText(text)
        self._loading = False
        self._flash(msg)

    def _add_pad(self):
        used = {(k["col"], k["row"]) for k in self.cfg["keys"]}
        col = row = 0
        while (col, row) in used:
            col += 1
            if col > 12:
                col, row = 0, row + 1
        self.cfg["keys"].append({"label": "", "col": col, "row": row, "w": 1, "h": 1})
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

    def _on_key_captured(self, token):
        self.btn_capture.setChecked(False)
        r = self.table.currentRow()
        name = token if is_gamepad_input(token) else label_for_token(token)
        if name is None or r < 0:
            self._flash(f"Unknown key ({token})")
            return
        k = self.cfg["keys"][r]
        old_input = k.get("input", k.get("label", ""))
        k.pop("sc", None)
        k["input"] = name
        if not k.get("label") or k.get("label") == old_input:
            k["label"] = GAMEPAD_LABELS.get(name, name)
        self._fill_table()
        self.table.selectRow(r)
        self._flash(f"Pad input set to {name}")
        self._apply()

    STICK_COLS = ("label", "up", "down", "left", "right", "col", "row", "w", "h")

    def _fill_sticks(self):
        self._loading = True
        self.stick_table.setRowCount(0)
        for st in self.cfg.get("sticks", []):
            r = self.stick_table.rowCount()
            self.stick_table.insertRow(r)
            for c, key in enumerate(self.STICK_COLS):
                val = st.get(key, "")
                it = QTableWidgetItem(self._num(val) if isinstance(val, (int, float)) else str(val))
                if c >= 1:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.stick_table.setItem(r, c, it)
        self._loading = False

    def _stick_edited(self, item):
        if self._loading:
            return
        r, c = item.row(), item.column()
        st = self.cfg["sticks"][r]
        key = self.STICK_COLS[c]
        text = item.text().strip()
        if key == "label":
            st["label"] = text
        elif key in ("up", "down", "left", "right"):
            try:
                parse_input(text)
            except ValueError as e:
                self._revert(item, st.get(key, ""), str(e))
                return
            if text:
                st[key] = text
            else:
                st.pop(key, None)
        else:
            try:
                val = float(text)
                if key in ("w", "h") and val <= 0:
                    raise ValueError
                st[key] = int(val) if val.is_integer() else round(val, 3)
            except ValueError:
                self._revert(item, self._num(st.get(key, 2)), "Enter a number")
                return
        self._apply()

    def _add_stick(self, kind):
        base = {"label": "", "col": 0, "row": 0, "w": 2, "h": 2}
        if kind == "keys":
            base.update(label="WASD", up="W", down="S", left="A", right="D")
        elif kind == "analog":
            base.update(label="L", axes=["gp:leftx", "gp:lefty"], click="gp:leftstick")
        else:
            base.update(up="gp:dpup", down="gp:dpdown", left="gp:dpleft", right="gp:dpright")
        self.cfg.setdefault("sticks", []).append(base)
        self._fill_sticks()
        self._apply()

    def _remove_stick(self):
        r = self.stick_table.currentRow()
        if r < 0:
            return
        del self.cfg["sticks"][r]
        self._fill_sticks()
        self._apply()

    def _set_font(self, key, val):
        if self._loading:
            return
        self.cfg["font"][key] = val
        self._apply()

    def _reset_colors(self):
        self.cfg["colors"].update(DEFAULT_COLORS)
        for b in self.color_buttons:
            b.refresh()
        self._apply()

    # ---- layout profiles ----------------------------------------------
    def _new_from_template(self):
        dlg = TemplateDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = dlg.name.text().strip() or dlg.device.currentText()
        prof = dlg.result_profile()
        prof["colors"] = dict(self.cfg["colors"])  # keep the user's colours
        prof["x"], prof["y"], prof["opacity"] = self.cfg["x"], self.cfg["y"], self.cfg.get("opacity", 0.85)
        migrate(prof)
        try:
            save_profile(name, prof)
        except (OSError, ValueError) as e:
            self._flash(f"Could not save: {e}")
            return
        for k in PROFILE_KEYS:
            if k in prof:
                self.cfg[k] = prof[k]
        self.cfg["profile"] = name
        self._refresh_profiles()
        self._rebuild_tabs()
        self._apply()
        self._flash(f"Created layout '{name}'")

    def _refresh_profiles(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("Unsaved layout")
        for name in list_profiles():
            self.profile_combo.addItem(name)
        current = self.cfg.get("profile", "")
        i = self.profile_combo.findText(current) if current else 0
        self.profile_combo.setCurrentIndex(max(0, i))
        self.profile_combo.blockSignals(False)

    def _profile_selected(self, index):
        if index == 0:
            return
        self.profile_combo.setCurrentIndex(index)
        name = self.profile_combo.itemText(index)
        try:
            data = load_profile(name)
        except (OSError, ValueError) as e:
            self._flash(f"Could not load: {e}")
            return
        for k in PROFILE_KEYS:
            if k in data:
                self.cfg[k] = data[k]
        self.cfg["profile"] = name
        self._rebuild_tabs()
        self._apply()
        self._flash(f"Loaded layout '{name}'")

    def _profile_save(self):
        if self.profile_combo.currentIndex() == 0:
            self._profile_save_as()
            return
        name = self.profile_combo.currentText()
        save_profile(name, self.cfg)
        self.cfg["profile"] = name
        self._schedule_save()
        self._flash(f"Saved layout '{name}'")

    def _profile_save_as(self):
        name, ok = QInputDialog.getText(self, "Save layout", "Layout name:",
                                        text=self.cfg.get("profile", ""))
        name = name.strip()
        if not ok or not name:
            return
        try:
            save_profile(name, self.cfg)
        except (OSError, ValueError) as e:
            self._flash(f"Could not save: {e}")
            return
        self.cfg["profile"] = name
        self._refresh_profiles()
        self._schedule_save()
        self._flash(f"Saved layout '{name}'")

    def _profile_delete(self):
        if self.profile_combo.currentIndex() == 0:
            return
        name = self.profile_combo.currentText()
        if QMessageBox.question(self, "Delete layout", f"Delete layout '{name}'?") != QMessageBox.StandardButton.Yes:
            return
        delete_profile(name)
        if self.cfg.get("profile") == name:
            self.cfg["profile"] = ""
        self._refresh_profiles()
        self._schedule_save()
        self._flash(f"Deleted layout '{name}'")

    # ---- save ---------------------------------------------------------
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

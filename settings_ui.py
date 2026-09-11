"""Settings window for the overlay. Every edit applies live and autosaves."""

import os
import tempfile

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPalette, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox,
    QFontComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QScrollArea,
    QSlider, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from overlay import (DEFAULT_COLORS, PROFILE_KEYS, delete_profile, label_for_vk, list_profiles,
                     load_profile, save_config, save_profile, vks_for_label)

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


# ---- the window ------------------------------------------------------------
class SettingsWindow(QWidget):
    PAGES = ("Layout", "Keys", "Appearance")

    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.cfg = overlay.cfg
        self.setWindowTitle("az-overlay")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setPalette(dark_palette())
        self.setStyleSheet(style())
        self.resize(720, 640)
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
        brand = QLabel("az-overlay")
        brand.setObjectName("brand")
        h.addWidget(brand)
        h.addStretch(1)
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
        l1.addWidget(muted("Label is what the Cyborg sends for that pad (Q, 9, Alt, Page Up, F1…). "
                           "Empty label hides the pad. Col / Row place it on the grid."))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Label", "Col", "Row"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
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
        l2.addWidget(section("Thumbstick"))
        j = self.cfg.setdefault("joystick", {"col": 6, "row": 3, "cols": 2, "rows": 2,
                                             "up": "W", "left": "A", "down": "S", "right": "D"})
        self.chk_joy = QCheckBox("Show thumbstick (keyboard mode)")
        self.chk_joy.setChecked(j.get("enabled", True))
        self.chk_joy.toggled.connect(lambda on: self._set_joy("enabled", on))
        l2.addWidget(self.chk_joy)
        keys_row = QGridLayout()
        keys_row.setHorizontalSpacing(8)
        keys_row.setVerticalSpacing(8)
        self.joy_edits = {}
        for i, (name, text) in enumerate((("up", "Up"), ("down", "Down"), ("left", "Left"), ("right", "Right"))):
            le = QLineEdit(j.get(name, ""))
            le.setFixedWidth(64)
            le.setAlignment(Qt.AlignmentFlag.AlignCenter)
            le.editingFinished.connect(lambda le=le, n=name: self._joy_label(n, le))
            self.joy_edits[name] = le
            lbl = QLabel(text)
            lbl.setObjectName("muted")
            lbl.setFixedWidth(44)
            keys_row.addWidget(lbl, i // 2, (i % 2) * 2)
            keys_row.addWidget(le, i // 2, (i % 2) * 2 + 1)
        keys_row.setColumnStretch(4, 1)
        pos_row = QHBoxLayout()
        pos_row.setSpacing(8)
        for name, text in (("col", "Col"), ("row", "Row")):
            sp = QSpinBox(); sp.setRange(0, 40); sp.setValue(j.get(name, 0)); sp.setFixedWidth(64)
            sp.valueChanged.connect(lambda val, n=name: self._set_joy(n, val))
            lbl = QLabel(text)
            lbl.setObjectName("muted")
            lbl.setFixedWidth(44)
            pos_row.addWidget(lbl)
            pos_row.addWidget(stepper(sp))
            pos_row.addSpacing(8)
        pos_row.addStretch(1)
        f4 = form()
        f4.addRow("Keys", keys_row)
        f4.addRow("Position", pos_row)
        l2.addLayout(f4)
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
        for name, le in self.joy_edits.items():
            le.setText(self.cfg["joystick"].get(name, ""))
        self._loading = False
        self._fill_table()
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
            field = "col" if c == 1 else "row"
            try:
                k[field] = max(0, int(text))
            except ValueError:
                self._loading = True
                item.setText(str(k[field]))
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
        self.cfg["colors"].update(DEFAULT_COLORS)
        for b in self.color_buttons:
            b.refresh()
        self._apply()

    # ---- layout profiles ----------------------------------------------
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

"""Settings window for the overlay. Edits apply live; named layouts autosave."""

import os
import tempfile
from math import ceil

from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, QUrl, QUrlQuery, Property, Signal
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QFont, QIcon, QLinearGradient, QPainter, QPalette, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QBoxLayout, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFontComboBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QMenu, QPushButton, QScrollArea, QSlider, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import templates
from gamepad import is_gamepad_input
from overlay import (APP_NAME, DEFAULT_COLORS, GAMEPAD_LABELS, PROFILE_KEYS, delete_profile,
                     KEY_TEXT_FLAGS, fit_key_font, key_text_rect,
                     label_for_token, list_profiles, load_profile, migrate, pad_inputs, parse_input,
                     save_config, save_profile, vks_for_label)

SUPPORT_EMAIL = "andres6perez@gmail.com"
# Set these to the creator's payment links to enable donations.
PAYPAL_DONATION_URL = ""
VENMO_DONATION_URL = "https://venmo.com/andrespc93"

# Theme colors belong to the editor; overlay colors remain part of each layout.
THEMES = {
    "dark": {
        "bg": "#000000", "card": "#161616", "field": "#242424",
        "line": "#333333", "text": "#f5f5f7", "muted": "#a1a1a6",
        "accent": "#b6ff00", "accent_text": "#101600", "accent_hover": "#ceff59",
        "hover": "#303030", "pressed": "#3c3c3c", "strong_line": "#6a6a6a",
        "disabled": "#757575", "badge_bg": "#253314", "badge_line": "#253314",
        "badge_text": "#b6ff00", "selection": "#253314", "sidebar": "#0b0b0b",
        "preview": "#121212", "preview_end": "#1f1f1f",
    },
    "light": {
        "bg": "#f2f2f7", "card": "#ffffff", "field": "#f0f0f5",
        "line": "#e3e3eb", "text": "#1c1c1e", "muted": "#6c6c76",
        "accent": "#416800", "accent_text": "#ffffff", "accent_hover": "#325100",
        "hover": "#e8e8f0", "pressed": "#dddde7", "strong_line": "#aaaab5",
        "disabled": "#90909a", "badge_bg": "#e8f7ed", "badge_line": "#e8f7ed",
        "badge_text": "#416800", "selection": "#e6f3cf", "sidebar": "#eaeaF1",
        "preview": "#f5f8f0", "preview_end": "#eaf0df",
    },
}


def theme_colors(cfg):
    return THEMES["light" if cfg.get("theme") == "light" else "dark"]


def theme_palette(theme="dark"):
    """Give native Fusion controls and dialogs the same colors as the stylesheet."""
    t = THEMES[theme]
    pal = QPalette()
    for role, key in (
        (QPalette.ColorRole.Window, "bg"), (QPalette.ColorRole.WindowText, "text"),
        (QPalette.ColorRole.Base, "field"), (QPalette.ColorRole.AlternateBase, "card"),
        (QPalette.ColorRole.Text, "text"), (QPalette.ColorRole.Button, "field"),
        (QPalette.ColorRole.ButtonText, "text"), (QPalette.ColorRole.Highlight, "accent"),
        (QPalette.ColorRole.HighlightedText, "accent_text"), (QPalette.ColorRole.ToolTipBase, "card"),
        (QPalette.ColorRole.ToolTipText, "text"), (QPalette.ColorRole.PlaceholderText, "muted"),
        (QPalette.ColorRole.Light, "card"), (QPalette.ColorRole.Midlight, "field"),
        (QPalette.ColorRole.Mid, "strong_line"), (QPalette.ColorRole.Dark, "line"),
        (QPalette.ColorRole.Shadow, "strong_line"),
    ):
        pal.setColor(role, QColor(t[key]))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor(t["disabled"]))
    return pal


def _arrow_icon(color):
    """Qt stylesheets can't draw arrows in a chosen color; ship a tiny PNG instead."""
    path = os.path.join(tempfile.gettempdir(), f"az-overlay-arrow-{color.lstrip('#')}.png")
    if not os.path.exists(path):
        pm = QPixmap(20, 20)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(color))
        p.drawPolygon(QPolygonF([QPointF(4, 7), QPointF(16, 7), QPointF(10, 13)]))
        p.end()
        pm.save(path)
    return path.replace("\\", "/")


def style(theme="dark"):
    """Stylesheet, built at runtime (needs a QApplication for the arrow icon)."""
    t = THEMES[theme]
    ARROW = _arrow_icon(t["text"])
    return f"""
QWidget {{ background: {t["bg"]}; color: {t["text"]}; font-family: 'Segoe UI'; font-size: 10pt; }}
QLabel, QCheckBox, QWidget#inline {{ background: transparent; }}
QLabel#muted {{ color: {t["muted"]}; }}
QLabel#section {{ color: {t["muted"]}; font-size: 8pt; font-weight: 600; letter-spacing: 1.2px; }}
QLabel#pageTitle {{ font-size: 27pt; font-weight: 700; letter-spacing: -1px; }}
QLabel#badge {{ color: {t["badge_text"]}; background: {t["badge_bg"]}; border-radius: 11px; padding: 5px 11px; font-size: 8pt; font-weight: 600; }}
QLabel#value {{ color: {t["accent"]}; background: {t["selection"]}; border-radius: 8px; padding: 4px 8px; font-weight: 600; }}
QFrame#header, QFrame#footer {{ background: {t["card"]}; }}
QFrame#header {{ border-bottom: 1px solid {t["line"]}; }}
QFrame#footer {{ border-top: 1px solid {t["line"]}; }}
QFrame#card {{ background: {t["card"]}; border: 1px solid {t["line"]}; border-radius: 18px; }}
QFrame#helpContact {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t["selection"]}, stop:1 {t["card"]}); border: 1px solid {t["badge_text"]}; border-radius: 18px; }}
QLabel#helpTitle {{ font-size: 20pt; font-weight: 700; letter-spacing: -0.5px; }}
QLabel#helpStepTitle {{ font-size: 11pt; font-weight: 600; }}
QLabel#helpNumber {{ color: {t["accent"]}; background: {t["selection"]}; border-radius: 12px; font-size: 11pt; font-weight: 700; }}
QWidget#sidebar {{ background: {t["sidebar"]}; border-right: 1px solid {t["line"]}; }}
QListWidget#nav {{ background: transparent; border: none; outline: 0; }}
QListWidget#nav::item {{ padding: 10px; margin: 3px 0; border-radius: 10px; color: {t["muted"]}; }}
QListWidget#nav::item:hover {{ background: {t["hover"]}; color: {t["text"]}; }}
QListWidget#nav::item:selected {{ background: {t["selection"]}; color: {t["accent"]}; font-weight: 600; }}
QScrollArea {{ border: none; }}
QPushButton {{ background: {t["field"]}; border: 1px solid transparent; border-radius: 10px; padding: 8px 15px; font-weight: 600; }}
QPushButton:hover {{ background: {t["hover"]}; }}
QPushButton:pressed {{ background: {t["pressed"]}; }}
QPushButton:focus {{ border-color: {t["accent"]}; }}
QPushButton:disabled {{ color: {t["disabled"]}; background: {t["field"]}; }}
QPushButton:checked {{ background: {t["selection"]}; color: {t["accent"]}; }}
QPushButton#primary {{ background: {t["accent"]}; color: {t["accent_text"]}; }}
QPushButton#primary:hover {{ background: {t["accent_hover"]}; }}
QPushButton#primary:pressed {{ background: {t["accent_hover"]}; border-color: {t["accent_text"]}; }}
QPushButton#primary:disabled {{ background: {t["field"]}; color: {t["disabled"]}; }}
QPushButton#quiet {{ background: transparent; color: {t["accent"]}; font-weight: 400; }}
QPushButton#quiet:hover {{ background: {t["selection"]}; }}
QPushButton#quiet:disabled {{ color: {t["disabled"]}; }}
QPushButton#disclosure {{ text-align: left; background: {t["card"]}; border: 1px solid {t["line"]}; border-radius: 12px; color: {t["text"]}; padding: 12px 16px; font-weight: 400; }}
QPushButton#disclosure:hover {{ background: {t["hover"]}; }}
QPushButton#disclosure:checked {{ color: {t["accent"]}; }}
QPushButton#disclosure:focus {{ border-color: {t["accent"]}; }}
QMenu {{ background: {t["card"]}; border: 1px solid {t["line"]}; border-radius: 12px; padding: 6px; }}
QMenu::item {{ padding: 10px 20px; border-radius: 7px; }}
QMenu::item:selected {{ background: {t["selection"]}; color: {t["accent"]}; }}
QMenu::item:disabled {{ color: {t["disabled"]}; }}
QPushButton#step {{ color: {t["accent"]}; font-size: 15pt; font-weight: 400; padding: 0; min-width: 36px; max-width: 36px; min-height: 34px; max-height: 34px; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QFontComboBox {{
    background: {t["field"]}; border: 1px solid transparent; border-radius: 9px; padding: 7px 10px; min-height: 20px; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {t["accent"]}; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: {t["disabled"]}; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ border: none; width: 26px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url({ARROW}); width: 10px; height: 10px; }}
QLineEdit, QSpinBox, QDoubleSpinBox {{ selection-background-color: {t["accent"]}; selection-color: {t["accent_text"]}; }}
QComboBox QAbstractItemView {{ background: {t["card"]}; border: 1px solid {t["line"]}; selection-background-color: {t["selection"]}; selection-color: {t["text"]}; padding: 5px; outline: none; }}
QTableWidget {{ background: {t["card"]}; alternate-background-color: {t["field"]}; gridline-color: {t["line"]}; border: none; selection-background-color: {t["selection"]}; selection-color: {t["text"]}; outline: none; }}
QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {t["line"]}; }}
QTableWidget::item:selected {{ background: {t["selection"]}; color: {t["text"]}; }}
QHeaderView::section {{ background: {t["card"]}; color: {t["muted"]}; padding: 8px; border: none; border-bottom: 1px solid {t["line"]}; font-size: 8pt; font-weight: 600; }}
QSlider {{ min-height: 32px; background: transparent; }}
QSlider::groove:horizontal {{ height: 5px; background: {t["line"]}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t["accent"]}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 23px; margin: -10px 0; background: #ffffff; border: 1px solid {t["line"]}; border-radius: 12px; }}
QSlider::handle:horizontal:hover, QSlider::handle:horizontal:focus {{ border-color: {t["accent"]}; }}
QToolTip {{ background: {t["card"]}; color: {t["text"]}; border: 1px solid {t["line"]}; padding: 6px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 0; }}
QScrollBar::handle:vertical {{ background: {t["line"]}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t["strong_line"]}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

"""



# ---- small building blocks ------------------------------------------------
def navigation_icon(name, theme="dark"):
    """Small, resolution-independent tiles drawn with the app's own glyphs."""
    pm = QPixmap(96, 96)
    pm.setDevicePixelRatio(3)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    t = THEMES[theme]
    accent = QColor(t["accent"])
    p.setPen(Qt.PenStyle.NoPen)
    gradient = QLinearGradient(0, 0, 32, 32)
    gradient.setColorAt(0, accent.lighter(115))
    gradient.setColorAt(1, accent)
    p.setBrush(gradient)
    p.drawRoundedRect(QRectF(0, 0, 32, 32), 8, 8)
    p.setPen(QPen(QColor(t["accent_text"]), 1.6))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if name == "Layout":
        p.drawRoundedRect(QRectF(7, 7, 18, 18), 3, 3)
        p.drawLine(QPointF(13, 7), QPointF(13, 25))
        p.drawLine(QPointF(13, 15), QPointF(25, 15))
    elif name == "Keys":
        for x in (7, 14, 21):
            for y in (9, 16):
                p.drawRoundedRect(QRectF(x, y, 4, 4), 1, 1)
        p.drawLine(QPointF(11, 24), QPointF(21, 24))
    elif name == "Appearance":
        for x, y in ((12, 12), (20, 12), (16, 20)):
            p.drawEllipse(QPointF(x, y), 5, 5)
    elif name in ("About", "Help"):
        p.drawEllipse(QRectF(6, 6, 20, 20))
        glyph_font = QFont("Segoe UI", 14)
        glyph_font.setPixelSize(18)
        glyph_font.setBold(True)
        p.setFont(glyph_font)
        p.drawText(QRectF(6, 5, 20, 21), Qt.AlignmentFlag.AlignCenter,
                   "i" if name == "About" else "?")
    p.end()
    icon = QIcon(pm)
    icon.addPixmap(pm, QIcon.Mode.Selected)
    icon.addPixmap(pm, QIcon.Mode.Active)
    return icon


class Switch(QCheckBox):
    """An animated switch with native checkbox keyboard and accessibility behavior."""

    def __init__(self, text):
        super().__init__(text)
        self._position = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.animation = QPropertyAnimation(self, b"position", self)
        self.animation.setDuration(160)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def _get_position(self):
        return self._position

    def _set_position(self, value):
        self._position = value
        self.update()

    position = Property(float, _get_position, _set_position)

    def setChecked(self, checked):
        super().setChecked(checked)
        if self.signalsBlocked():
            self.animation.stop()
            self.position = float(checked)

    def _animate(self, checked):
        self.animation.stop()
        if not self.isVisible():
            self.position = float(checked)
            return
        self.animation.setStartValue(self._position)
        self.animation.setEndValue(float(checked))
        self.animation.start()

    def sizeHint(self):
        return QSize(56 + self.fontMetrics().horizontalAdvance(self.text().replace("&&", "&")), 32)

    def minimumSizeHint(self):
        return self.sizeHint()

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = theme_colors(getattr(self.window(), "cfg", {}))
        off = QColor(colors["strong_line"])
        on = QColor(colors["accent"])
        t = self._position
        track_color = QColor(*(round(a + (b - a) * t) for a, b in zip(off.getRgb()[:3], on.getRgb()[:3])))
        if not self.isEnabled():
            p.setOpacity(0.45)
        track = QRectF(2, (self.height() - 24) / 2, 42, 24)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track, 12, 12)
        p.setBrush(QColor(colors["accent_text"]))
        p.drawEllipse(QRectF(track.x() + 2 + 18 * t, track.y() + 2, 20, 20))
        if self.hasFocus():
            p.setPen(QPen(self.palette().color(QPalette.ColorRole.Highlight), 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(track.adjusted(-2, -2, 2, 2), 14, 14)
        p.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        p.setFont(self.font())
        p.drawText(QRectF(56, 0, max(0, self.width() - 56), self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   self.text().replace("&&", "&"))
        p.end()


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
    lay.setContentsMargins(22, 18, 22, 18)
    lay.setSpacing(14)
    return f, lay


def form():
    f = QFormLayout()
    f.setHorizontalSpacing(16)
    f.setVerticalSpacing(12)
    f.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
    return f


def disclosure(title, content):
    """Keep infrequent controls available without crowding the main workflow."""
    wrapper = QWidget()
    wrapper.setObjectName("inline")
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    title = title.replace("&", "&&")
    button = QPushButton(f"▸  {title}")
    button.setObjectName("disclosure")
    button.setCheckable(True)
    content.setVisible(False)
    def toggle(opened):
        content.setVisible(opened)
        button.setText(f"{'▾' if opened else '▸'}  {title}")
    button.toggled.connect(toggle)
    layout.addWidget(button)
    layout.addWidget(content)
    return wrapper


def stepper(spin):
    """Wrap a spinbox with big - / + buttons (the native arrows are tiny)."""
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
    w = QWidget()
    w.setObjectName("inline")
    w.setMaximumWidth(260)
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
        self.setFixedSize(126, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.pick)
        self.refresh()

    def refresh(self):
        col = QColor(self.cfg["colors"][self.key])
        self.setText(col.name().upper())
        self.setAccessibleName(f"{self.key.replace('_', ' ')} color")
        self.setToolTip(f"Change {self.key.replace('_', ' ')}")
        swatch = QPixmap(40, 40)
        swatch.setDevicePixelRatio(2)
        swatch.fill(Qt.GlobalColor.transparent)
        painter = QPainter(swatch)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(theme_colors(self.cfg)["strong_line"]), 0.5))
        painter.setBrush(col)
        painter.drawEllipse(QRectF(1, 1, 18, 18))
        painter.end()
        self.setIcon(QIcon(swatch))
        self.setIconSize(QSize(20, 20))
        self.setStyleSheet("font-family: Consolas, 'Segoe UI'; font-size: 9pt; font-weight: 400;")

    def pick(self):
        dlg = QColorDialog(QColor(self.cfg["colors"][self.key]), self)
        # The Windows native picker ignores the editor's palette and stylesheet.
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        theme = "light" if self.cfg.get("theme") == "light" else "dark"
        dlg.setWindowTitle(f"Choose {self.key.replace('_', ' ')} color")
        dlg.setPalette(theme_palette(theme))
        buttons = dlg.findChild(QDialogButtonBox)
        if buttons:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primary")
        dlg.setStyleSheet(style(theme))
        dlg.currentColorChanged.connect(self._live)
        start = self.cfg["colors"][self.key]
        if dlg.exec():
            self._live(dlg.selectedColor())
        else:
            self.cfg["colors"][self.key] = start
            self.refresh()
            self.on_change()
        dlg.deleteLater()

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
        self.setFixedHeight(160)

    def paintEvent(self, _e):
        c = {k: QColor(v) for k, v in self.cfg["colors"].items()}
        fnt = self.cfg["font"]
        font = QFont(fnt["family"], int(fnt["size"]),
                     QFont.Weight.Bold if fnt["bold"] else QFont.Weight.Normal)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ratio = min(0.9, (self.width() - 76) / (2 * self.cfg["cell_w"]),
                    (self.height() - 52) / self.cfg["cell_h"])
        w = self.cfg["cell_w"] * ratio
        h = self.cfg["cell_h"] * ratio
        gap = 28
        x0 = (self.width() - (2 * w + gap)) / 2
        y0 = (self.height() - h - 18) / 2
        r = 10
        t = theme_colors(self.cfg)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(t["preview"]))
        gradient.setColorAt(1, QColor(t["preview_end"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(gradient)
        p.drawRoundedRect(QRectF(self.rect()), 14, 14)
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
            text_rect = key_text_rect(rect)
            p.setFont(fit_key_font("Space", font, text_rect, self))
            p.setPen(c[f"{state}_text"])
            p.drawText(text_rect, KEY_TEXT_FLAGS, "Space")
            p.setFont(QFont("Segoe UI", 8))
            p.setPen(QColor(theme_colors(self.cfg)["muted"]))
            p.drawText(QRectF(x, y0 + h + 4, w, 16), Qt.AlignmentFlag.AlignCenter, state)
        p.end()


class PadLayoutEditor(QWidget):
    """Fit the complete layout into a clickable view, including unassigned pads."""

    pad_selected = Signal(int)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.selected = -1
        self.setMinimumHeight(240)
        self.setAccessibleName("All pads layout")
        self.setToolTip("Click any pad to select its mapping below. Blank pads show their pad number.")

    def layout_rects(self):
        gap = self.cfg["gap"]
        cw, ch = self.cfg["cell_w"] + gap, self.cfg["cell_h"] + gap
        keys = self.cfg["keys"]
        entries = keys + self.cfg.get("sticks", [])
        rects = [QRectF(k["col"] * cw, k["row"] * ch,
                        k.get("w", 1 if i < len(keys) else 2) * cw - gap,
                        k.get("h", 1 if i < len(keys) else 2) * ch - gap)
                 for i, k in enumerate(entries)]
        if not rects:
            return []
        bounds = QRectF(rects[0])
        for rect in rects[1:]:
            bounds = bounds.united(rect)
        ratio = min(max(1, self.width() - 24) / max(1, bounds.width()),
                    max(1, self.height() - 24) / max(1, bounds.height()))
        x = (self.width() - bounds.width() * ratio) / 2
        y = (self.height() - bounds.height() * ratio) / 2
        return [QRectF(x + (r.x() - bounds.x()) * ratio,
                       y + (r.y() - bounds.y()) * ratio,
                       r.width() * ratio, r.height() * ratio) for r in rects]

    def paintEvent(self, event):
        t = theme_colors(self.cfg)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(t["preview"]))
        keys = self.cfg["keys"]
        entries = keys + self.cfg.get("sticks", [])
        rects = self.layout_rects()
        for i, (entry, rect) in enumerate(zip(entries, rects)):
            selected = i < len(keys) and i == self.selected
            p.setBrush(QColor(t["selection"] if selected else t["field"]))
            p.setPen(QPen(QColor(t["accent"] if selected else t["strong_line"]), 2 if selected else 1))
            circle = i >= len(keys) or entry.get("shape", self.cfg.get("shape")) in ("circle", "dot")
            if circle:
                p.drawEllipse(rect)
            else:
                p.drawRoundedRect(rect, 5, 5)
            label = entry.get("label") or (f"#{i + 1}" if i < len(keys) else "Stick")
            text_rect = key_text_rect(rect, "circle" if circle else "rect")
            p.setFont(fit_key_font(label, QFont("Segoe UI", 10), text_rect, self))
            p.setPen(QColor(t["accent"] if selected else t["text"]))
            p.drawText(text_rect, KEY_TEXT_FLAGS, label)
        if not rects:
            p.setPen(QColor(t["muted"]))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Add a pad, row, or column to start.")
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            rects = self.layout_rects()[:len(self.cfg["keys"])]
            for i in reversed(range(len(rects))):
                if rects[i].contains(event.position()):
                    self.pad_selected.emit(i)
                    event.accept()
                    return
        super().mousePressEvent(event)


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
    PAGES = ("Layout", "Keys", "Appearance", "About", "Help")

    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.cfg = overlay.cfg
        self.setWindowTitle(APP_NAME)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        theme = "light" if self.cfg.get("theme") == "light" else "dark"
        self.setPalette(theme_palette(theme))
        self.setStyleSheet(style(theme))
        self.resize(1040, 860)
        self.setMinimumSize(820, 580)
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
        self.nav.setIconSize(QSize(28, 28))
        self.nav.setSpacing(2)
        self.nav.setAccessibleName("Settings pages")
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for name in self.PAGES:
            QListWidgetItem(navigation_icon(name, theme), name, self.nav)
        self.stack = QStackedWidget()
        self.nav.currentRowChanged.connect(self._page_changed)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(184)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 28, 12, 20)
        sidebar_layout.setSpacing(12)
        sidebar_layout.addWidget(section("Workspace"))
        sidebar_layout.addWidget(self.nav, 1)
        body.addWidget(sidebar)
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
        header = QVBoxLayout(f)
        header.setContentsMargins(26, 20, 26, 18)
        header.setSpacing(18)
        title = QHBoxLayout()
        h = QHBoxLayout()
        h.setSpacing(10)
        tagline = muted("Every move. On display.")
        tagline.setWordWrap(False)
        title.addWidget(tagline)
        title.addStretch(1)
        theme_label = QLabel("Theme")
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.setCurrentIndex(1 if self.cfg.get("theme") == "light" else 0)
        self.theme_combo.setMinimumWidth(100)
        self.theme_combo.setAccessibleName("App theme")
        self.theme_combo.setToolTip("Choose the settings window's appearance")
        theme_label.setBuddy(self.theme_combo)
        self.theme_combo.currentIndexChanged.connect(self._theme_changed)
        title.addWidget(theme_label)
        title.addWidget(self.theme_combo)
        header.addLayout(title)
        header.addLayout(h)
        b_tpl = QPushButton("+ New layout")
        b_tpl.setToolTip("Create a layout from a template: Azeron, keyboards, Xbox, PlayStation")
        b_tpl.clicked.connect(self._new_from_template)
        h.addWidget(muted("Layout"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(200)
        self.profile_combo.activated.connect(self._profile_selected)
        self.profile_combo.setAccessibleName("Saved layout")
        h.addWidget(self.profile_combo, 1)
        b_save = QPushButton("Save layout")
        b_save.setToolTip("Save an unnamed layout. Changes to saved layouts are saved automatically.")
        b_save.clicked.connect(self._profile_save)
        more = QPushButton("More")
        more.setObjectName("quiet")
        more.setAccessibleName("Layout options")
        menu = QMenu(more)
        menu.addAction("Save as new layout…", self._profile_save_as)
        self.delete_layout_action = menu.addAction("Delete saved layout…", self._profile_delete)
        more.setMenu(menu)
        h.addWidget(b_save)
        h.addWidget(more)
        h.addSpacing(8)
        b_tpl.setObjectName("primary")
        h.addWidget(b_tpl)
        self._refresh_profiles()
        return f

    def _footer(self):
        f = QFrame()
        f.setObjectName("footer")
        h = QHBoxLayout(f)
        h.setContentsMargins(20, 10, 20, 10)
        h.addStretch(1)
        self.chk_visible = Switch("Overlay visible")
        self.chk_visible.setChecked(self.overlay.isVisible())
        self.chk_visible.toggled.connect(self.overlay.setVisible)
        h.addWidget(self.chk_visible)
        quit_btn = QPushButton("Quit overlay")
        quit_btn.setObjectName("quiet")
        quit_btn.clicked.connect(self.overlay.shutdown)
        h.addWidget(quit_btn)
        return f

    def _page(self, title, description, *cards):
        """Scrollable page holding a column of cards."""
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(28, 24, 28, 24)
        v.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        v.addWidget(heading)
        v.addWidget(muted(description))
        v.addSpacing(4)
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
        self.stack.addWidget(self._about_page())
        self.stack.addWidget(self._help_page())
        self._adapt_appearance_columns()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "appearance_columns"):
            self._adapt_appearance_columns()

    def _adapt_appearance_columns(self):
        self.appearance_columns.setDirection(
            QBoxLayout.Direction.LeftToRight if self.width() >= 1000
            else QBoxLayout.Direction.TopToBottom)

    def _page_changed(self, index):
        self.stack.setCurrentIndex(index)
        if index != 1 and hasattr(self, "btn_capture"):
            self.btn_capture.setChecked(False)

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
        l1.addWidget(section("Position your overlay"))
        self.btn_move = QPushButton("Edit on screen")
        self.btn_move.setObjectName("primary")
        self.btn_move.setCheckable(True)
        self.btn_move.setMinimumHeight(38)
        self.btn_move.setMinimumWidth(156)
        self.btn_move.toggled.connect(self._toggle_move)
        l1.addWidget(self.btn_move, 0, Qt.AlignmentFlag.AlignLeft)
        self.move_help = muted("Drag to reposition. Scroll to resize. Choose Done editing when you’re finished.")
        l1.addWidget(self.move_help)
        f = form()
        self.sp_x = QSpinBox(); self.sp_x.setRange(-10000, 10000)
        self.sp_y = QSpinBox(); self.sp_y.setRange(-10000, 10000)
        self.sp_scale = QDoubleSpinBox(); self.sp_scale.setRange(0.2, 3.0); self.sp_scale.setSingleStep(0.05); self.sp_scale.setDecimals(2)
        for sp, key in ((self.sp_x, "x"), (self.sp_y, "y")):
            sp.setValue(self.cfg[key])
            sp.valueChanged.connect(lambda val, k=key: self._set(k, val))
        self.sp_scale.setValue(self.cfg.get("scale", 1.0))
        self.sp_scale.valueChanged.connect(lambda val: self._set("scale", round(val, 3)))
        self.sp_x.setSuffix(" px")
        self.sp_y.setSuffix(" px")
        self.sp_scale.setSuffix(" ×")
        self.sl_scale = QSlider(Qt.Orientation.Horizontal)
        self.sl_scale.setRange(20, 300)
        self.sl_scale.setValue(round(self.sp_scale.value() * 100))
        self.sl_scale.setAccessibleName("Overlay size")
        self.lbl_scale = muted(f"{self.sl_scale.value()}%")
        self.lbl_scale.setFixedWidth(68)
        self.lbl_scale.setObjectName("value")
        self.lbl_scale.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sl_scale.valueChanged.connect(lambda value: self.sp_scale.setValue(value / 100))
        self.sp_scale.valueChanged.connect(self._sync_scale)
        scale_row = QHBoxLayout()
        scale_row.addWidget(self.sl_scale, 1)
        scale_row.addWidget(self.lbl_scale)
        f.addRow("Size", scale_row)
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal); self.sl_opacity.setRange(10, 100)
        self.sl_opacity.setAccessibleName("Overlay opacity")
        self.sl_opacity.setValue(int(self.cfg.get("opacity", 0.85) * 100))
        self.lbl_opacity = muted(f"{self.sl_opacity.value()}%")
        self.lbl_opacity.setFixedWidth(68)
        self.lbl_opacity.setObjectName("value")
        self.lbl_opacity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sl_opacity.valueChanged.connect(self._opacity)
        row = QHBoxLayout(); row.addWidget(self.sl_opacity, 1); row.addWidget(self.lbl_opacity)
        f.addRow("Opacity", row)
        l1.addLayout(f)
        precise = QWidget()
        precise.setObjectName("inline")
        precise_form = form()
        precise.setLayout(precise_form)
        precise_form.addRow("Horizontal", stepper(self.sp_x))
        precise_form.addRow("Vertical", stepper(self.sp_y))
        precise_form.addRow("Exact scale", stepper(self.sp_scale))
        l1.addWidget(disclosure("Precise position & scale", precise))

        c2, l2 = card()
        l2.addWidget(section("Key dimensions"))
        l2.addWidget(muted("Change the size and spacing of individual keys."))
        f2 = form()
        self.sp_cw = QSpinBox(); self.sp_cw.setRange(20, 400); self.sp_cw.setValue(self.cfg["cell_w"])
        self.sp_ch = QSpinBox(); self.sp_ch.setRange(20, 400); self.sp_ch.setValue(self.cfg["cell_h"])
        self.sp_gap = QSpinBox(); self.sp_gap.setRange(0, 100); self.sp_gap.setValue(self.cfg["gap"])
        for sp, key in ((self.sp_cw, "cell_w"), (self.sp_ch, "cell_h"), (self.sp_gap, "gap")):
            sp.setSuffix(" px")
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
        return self._page("Layout", "Get your overlay in the right place, at the right size.", c1,
                          disclosure("Key dimensions", c2), disclosure("Keyboard shortcuts", c3))

    def _keys_page(self):
        c1, l1 = card()
        l1.addWidget(section("Pads"))
        l1.addWidget(muted("Double-click a cell to edit. Leave Input empty to use the label, "
                           "or select a pad and capture a key or controller button."))
        self.show_all_pads = Switch("Show all pads")
        self.show_all_pads.setToolTip("Show a clickable layout, including blank pads, above the mapping table.")
        l1.addWidget(self.show_all_pads)
        self.pad_layout = PadLayoutEditor(self.cfg)
        self.pad_layout.hide()
        self.pad_layout.pad_selected.connect(self._select_visual_pad)
        self.show_all_pads.toggled.connect(self.pad_layout.setVisible)
        l1.addWidget(self.pad_layout)
        self.table = QTableWidget(0, 6)
        search_row = QHBoxLayout()
        self.key_search = QLineEdit()
        self.key_search.setPlaceholderText("Search by label or input")
        self.key_search.setClearButtonEnabled(True)
        self.key_search.setAccessibleName("Find a pad")
        self.key_search.textChanged.connect(self._filter_keys)
        self.key_count = muted("")
        search_row.addWidget(self.key_search, 1)
        search_row.addWidget(self.key_count)
        l1.addLayout(search_row)
        self.table.setHorizontalHeaderLabels(["Label", "Input", "Col", "Row", "W", "H"])
        for col, hint in enumerate(("Text displayed on the pad", "Key: F5 · Macro: F5, F6 · Chord: Ctrl+Shift+K · Controller: gp:a",
                                    "Horizontal position in key units", "Vertical position in key units",
                                    "Width in key units", "Height in key units")):
            self.table.horizontalHeaderItem(col).setToolTip(hint)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for c in (2, 3, 4, 5):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(c, 56)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(260)
        self.table.itemChanged.connect(self._table_edited)
        row = QHBoxLayout()
        self.btn_capture = QPushButton("Record input")
        self.btn_capture.setObjectName("primary")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setToolTip("Select a pad, then record a key or controller button. Click again to cancel.")
        self.btn_capture.toggled.connect(self._toggle_capture)
        btn_add = QPushButton("Add pad")
        btn_add.clicked.connect(self._add_pad)
        btn_del = self.btn_remove_pad = QPushButton("Remove")
        btn_del.setObjectName("quiet")
        btn_del.clicked.connect(self._remove_pad)
        row.addWidget(self.btn_capture)
        row.addStretch(1)
        row.addWidget(btn_add)
        row.addWidget(btn_del)
        l1.addLayout(row)
        grow_row = QHBoxLayout()
        self.btn_add_row = QPushButton("Add row")
        self.btn_add_row.setToolTip("Add a row of blank pads below the layout, spanning its pad columns.")
        self.btn_add_row.clicked.connect(lambda: self._add_pad_line("row"))
        self.btn_add_column = QPushButton("Add column")
        self.btn_add_column.setToolTip("Add a column of blank pads to the right, spanning its pad rows.")
        self.btn_add_column.clicked.connect(lambda: self._add_pad_line("col"))
        grow_row.addWidget(self.btn_add_row)
        grow_row.addWidget(self.btn_add_column)
        grow_row.addStretch(1)
        l1.addLayout(grow_row)
        self.selection_hint = muted("Select a pad below to record its input.")
        l1.addWidget(self.selection_hint)
        l1.addWidget(self.table)
        self.no_keys = muted("No matching pads. Try another search or add a pad.")
        l1.addWidget(self.no_keys)
        self.show_geometry = Switch("Edit position && size")
        self.show_geometry.setToolTip("Show position and dimensions in key units.")
        self.show_geometry.toggled.connect(self._show_key_geometry)
        l1.addWidget(self.show_geometry)
        self._show_key_geometry(False)
        self.table.itemSelectionChanged.connect(self._pad_selection_changed)

        c2, l2 = card()
        l2.addWidget(section("Sticks & d-pads"))
        l2.addWidget(muted("Add a keyboard stick, analog stick, or d-pad. Double-click a direction to change its input."))
        self.stick_table = QTableWidget(0, 9)
        self.stick_table.setHorizontalHeaderLabels(["Label", "Up", "Down", "Left", "Right", "Col", "Row", "W", "H"])
        sh = self.stick_table.horizontalHeader()
        sh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1, 9):
            sh.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
            self.stick_table.setColumnWidth(c, 62 if c < 5 else 48)
        self.stick_table.verticalHeader().setVisible(False)
        self.stick_table.verticalHeader().setDefaultSectionSize(36)
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
        return self._page("Keys & inputs", "Choose a pad. Record an input. Make it yours.", c1,
                          disclosure("Sticks & d-pads", c2))

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
        self.font_combo.setMinimumWidth(130)
        self.font_combo.setCurrentFont(QFont(fnt["family"]))
        self.font_combo.currentFontChanged.connect(lambda ft: self._set_font("family", ft.family()))
        self.sp_font = QSpinBox(); self.sp_font.setRange(4, 72); self.sp_font.setValue(int(fnt["size"]))
        self.sp_font.setSuffix(" pt")
        self.sp_font.valueChanged.connect(lambda v: self._set_font("size", v))
        self.chk_bold = Switch("Bold"); self.chk_bold.setChecked(bool(fnt["bold"]))
        self.chk_bold.toggled.connect(lambda on: self._set_font("bold", on))
        f.addRow("Font", self.font_combo)
        font_stepper = stepper(self.sp_font)
        font_stepper.setMaximumWidth(208)
        f.addRow("Size", font_stepper)
        f.addRow("Weight", self.chk_bold)
        l1.addLayout(f)
        l1.addStretch(1)

        c2, l2 = card()
        l2.addWidget(section("Colors"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
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
        controls = QWidget()
        controls.setObjectName("inline")
        self.appearance_columns = QBoxLayout(QBoxLayout.Direction.TopToBottom, controls)
        self.appearance_columns.setContentsMargins(0, 0, 0, 0)
        self.appearance_columns.setSpacing(16)
        self.appearance_columns.addWidget(c1, 1)
        self.appearance_columns.addWidget(c2, 1)
        return self._page("Appearance", "Make it yours. Preview your font and colors as you edit.", c0, controls)

    def _about_page(self):
        overview, overview_layout = card()
        overview_layout.addWidget(section(APP_NAME))
        overview_layout.addWidget(muted(
            "A customizable input overlay for Azeron keypads, keyboards, and controllers. "
            "Show your inputs as you play with a transparent, click-through overlay "
            "and live layout editing."))

        credits, credits_layout = card()
        credits_layout.addWidget(section("Created by Andres Perez"))
        credits_layout.addWidget(muted(
            "Copyright 2026 Andres Perez. Released under the MIT License."))
        credits_layout.addWidget(muted(
            "Built with PySide6, pynput, and the optional pygame-ce controller backend."))
        donations, donations_layout = card()
        donations_layout.addWidget(section("Support AZ-Overlay"))
        donations_layout.addWidget(muted(
            "Enjoying the overlay? A donation helps support its development. Thank you!"))
        donation_buttons = QHBoxLayout()
        donation_buttons.setSpacing(12)
        for provider, url in (("PayPal", PAYPAL_DONATION_URL), ("Venmo", VENMO_DONATION_URL)):
            button = QPushButton(f"Donate with {provider}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setEnabled(bool(url))
            button.setToolTip(f"Open {provider} in your browser" if url
                              else f"{provider} donations are not available yet")
            button.clicked.connect(
                lambda checked=False, provider=provider, url=url: self._open_donation(provider, url))
            donation_buttons.addWidget(button)
        donation_buttons.addStretch(1)
        donations_layout.addLayout(donation_buttons)
        return self._page("About", "Every move. On display.", overview, credits, donations)

    def _open_donation(self, provider, url):
        if url and not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.information(
                self, f"Open {provider}",
                f"Could not open your browser. Visit this link to donate:\n{url}")

    def _help_page(self):
        contact, contact_layout = card()
        contact.setObjectName("helpContact")
        contact_layout.addWidget(section("LET’S TALK"))
        title = QLabel("A little help. A better overlay.")
        title.setObjectName("helpTitle")
        title.setWordWrap(True)
        contact_layout.addWidget(title)
        contact_layout.addWidget(muted(
            "Questions, bugs, or a feature you’d love to see? Get in touch with Andres."))
        contact_layout.addSpacing(6)
        contact_row = QHBoxLayout()
        contact_row.setSpacing(16)
        address = QLabel(SUPPORT_EMAIL)
        address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse |
                                       Qt.TextInteractionFlag.TextSelectableByKeyboard)
        contact_row.addWidget(address, 1)
        email_button = QPushButton("Email")
        email_button.setObjectName("primary")
        email_button.setMinimumWidth(110)
        email_button.setCursor(Qt.CursorShape.PointingHandCursor)
        email_button.setToolTip("Open a Gmail draft in your browser")
        email_button.clicked.connect(self._email_support)
        contact_row.addWidget(email_button)
        contact_layout.addLayout(contact_row)
        contact_layout.addWidget(muted("Opens Gmail in your browser. For bugs, include your device and what happened."))

        guide, guide_layout = card()
        guide_layout.addWidget(section("Quick start"))
        for number, (heading, description) in enumerate((
            ("Pick your layout", "Choose + New layout and start with a template for your device."),
            ("Find the perfect spot", "On Layout, choose Edit on screen. Drag to move, scroll to resize, then choose Done editing."),
            ("Connect your inputs", "On Keys, select a pad and choose Record input to assign a key or controller button."),
            ("Make it yours", "Adjust fonts and colors on Appearance. Changes to saved layouts are saved automatically."),
        ), start=1):
            row = QHBoxLayout()
            row.setSpacing(14)
            marker = QLabel(f"{number:02}")
            marker.setObjectName("helpNumber")
            marker.setFixedSize(40, 40)
            marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(marker, 0, Qt.AlignmentFlag.AlignTop)
            copy = QVBoxLayout()
            copy.setSpacing(3)
            step_title = QLabel(heading)
            step_title.setObjectName("helpStepTitle")
            copy.addWidget(step_title)
            copy.addWidget(muted(description))
            row.addLayout(copy, 1)
            guide_layout.addLayout(row)

        tip, tip_layout = card()
        tip_layout.addWidget(section("Can’t see your overlay?"))
        tip_layout.addWidget(muted(
            "Turn on Overlay visible below, and use windowed or borderless mode in your game."))
        return self._page("Help", "Get set up, find your way, or send an idea.", contact, guide, tip)

    def _email_support(self):
        url = QUrl("https://mail.google.com/mail/")
        query = QUrlQuery()
        for key, value in (("view", "cm"), ("fs", "1"), ("to", SUPPORT_EMAIL), ("su", "AZ-Overlay help")):
            query.addQueryItem(key, value)
        url.setQuery(query)
        if not QDesktopServices.openUrl(url):
            QMessageBox.information(
                self, "Open Gmail",
                f"Could not open your browser. Open Gmail and write to {SUPPORT_EMAIL}.")

    # ---- behaviour ----------------------------------------------------
    def _theme_changed(self):
        theme = self.theme_combo.currentData()
        self.cfg["theme"] = theme
        self.setPalette(theme_palette(theme))
        self.setStyleSheet(style(theme))
        for row, name in enumerate(self.PAGES):
            self.nav.item(row).setIcon(navigation_icon(name, theme))
        for button in self.color_buttons:
            button.refresh()
        # Update custom item brushes without rebuilding the table or losing selection.
        blocked = self.table.blockSignals(True)
        for row, pad in enumerate(self.cfg["keys"]):
            if "sc" in pad and pad.get("input") is None:
                self.table.item(row, 1).setForeground(QColor(theme_colors(self.cfg)["muted"]))
        self.table.blockSignals(blocked)
        self.preview.update()
        self.pad_layout.update()
        self._schedule_save()

    def present(self):
        self.chk_visible.blockSignals(True)
        self.chk_visible.setChecked(self.overlay.isVisible())
        self.chk_visible.blockSignals(False)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, e):
        self.btn_move.setChecked(False)
        self.btn_capture.setChecked(False)
        if self.save_timer.isActive():
            self.save_timer.stop()
            self._save_now()
        e.accept()

    def _apply(self):
        self.overlay.apply()
        self.pad_layout.update()
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

    def _sync_scale(self, value):
        percent = round(value * 100)
        self.sl_scale.blockSignals(True)
        self.sl_scale.setValue(percent)
        self.sl_scale.blockSignals(False)
        self.lbl_scale.setText(f"{percent}%")

    def _hotkey(self, name, le):
        try:
            vks_for_label(le.text())
        except ValueError:
            le.setText(self.cfg["hotkeys"].get(name, ""))
            self._show_error("Unknown key name")
            return
        self.cfg["hotkeys"][name] = le.text().strip()
        self._apply()

    def _toggle_move(self, on):
        self.overlay.set_edit_mode(on)
        self.btn_move.setText("Done editing" if on else "Edit on screen")
        self.move_help.setText("Drag to move · Scroll to resize · Click a pad to rebind · Right-click to clear"
                               if on else "Drag to reposition. Scroll to resize. Choose Done editing when you’re finished.")
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
    def _select_visual_pad(self, row):
        self.btn_capture.setChecked(False)
        self.key_search.clear()
        self.table.selectRow(row)
        self.table.scrollToItem(self.table.item(row, 0))

    def _show_key_geometry(self, visible):
        for column in range(2, 6):
            self.table.setColumnHidden(column, not visible)

    def _filter_keys(self, text=None):
        query = self.key_search.text().strip().casefold()
        visible = 0
        for row in range(self.table.rowCount()):
            match = any(query in self.table.item(row, col).text().casefold() for col in (0, 1))
            self.table.setRowHidden(row, not match)
            visible += int(match)
        self.key_count.setText(f"{visible} / {self.table.rowCount()} pads")
        self.no_keys.setVisible(visible == 0)
        self.table.setVisible(visible > 0)
        if self.table.currentRow() >= 0 and self.table.isRowHidden(self.table.currentRow()):
            self.table.clearSelection()
        self._pad_selection_changed()

    def _pad_selection_changed(self):
        selected = bool(self.table.selectionModel().selectedRows())
        self.pad_layout.selected = self.table.currentRow() if selected else -1
        self.pad_layout.update()
        self.btn_capture.setEnabled(selected)
        self.btn_remove_pad.setEnabled(selected)
        if selected:
            label = self.cfg["keys"][self.table.currentRow()].get("label") or "Untitled pad"
            self.selection_hint.setText(f"Selected: {label}")
        else:
            self.selection_hint.setText("Select a pad below to record its input.")
        if not selected:
            self.btn_capture.setChecked(False)

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
                inp.setForeground(QColor(theme_colors(self.cfg)["muted"]))
                inp.setToolTip("Physical key (scancode). Type a key name to override.")
            self.table.setItem(r, 1, inp)
            for c, key in ((2, "col"), (3, "row"), (4, "w"), (5, "h")):
                it = QTableWidgetItem(self._num(k.get(key, 1)))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, c, it)
        self._loading = False

        self._filter_keys()

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
        self._show_error(msg)

    def _add_pad(self):
        self.key_search.clear()
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

    def _add_pad_line(self, axis):
        """Append unit pads beyond the layout bounds without copying bindings."""
        self.btn_capture.setChecked(False)
        self.key_search.clear()
        keys = self.cfg["keys"]
        cross = "col" if axis == "row" else "row"
        size = "h" if axis == "row" else "w"
        cross_size = "w" if axis == "row" else "h"
        edge = max([k[axis] + k.get(size, 1) for k in keys] +
                   [s[axis] + s.get(size, 2) for s in self.cfg.get("sticks", [])], default=0)
        start = min((k[cross] for k in keys), default=0)
        end = max((k[cross] + k.get(cross_size, 1) for k in keys), default=start + 1)
        first = len(keys)
        for offset in range(max(1, ceil(end - start))):
            keys.append({"label": "", axis: edge, cross: start + offset, "w": 1, "h": 1})
        self.show_all_pads.setChecked(True)
        self._fill_table()
        self.table.selectRow(first)
        self.table.scrollToItem(self.table.item(first, 0))
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
            self._show_error("Select a pad row first")
            return
        self.overlay.capturing = on
        self.btn_capture.setText("Cancel recording" if on else "Record input")
        if on:
            self.selection_hint.setText("Listening… press a key or controller button to assign it.")
        else:
            self._pad_selection_changed()

    def _on_key_captured(self, token):
        self.btn_capture.setChecked(False)
        r = self.table.currentRow()
        name = token if is_gamepad_input(token) else label_for_token(token)
        if name is None or r < 0:
            self._show_error(f"Unknown key ({token})")
            return
        k = self.cfg["keys"][r]
        old_input = k.get("input", k.get("label", ""))
        k.pop("sc", None)
        k["input"] = name
        if not k.get("label") or k.get("label") == old_input:
            k["label"] = GAMEPAD_LABELS.get(name, name)
        self._fill_table()
        self.table.selectRow(r)
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
        if not self._save_now():
            return
        name = dlg.name.text().strip() or dlg.device.currentText()
        prof = dlg.result_profile()
        prof["colors"] = dict(self.cfg["colors"])  # keep the user's colours
        prof["x"], prof["y"], prof["opacity"] = self.cfg["x"], self.cfg["y"], self.cfg.get("opacity", 0.85)
        migrate(prof)
        try:
            name = save_profile(name, prof)
        except (OSError, ValueError) as e:
            self._show_error(f"Could not save: {e}")
            return
        for k in PROFILE_KEYS:
            if k in prof:
                self.cfg[k] = prof[k]
        self.cfg["profile"] = name
        self._refresh_profiles()
        self._rebuild_tabs()
        self._apply()

    def _refresh_profiles(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.setPlaceholderText("Choose a saved layout")
        for name in list_profiles():
            self.profile_combo.addItem(name)
        current = self.cfg.get("profile", "")
        i = self.profile_combo.findText(current) if current else -1
        self.profile_combo.setCurrentIndex(i)
        self.delete_layout_action.setEnabled(i >= 0)
        self.profile_combo.blockSignals(False)

    def _profile_selected(self, index):
        if index < 0:
            return
        name = self.profile_combo.itemText(index)
        if not self._save_now():
            self._refresh_profiles()
            return
        try:
            data = load_profile(name)
        except (OSError, ValueError) as e:
            self._refresh_profiles()
            self._show_error(f"Could not load: {e}")
            return
        for k in PROFILE_KEYS:
            self.cfg.pop(k, None)
            if k in data:
                self.cfg[k] = data[k]
        self.cfg["profile"] = name
        self._refresh_profiles()
        self._rebuild_tabs()
        self._apply()
        self._save_now()

    def _profile_save(self):
        if not self.cfg.get("profile"):
            self._profile_save_as()
            return
        self._save_now()

    def _profile_save_as(self):
        name, ok = QInputDialog.getText(self, "Save layout", "Layout name:",
                                        text=self.cfg.get("profile", ""))
        name = name.strip()
        if not ok or not name:
            return
        if not self._save_now():
            return
        try:
            name = save_profile(name, self.cfg)
        except (OSError, ValueError) as e:
            self._show_error(f"Could not save: {e}")
            return
        self.cfg["profile"] = name
        self._refresh_profiles()
        self._schedule_save()

    def _profile_delete(self):
        if not self.cfg.get("profile"):
            return
        name = self.profile_combo.currentText()
        if QMessageBox.question(self, "Delete layout", f"Delete layout '{name}'?") != QMessageBox.StandardButton.Yes:
            return
        delete_profile(name)
        if self.cfg.get("profile") == name:
            self.cfg["profile"] = ""
        self._refresh_profiles()
        self._schedule_save()

    # ---- save ---------------------------------------------------------
    def _schedule_save(self):
        self.save_timer.start()

    def _save_now(self):
        self.save_timer.stop()
        try:
            save_config(self.cfg)
        except (OSError, ValueError) as e:
            self._show_error(f"Save failed: {e}")
            return False
        return True

    def _show_error(self, text):
        QMessageBox.warning(self, "Settings", text)

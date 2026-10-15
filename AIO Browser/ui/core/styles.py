# styles.py
"""Application-wide Qt stylesheet and dark palette generation.

The look is intentionally restrained and flat: solid colours, 1px borders and
small radii. Only true call-to-action buttons use the accent colour (via the
``PrimaryButton`` object name); everything else is neutral.
"""
from PyQt6.QtGui import QColor, QPalette  # QColor kept for backwards compatibility

from ui.core.assets import icon_url
from ui.themes import (
    THEMES,
    get_current_theme,
    set_current_theme,
    get_colors,
    COLORS,
    update_colors,
)

#: Cross-platform font stack - the first installed family is used.
FONT_STACK = (
    "'Inter', 'SF Pro Text', 'Segoe UI', 'Ubuntu', 'Noto Sans', "
    "'Cantarell', 'DejaVu Sans', 'Helvetica Neue', Arial, sans-serif"
)


def _resolve_colors(theme_name=None):
    if theme_name:
        return THEMES.get(theme_name, THEMES["default"])
    return get_colors()


def _contrast_text(color_hex):
    """Return near-black or white, whichever reads better on ``color_hex``."""
    color = QColor(color_hex)
    luminance = (
        0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
    )
    return "#0B0D10" if luminance > 0.6 else "#FFFFFF"


def build_palette(theme_name=None):
    """Return a dark QPalette matching the active theme.

    Setting a palette (in addition to the stylesheet) makes native widgets that
    are not covered by the stylesheet - menus, message boxes, item views -
    blend into the dark UI instead of falling back to a light system theme.
    """
    colors = _resolve_colors(theme_name)
    accent = QColor(colors["accent_primary"])
    text = QColor(colors["text_primary"])
    muted = QColor(colors["text_muted"])
    on_accent = QColor(_contrast_text(colors["accent_primary"]))

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["bg_primary"]))
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["bg_card"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["bg_secondary"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["bg_card"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["bg_card"]))
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["accent_red"]))
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, on_accent)
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)

    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.WindowText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, muted)

    return palette

# The stylesheet is built with %-formatting (not f-strings) so that the many
# CSS braces do not need escaping.
_STYLESHEET_TEMPLATE = """
/* ------------------------------ Base ------------------------------ */
QMainWindow, QDialog, QMessageBox, QWizard {
    background-color: %(bg_primary)s;
    color: %(text)s;
    font-family: %(font)s;
    font-size: 13px;
}

QWidget {
    color: %(text)s;
    font-family: %(font)s;
}

/* ------------------------------ Text ------------------------------ */
QLabel { background: transparent; color: %(text)s; }
QLabel#AppName { font-size: 14px; font-weight: 600; color: %(text)s; }
QLabel#PageTitle { font-size: 16px; font-weight: 600; color: %(text)s; }
QLabel#SectionLabel { font-size: 11px; font-weight: 600; color: %(muted)s; letter-spacing: 0.5px; }
QLabel#Muted { color: %(text2)s; }

/* ---------------------------- Buttons ---------------------------- */
QPushButton {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover { background-color: %(bg_hover)s; border-color: %(border_hover)s; }
QPushButton:pressed { background-color: %(bg_secondary)s; }
QPushButton:disabled {
    background-color: %(bg_secondary)s;
    color: %(muted)s;
    border-color: %(border)s;
}

QPushButton#PrimaryButton {
    background-color: %(accent)s;
    color: %(on_accent)s;
    border: 1px solid %(accent)s;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover { background-color: %(accent2)s; border-color: %(accent2)s; }
QPushButton#PrimaryButton:pressed { background-color: %(accent)s; }
QPushButton#PrimaryButton:disabled {
    background-color: %(bg_card)s;
    color: %(muted)s;
    border-color: %(border)s;
}

QToolButton {
    background: transparent;
    color: %(text2)s;
    border: none;
    border-radius: 6px;
    padding: 6px;
}
QToolButton:hover { background: %(bg_hover)s; color: %(text)s; }

/* ----------------------------- Inputs ---------------------------- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: %(accent)s;
    selection-color: %(on_accent)s;
}
QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover { border-color: %(border_hover)s; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus { border-color: %(accent)s; }

/* ------------------------- Checks / radios ----------------------- */
QCheckBox, QRadioButton { color: %(text)s; spacing: 8px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid %(border_hover)s;
    background-color: %(bg_card)s;
}
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: 8px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: %(accent)s; }
QCheckBox::indicator:checked {
    background-color: %(accent)s;
    border-color: %(accent)s;
    %(check_css)s
}
QRadioButton::indicator:checked {
    border: 5px solid %(accent)s;
    background-color: %(bg_card)s;
}

/* ------------------------------ Tabs ----------------------------- */
QTabWidget::pane { border: none; background: transparent; }
QTabWidget::tab-bar { alignment: left; }
QTabBar { background: transparent; }
QTabBar::tab {
    background: transparent;
    color: %(text2)s;
    padding: 8px 14px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}
QTabBar::tab:hover:!selected { color: %(text)s; }
QTabBar::tab:selected {
    color: %(text)s;
    border-bottom: 2px solid %(accent)s;
    font-weight: 600;
}

/* ---------------------------- Combo box -------------------------- */
QComboBox {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 7px 10px;
    min-width: 120px;
}
QComboBox:hover { border-color: %(border_hover)s; }
QComboBox:focus { border-color: %(accent)s; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow { width: 11px; height: 11px; %(arrow_css)s }
QComboBox QAbstractItemView {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 4px;
    outline: 0;
    selection-background-color: %(bg_hover)s;
    selection-color: %(text)s;
}
QComboBox QAbstractItemView::item { padding: 6px 8px; border-radius: 4px; }

/* --------------------------- Item views -------------------------- */
QListView, QListWidget, QTreeView, QTreeWidget, QTableWidget, QTableView {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    outline: 0;
    gridline-color: %(border)s;
    selection-background-color: %(accent)s;
    selection-color: %(on_accent)s;
}
QHeaderView::section {
    background-color: %(bg_secondary)s;
    color: %(text2)s;
    border: none;
    border-bottom: 1px solid %(border)s;
    padding: 6px 8px;
    font-weight: 600;
}

/* --------------------------- Scrollbars -------------------------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: %(border_hover)s; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: %(muted)s; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(border_hover)s; border-radius: 5px; min-width: 32px; }
QScrollBar::handle:horizontal:hover { background: %(muted)s; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; background: transparent; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* -------------------------- Progress bar ------------------------- */
QProgressBar {
    background-color: %(bg_secondary)s;
    border: none;
    border-radius: 3px;
    color: %(text2)s;
    text-align: center;
    font-size: 10px;
}
QProgressBar::chunk { background-color: %(accent)s; border-radius: 3px; }

/* ----------------------------- Slider ---------------------------- */
QSlider::groove:horizontal { height: 3px; background: %(border)s; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: 2px; }
QSlider::handle:horizontal {
    background: %(text)s; width: 12px; height: 12px; margin: -5px 0; border-radius: 6px;
}

/* ------------------------ Frames / containers -------------------- */
QFrame#Card { background-color: %(bg_card)s; border: 1px solid %(border)s; border-radius: 8px; }
QFrame#Card:hover { border-color: %(border_hover)s; }
QFrame#Header { background-color: %(bg_primary)s; border-bottom: 1px solid %(border)s; }
QWidget#ContentArea { background-color: %(bg_primary)s; }
QGroupBox { border: 1px solid %(border)s; border-radius: 6px; margin-top: 10px; padding: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: %(text2)s; }
QSplitter::handle { background: %(border)s; }

/* ------------------------------ Menus ---------------------------- */
QMenuBar { background: %(bg_primary)s; color: %(text)s; }
QMenuBar::item { padding: 5px 8px; background: transparent; }
QMenuBar::item:selected { background: %(bg_hover)s; }
QMenu {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { padding: 6px 18px; border-radius: 4px; }
QMenu::item:selected { background-color: %(bg_hover)s; color: %(text)s; }
QMenu::separator { height: 1px; background: %(border)s; margin: 4px 6px; }

/* ----------------------------- Dialogs --------------------------- */
QMessageBox { background-color: %(bg_primary)s; }
QDialogButtonBox QPushButton { min-width: 78px; }

/* ----------------------------- Tooltip --------------------------- */
QToolTip {
    background-color: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 5px 7px;
    font-size: 12px;
}

/* --------------------------- Status bar -------------------------- */
QStatusBar {
    background-color: %(bg_secondary)s;
    color: %(muted)s;
    border-top: 1px solid %(border)s;
    font-size: 12px;
}
QStatusBar::item { border: none; }
QSizeGrip { background: transparent; width: 16px; height: 16px; }

/* ---------------------------- Sidebar ---------------------------- */
QFrame#Sidebar { background-color: %(bg_secondary)s; border-right: 1px solid %(border)s; }
"""


def generate_stylesheet(theme_name=None):
    """Build the application stylesheet for ``theme_name`` (or the current one)."""
    colors = _resolve_colors(theme_name)
    on_accent = _contrast_text(colors["accent_primary"])

    check_url = icon_url("check", on_accent, 16)
    check_css = ("image: %s;" % check_url) if check_url else ""
    arrow_url = icon_url("chevron_down", colors["text_secondary"], 11)
    arrow_css = ("image: %s;" % arrow_url) if arrow_url else ""

    mapping = {
        "font": FONT_STACK,
        "bg_primary": colors["bg_primary"],
        "bg_secondary": colors["bg_secondary"],
        "bg_card": colors["bg_card"],
        "bg_hover": colors["bg_card_hover"],
        "accent": colors["accent_primary"],
        "accent2": colors["accent_secondary"],
        "accent_end": colors["glossy_gradient_end"],
        "on_accent": on_accent,
        "text": colors["text_primary"],
        "text2": colors["text_secondary"],
        "muted": colors["text_muted"],
        "border": colors["border"],
        "border_hover": colors["border_hover"],
        "check_css": check_css,
        "arrow_css": arrow_css,
    }
    return _STYLESHEET_TEMPLATE % mapping


# Default stylesheet for backward compatibility.
STYLESHEET = generate_stylesheet("default")


def get_sidebar_button_style(colors, is_active=False):
    """Kept for backwards compatibility; the sidebar styles itself now."""
    if is_active:
        return (
            "QPushButton { background-color: %s; color: %s; border: none; "
            "border-radius: 6px; text-align: left; font-weight: 600; }"
            % (colors["accent_glow"], colors["accent_primary"])
        )
    return (
        "QPushButton { background-color: transparent; color: %s; border: none; "
        "border-radius: 6px; text-align: left; font-weight: 500; }"
        "QPushButton:hover { background-color: %s; color: %s; }"
        % (colors["text_secondary"], colors["bg_card_hover"], colors["text_primary"])
    )


def get_theme_preview_style(theme_name):
    """A flat preview swatch for theme selection."""
    colors = THEMES.get(theme_name, THEMES["default"])
    return (
        "background-color: %s; border: 1px solid %s; border-radius: 8px;"
        % (colors["bg_primary"], colors["border"])
    )

# styles.py
"""Application-wide Qt stylesheet and dark palette generation."""
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
    "'Inter', 'Outfit', 'Segoe UI Variable Text', 'Segoe UI', 'Ubuntu', "
    "'Noto Sans', 'Cantarell', 'DejaVu Sans', 'Helvetica Neue', Arial, sans-serif"
)


def _resolve_colors(theme_name=None):
    if theme_name:
        return THEMES.get(theme_name, THEMES["default"])
    return get_colors()


def _is_black_gold(theme_name=None):
    return (theme_name or get_current_theme()) == "black_gold"


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
    on_accent = QColor("#0B0B0B" if _is_black_gold(theme_name) else "#FFFFFF")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["bg_primary"]))
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["bg_card"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["bg_secondary"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["bg_secondary"]))
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

QToolTip {
    background-color: %(bg_secondary)s;
    color: %(text)s;
    border: 1px solid %(accent)s;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12px;
}

/* ------------------------------ Text ------------------------------ */
QLabel { background: transparent; color: %(text)s; }
QLabel#TitleLabel { color: %(text2)s; font-weight: 700; letter-spacing: 1px; }
QLabel#PageTitle { font-size: 22px; font-weight: 800; color: %(text)s; }
QLabel#SectionTitle { color: %(accent)s; font-size: 11px; font-weight: 800; letter-spacing: 1px; }
QLabel#Muted { color: %(muted)s; }

/* ---------------------------- Buttons ---------------------------- */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(accent)s, stop:1 %(accent_end)s);
    color: %(on_accent)s;
    border: 1px solid %(accent2)s;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(accent2)s, stop:1 %(accent)s);
}
QPushButton:pressed { background: %(accent_end)s; }
QPushButton:disabled {
    background: %(bg_secondary)s;
    color: %(muted)s;
    border: 1px solid %(border)s;
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
    background: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    padding: 9px 12px;
    selection-background-color: %(accent)s;
    selection-color: %(on_accent)s;
}
QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover { border-color: %(border_hover)s; }
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid %(accent)s; }

/* ------------------------- Checks / radios ----------------------- */
QCheckBox, QRadioButton { color: %(text)s; spacing: 10px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid %(border_hover)s;
    background: %(bg_card)s;
}
QCheckBox::indicator { border-radius: 5px; }
QRadioButton::indicator { border-radius: 9px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: %(accent)s; }
QCheckBox::indicator:checked {
    background: %(accent)s;
    border-color: %(accent)s;
    %(check_css)s
}
QRadioButton::indicator:checked {
    border: 5px solid %(accent)s;
    background: %(bg_card)s;
}

/* ------------------------------ Tabs ----------------------------- */
QTabWidget::pane { border: none; background: transparent; }
QTabWidget::tab-bar { alignment: left; }
QTabBar { background: transparent; }
QTabBar::tab {
    background: transparent;
    color: %(text2)s;
    padding: 10px 20px;
    margin-right: 6px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:hover:!selected { color: %(text)s; }
QTabBar::tab:selected {
    color: %(accent)s;
    border-bottom: 2px solid %(accent)s;
    font-weight: 700;
}

/* ---------------------------- Combo box -------------------------- */
QComboBox {
    background: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    padding: 8px 12px;
    min-width: 120px;
}
QComboBox:hover { border-color: %(border_hover)s; }
QComboBox:focus { border-color: %(accent)s; }
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 26px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow { width: 12px; height: 12px; %(arrow_css)s }
QComboBox QAbstractItemView {
    background: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    padding: 6px;
    outline: 0;
    selection-background-color: %(accent)s;
    selection-color: %(on_accent)s;
}
QComboBox QAbstractItemView::item { padding: 7px 10px; border-radius: 6px; }

/* --------------------------- Item views -------------------------- */
QListView, QListWidget, QTreeView, QTreeWidget, QTableWidget, QTableView {
    background: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 10px;
    outline: 0;
    gridline-color: %(border)s;
    selection-background-color: %(accent)s;
    selection-color: %(on_accent)s;
}
QHeaderView::section {
    background: %(bg_secondary)s;
    color: %(text2)s;
    border: none;
    border-right: 1px solid %(border)s;
    border-bottom: 1px solid %(border)s;
    padding: 8px 10px;
    font-weight: 600;
}
QTableCornerButton::section { background: %(bg_secondary)s; border: none; }

/* --------------------------- Scrollbars -------------------------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: %(border_hover)s; border-radius: 5px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: %(border_hover)s; border-radius: 5px; min-width: 36px; }
QScrollBar::handle:horizontal:hover { background: %(accent)s; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0px; height: 0px; background: transparent; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* -------------------------- Progress bar ------------------------- */
QProgressBar {
    background: %(bg_secondary)s;
    border: 1px solid %(border)s;
    border-radius: 7px;
    color: %(text)s;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    min-height: 14px;
}
QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 %(accent)s, stop:1 %(accent2)s);
}

/* ----------------------------- Slider ---------------------------- */
QSlider::groove:horizontal { height: 4px; background: %(border)s; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: 2px; }
QSlider::handle:horizontal {
    background: %(text)s; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
}

/* ------------------------ Frames / containers -------------------- */
QFrame#Card {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 %(bg_card)s, stop:1 %(bg_secondary)s);
    border: 1px solid %(border)s;
    border-radius: 14px;
}
QFrame#Card:hover { border-color: %(accent)s; }
QFrame#Header { background: %(bg_primary)s; border-bottom: 1px solid %(border)s; }
QWidget#ContentArea { background: %(bg_primary)s; }
QGroupBox { border: 1px solid %(border)s; border-radius: 10px; margin-top: 12px; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: %(text2)s; }
QSplitter::handle { background: %(border)s; }

/* ------------------------------ Menus ---------------------------- */
QMenuBar { background: %(bg_primary)s; color: %(text)s; }
QMenuBar::item { padding: 6px 10px; background: transparent; border-radius: 6px; }
QMenuBar::item:selected { background: %(bg_hover)s; }
QMenu {
    background: %(bg_card)s;
    color: %(text)s;
    border: 1px solid %(border)s;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item { padding: 7px 22px; border-radius: 6px; }
QMenu::item:selected { background: %(accent)s; color: %(on_accent)s; }
QMenu::separator { height: 1px; background: %(border)s; margin: 5px 8px; }

/* ----------------------------- Dialogs --------------------------- */
QMessageBox { background: %(bg_primary)s; }
QMessageBox QLabel { color: %(text)s; }
QDialogButtonBox QPushButton { min-width: 84px; }

/* --------------------------- Status bar -------------------------- */
QStatusBar { background: %(bg_secondary)s; color: %(text2)s; border-top: 1px solid %(border)s; }
QStatusBar::item { border: none; }
QSizeGrip { background: transparent; width: 18px; height: 18px; }

/* ---------------------------- Sidebar ---------------------------- */
QFrame#Sidebar, QWidget#Sidebar { background: %(bg_secondary)s; border-right: 1px solid %(border)s; }
"""


def generate_stylesheet(theme_name=None):
    """Build the application stylesheet for ``theme_name`` (or the current one)."""
    colors = _resolve_colors(theme_name)
    on_accent = "#0B0B0B" if _is_black_gold(theme_name) else "#FFFFFF"

    check_url = icon_url("check", on_accent, 16)
    check_css = ("image: %s;" % check_url) if check_url else ""
    arrow_url = icon_url("chevron_down", colors["text_secondary"], 12)
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
    """Generate glossy sidebar button style."""
    if is_active:
        return (
            "QPushButton { background-color: %s; color: #FFFFFF; border: none; "
            "border-left: 3px solid %s; border-radius: 0px; padding: 15px 20px; "
            "text-align: left; font-weight: 700; }"
            % (colors["accent_glow"], colors["accent_primary"])
        )
    return (
        "QPushButton { background-color: transparent; color: %s; border: none; "
        "border-left: 3px solid transparent; border-radius: 0px; padding: 15px 20px; "
        "text-align: left; font-weight: 500; }"
        "QPushButton:hover { color: %s; }"
        % (colors["text_secondary"], colors["text_primary"])
    )


def get_theme_preview_style(theme_name):
    """Generate a mini preview style for theme selection."""
    colors = THEMES.get(theme_name, THEMES["default"])
    return (
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        "stop:0 %s, stop:0.5 %s, stop:1 %s); "
        "border: 2px solid %s; border-radius: 8px;"
        % (
            colors["bg_primary"],
            colors["accent_primary"],
            colors["bg_secondary"],
            colors["accent_primary"],
        )
    )

# styles.py
from PyQt6.QtGui import QColor
from ui.themes import (
    THEMES,
    get_current_theme,
    set_current_theme,
    get_colors,
    COLORS,
    update_colors,
)


def generate_stylesheet(theme_name=None):
    """Generate stylesheet for the given theme or current theme"""
    if theme_name:
        colors = THEMES.get(theme_name, THEMES["default"])
    else:
        colors = get_colors()

    # Add white gloss overlay and premium particle simulation for black_gold theme
    gloss_overlay = ""
    if theme_name == "black_gold" or (
        not theme_name and get_current_theme() == "black_gold"
    ):
        gloss_overlay = f"""
QWidget#ContentArea, QFrame#Card {{
    background: qradialgradient(cx:0.5, cy:0, radius:1, fx:0.5, fy:0,
        stop:0 rgba(212, 175, 55, 0.08),
        stop:0.4 {colors["bg_primary"]},
        stop:1 {colors["bg_secondary"]});
    border: 1px solid rgba(212, 175, 55, 0.1);
}}

QLabel#ParticleBackground {{
    background-color: transparent;
}}
        """

    # Define theme-specific component styles
    if theme_name == "black_gold" or (
        not theme_name and get_current_theme() == "black_gold"
    ):
        # Luxury specific styles
        btn_style = f"""
QPushButton {{
    background-color: {colors["accent_primary"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.18),
        stop:0.08 {colors["accent_primary"]},
        stop:0.55 {colors["glossy_gradient_end"]},
        stop:1 #4D3308);
    color: {colors["text_primary"]};
    border: 1px solid rgba(255, 255, 255, 0.5);
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {colors["accent_secondary"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.30),
        stop:0.1 {colors["accent_secondary"]},
        stop:0.55 {colors["accent_primary"]},
        stop:1 {colors["glossy_gradient_end"]});
    border: 1px solid {colors["accent_secondary"]};
    color: #0B0B0B;
}}
"""
        progress_chunk_style = f"""
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #996515,
        stop:0.4 {colors["accent_secondary"]},
        stop:0.5 #FFFFFF,
        stop:0.6 {colors["accent_secondary"]},
        stop:1 #996515);
    border-radius: 9px;
}}
"""
        checkbox_checked_style = f"""
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF,
        stop:0.2 {colors["accent_secondary"]},
        stop:0.6 {colors["accent_primary"]},
        stop:1 {colors["glossy_gradient_end"]});
    border-color: #FFFFFF;
}}
"""
    else:
        # Default style
        btn_style = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["glossy_shine"]},
        stop:0.1 {colors["glossy_gradient_start"]},
        stop:0.5 {colors["glossy_gradient_start"]},
        stop:0.9 {colors["glossy_gradient_end"]},
        stop:1 {colors["glossy_gradient_end"]});
    color: white;
    border: 1px solid {colors["accent_secondary"]};
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["accent_secondary"]},
        stop:0.4 {colors["accent_secondary"]},
        stop:0.5 {colors["glossy_gradient_start"]},
        stop:1 {colors["glossy_gradient_start"]});
    border: 1px solid {colors["accent_secondary"]};
}}
"""
        progress_chunk_style = f"""
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors["glossy_gradient_end"]},
        stop:0.3 {colors["accent_primary"]},
        stop:0.5 {colors["accent_secondary"]},
        stop:0.7 {colors["accent_primary"]},
        stop:1 {colors["glossy_gradient_end"]});
    border-radius: 9px;
}}
"""
        checkbox_checked_style = f"""
QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["accent_secondary"]},
        stop:0.4 {colors["accent_primary"]},
        stop:1 {colors["glossy_gradient_end"]});
    border-color: {colors["accent_primary"]};
}}
"""

    return f"""
QMainWindow, QDialog, QWidget {{
    background-color: {colors["bg_primary"]};
    color: {colors["text_primary"]};
    font-family: 'Outfit', 'Inter', 'Segoe UI', sans-serif;
}}
{gloss_overlay}

QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors["text_secondary"]};
    padding: 14px 28px;
    margin-right: 8px;
    border-bottom: 3px solid transparent;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.5px;
}}

QTabBar::tab:selected {{
    color: {colors["accent_primary"]};
    border-bottom: 3px solid {colors["accent_primary"]};
    font-weight: 800;
    background-color: rgba(255, 255, 255, 0.03);
}}

QTabBar::tab:hover:!selected {{
    color: {colors["text_primary"]};
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 10px 10px 0 0;
}}

{btn_style}

QPushButton:pressed {{
    padding-top: 10px;
    padding-bottom: 6px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["glossy_gradient_end"]},
        stop:1 {colors["accent_primary"]});
}}

QPushButton:disabled {{
    background-color: {colors["bg_secondary"]};
    color: {colors["text_muted"]};
    border: 1px solid {colors["border"]};
    opacity: 0.5;
}}

QLineEdit {{
    background: {colors["bg_card"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 14px;
    selection-background-color: {colors["accent_primary"]};
}}

QLineEdit:hover {{
    border: 1px solid {colors["border_hover"]};
    background: {colors["bg_card_hover"]};
}}

QLineEdit:focus {{
    border: 2px solid {colors["accent_primary"]};
    background: {colors["bg_secondary"]};
    outline: none;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {colors["text_muted"]};
    border-radius: 4px;
    min-height: 40px;
    opacity: 0.5;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors["accent_primary"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0px;
    background: transparent;
}}

QProgressBar {{
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    background: {colors["bg_secondary"]};
    text-align: center;
    color: white;
    font-weight: bold;
    font-size: 11px;
    height: 12px;
}}

{progress_chunk_style}

QLabel {{
    color: {colors["text_primary"]};
    background-color: transparent;
}}

QFrame#Card {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card"]},
        stop:1 {colors["bg_secondary"]});
    border-radius: 16px;
    border: 1px solid {colors["border"]};
}}

QFrame#Card:hover {{
    border: 1px solid {colors["accent_primary"]};
    background: {colors["bg_card_hover"]};
}}

QCheckBox {{
    color: {colors["text_primary"]};
    spacing: 12px;
    font-weight: 500;
}}

QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 8px;
    border: 2px solid {colors["border"]};
    background: {colors["bg_card"]};
}}

{checkbox_checked_style}

QCheckBox::indicator:hover {{
    border-color: {colors["accent_primary"]};
    background: {colors["bg_card_hover"]};
}}

QComboBox {{
    background: {colors["bg_card"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    padding: 10px 18px;
    font-size: 14px;
    min-width: 150px;
}}

QComboBox:hover {{
    border: 1px solid {colors["accent_primary"]};
    background: {colors["bg_card_hover"]};
}}

QComboBox:focus {{
    border: 2px solid {colors["accent_primary"]};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 35px;
    border-left: 1px solid {colors["border"]};
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    background: transparent;
}}

QComboBox::down-arrow {{
    image: none;
    border-top: 5px solid {colors["text_secondary"]};
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    margin-top: 2px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors["bg_card"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["accent_primary"]};
    border-radius: 10px;
    padding: 8px;
    selection-background-color: {colors["accent_primary"]};
    selection-color: white;
    outline: 0;
}}

QComboBox QAbstractItemView::item {{
    padding: 10px;
    border-radius: 6px;
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {colors["accent_primary"]};
    color: white;
}}

QListView {{
    background-color: {colors["bg_card"]};
    color: {colors["text_primary"]};
    selection-background-color: {colors["accent_primary"]};
    selection-color: white;
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    padding: 5px;
}}

QToolTip {{
    background: {colors["bg_secondary"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["accent_primary"]};
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
}}

/* Glossy Sidebar Style */
QWidget#Sidebar {{
    background: {colors["bg_secondary"]};
    border-right: 1px solid {colors["border"]};
}}

/* Glossy Header Style */
QFrame#Header {{
    background: {colors["bg_primary"]};
    border-bottom: 1px solid {colors["border"]};
}}

QStatusBar {{
    background-color: {colors["bg_secondary"]};
    color: {colors["text_secondary"]};
    border-top: 1px solid {colors["border"]};
    font-size: 12px;
}}

QSizeGrip {{
    background-color: transparent;
    width: 20px;
    height: 20px;
}}
"""


# Default stylesheet for backward compatibility
STYLESHEET = generate_stylesheet("default")


def get_sidebar_button_style(colors, is_active=False):
    """Generate glossy sidebar button style"""
    if is_active:
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.1 {colors["accent_glow"]},
                    stop:0.9 {colors["accent_glow"]},
                    stop:1 transparent);
                color: {colors["accent_primary"]};
                border: none;
                border-left: 3px solid {colors["accent_primary"]};
                border-radius: 0px;
                padding: 15px 20px;
                text-align: left;
                font-weight: 600;
            }}
        """
    else:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {colors["text_secondary"]};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
                padding: 15px 20px;
                text-align: left;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.1 {colors["bg_card_hover"]},
                    stop:0.9 {colors["bg_card_hover"]},
                    stop:1 transparent);
                color: {colors["text_primary"]};
            }}
        """


def get_theme_preview_style(theme_name):
    """Generate a mini preview style for theme selection"""
    colors = THEMES.get(theme_name, THEMES["default"])
    return f"""
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {colors["bg_primary"]},
            stop:0.5 {colors["accent_primary"]},
            stop:1 {colors["bg_secondary"]});
        border: 2px solid {colors["accent_primary"]};
        border-radius: 8px;
    """

# styles.py
from PyQt6.QtGui import QColor

# Theme Definitions
THEMES = {
    "default": {
        "name": "Midnight Purple",
        "bg_primary": "#13111C",
        "bg_secondary": "#0A090F",
        "bg_card": "#1E1B2E",
        "bg_card_hover": "#252238",
        "accent_primary": "#8B5CF6",
        "accent_secondary": "#A78BFA",
        "accent_glow": "rgba(139, 92, 246, 0.25)",
        "accent_red": "#F43F5E",
        "accent_red_hover": "#E11D48",
        "accent_green": "#10B981",
        "accent_green_hover": "#059669",
        "text_primary": "#FFFFFF",
        "text_secondary": "#9CA3AF",
        "text_muted": "#6B7280",
        "border": "#2E2B3D",
        "border_hover": "#4C4863",
        "glossy_gradient_start": "#8B5CF6",
        "glossy_gradient_end": "#6D28D9",
        "glossy_shine": "rgba(255, 255, 255, 0.15)",
    },
    "black_gold": {
        "name": "Luxury",
        "bg_primary": "#040404",
        "bg_secondary": "#000000",
        "bg_card": "#0A0A0A",
        "bg_card_hover": "#121212",
        "accent_primary": "#D4AF37",
        "accent_secondary": "#F9E076",
        "accent_glow": "rgba(212, 175, 55, 0.4)",
        "accent_red": "#991B1B",
        "accent_red_hover": "#7F1D1D",
        "accent_green": "#065F46",
        "accent_green_hover": "#064E3B",
        "text_primary": "#FFFFFF",
        "text_secondary": "#F9E076",
        "text_muted": "#8A6D1D",
        "border": "#1A1A1A",
        "border_hover": "#D4AF37",
        "glossy_gradient_start": "#F9E076",
        "glossy_gradient_end": "#996515",
        "glossy_shine": "rgba(255, 255, 255, 0.6)",
    },
}

# Current active theme (default)
_current_theme = "default"


def get_current_theme():
    return _current_theme


def set_current_theme(theme_name):
    global _current_theme
    if theme_name in THEMES:
        _current_theme = theme_name
        return True
    return False


def get_colors():
    return THEMES.get(_current_theme, THEMES["default"])


# For backward compatibility - create a copy, not a reference
COLORS = dict(THEMES["default"])


def update_colors():
    global COLORS
    # Update all keys in the COLORS dictionary with current theme
    new_colors = get_colors()
    # Remove keys that don't exist in new theme
    for key in list(COLORS.keys()):
        if key not in new_colors:
            del COLORS[key]
    # Update/add all keys from new theme
    for key, value in new_colors.items():
        COLORS[key] = value


def generate_stylesheet(theme_name=None):
    """Generate stylesheet for the given theme or current theme"""
    if theme_name:
        colors = THEMES.get(theme_name, THEMES["default"])
    else:
        colors = get_colors()

    # Add white gloss overlay and premium particle simulation for black_gold theme
    gloss_overlay = ""
    if theme_name == "black_gold" or (
        not theme_name and _current_theme == "black_gold"
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
        not theme_name and _current_theme == "black_gold"
    ):
        # Luxury specific styles
        btn_style = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["accent_secondary"]},
        stop:0.2 rgba(255, 255, 255, 0.9),
        stop:0.4 {colors["accent_primary"]},
        stop:0.5 {colors["glossy_gradient_end"]},
        stop:1 #4D3308);
    color: #000000;
    border: 1px solid rgba(255, 255, 255, 0.5);
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.3),
        stop:0.1 {colors["accent_secondary"]},
        stop:0.5 {colors["accent_secondary"]},
        stop:0.9 {colors["glossy_gradient_start"]},
        stop:1 {colors["glossy_gradient_start"]});
    border: 1px solid {colors["accent_secondary"]};
    color: #000000;
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
    font-family: 'Segoe UI', 'Roboto', 'Inter', sans-serif;
}}
{gloss_overlay}

QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {colors["text_secondary"]};
    padding: 12px 25px;
    margin-right: 5px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    font-size: 14px;
}}

QTabBar::tab:selected {{
    color: {colors["accent_primary"]};
    border-bottom: 2px solid {colors["accent_primary"]};
    font-weight: bold;
    background-color: transparent;
}}

QTabBar::tab:hover:!selected {{
    color: {colors["text_primary"]};
    background-color: {colors["bg_secondary"]};
    border-radius: 8px;
}}

{btn_style}

QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["glossy_gradient_end"]},
        stop:1 {colors["glossy_gradient_start"]});
}}

QPushButton:disabled {{
    background-color: {colors["border"]};
    color: {colors["text_muted"]};
    border: none;
}}

QLineEdit {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_secondary"]},
        stop:0.1 {colors["bg_card"]},
        stop:1 {colors["bg_secondary"]});
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 2px solid {colors["accent_primary"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card"]},
        stop:0.1 {colors["bg_card_hover"]},
        stop:1 {colors["bg_card"]});
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent,
        stop:0.5 {colors["bg_secondary"]},
        stop:1 transparent);
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors["accent_primary"]},
        stop:0.5 {colors["accent_secondary"]},
        stop:1 {colors["accent_primary"]});
    border-radius: 5px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors["accent_secondary"]},
        stop:0.5 {colors["accent_primary"]},
        stop:1 {colors["accent_secondary"]});
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QProgressBar {{
    border: 1px solid {colors["border"]};
    border-radius: 10px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_secondary"]},
        stop:0.5 {colors["bg_card"]},
        stop:1 {colors["bg_secondary"]});
    text-align: center;
    color: transparent;
    height: 10px;
}}

{progress_chunk_style}

QLabel {{
    color: {colors["text_primary"]};
    background-color: transparent;
}}

QFrame#Card {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.05),
        stop:0.05 {colors["bg_card_hover"]},
        stop:0.1 {colors["bg_card"]},
        stop:0.9 {colors["bg_card"]},
        stop:0.95 {colors["bg_secondary"]},
        stop:1 rgba(0, 0, 0, 0.8));
    border-radius: 12px;
    border: 1px solid {colors["border"]};
}}

QFrame#Card:hover {{
    border: 1px solid {colors["accent_primary"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card_hover"]},
        stop:0.1 {colors["bg_card_hover"]},
        stop:0.9 {colors["bg_card"]},
        stop:1 {colors["bg_card"]});
}}

QCheckBox {{
    color: {colors["text_primary"]};
    spacing: 10px;
}}

QCheckBox::indicator {{
    width: 22px;
    height: 22px;
    border-radius: 6px;
    border: 2px solid {colors["border"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card"]},
        stop:0.5 {colors["bg_secondary"]},
        stop:1 {colors["bg_card"]});
}}

{checkbox_checked_style}

QCheckBox::indicator:hover {{
    border-color: {colors["accent_primary"]};
}}

QComboBox {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card_hover"]},
        stop:0.5 {colors["bg_card"]},
        stop:1 {colors["bg_secondary"]});
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: 8px;
    padding: 10px 15px;
    font-size: 14px;
    min-width: 150px;
}}

QComboBox:hover {{
    border: 1px solid {colors["accent_primary"]};
}}

QComboBox:focus {{
    border: 2px solid {colors["accent_primary"]};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left: 1px solid {colors["border"]};
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["accent_primary"]},
        stop:1 {colors["glossy_gradient_end"]});
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors["bg_card"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["accent_primary"]};
    border-radius: 8px;
    selection-background-color: {colors["accent_primary"]};
    selection-color: white;
    padding: 5px;
}}

QToolTip {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {colors["bg_card_hover"]},
        stop:1 {colors["bg_card"]});
    color: {colors["text_primary"]};
    border: 1px solid {colors["accent_primary"]};
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
}}

/* Glossy Sidebar Style */
QWidget#Sidebar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {colors["bg_secondary"]},
        stop:0.01 rgba(255, 255, 255, 0.03),
        stop:0.02 {colors["bg_card"]},
        stop:0.98 {colors["bg_secondary"]},
        stop:0.99 rgba(255, 255, 255, 0.02),
        stop:1 {colors["border"]});
    border-right: 1px solid {colors["border"]};
}}

/* Glossy Header Style */
QFrame#Header {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 0.05),
        stop:0.1 {colors["bg_card"]},
        stop:0.5 {colors["bg_primary"]},
        stop:1 {colors["bg_secondary"]});
    border-bottom: 1px solid {colors["border"]};
}}

QStatusBar {{
    background-color: {colors["bg_secondary"]};
    color: {colors["text_secondary"]};
    border-top: 1px solid {colors["border"]};
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

# styles.py
from PyQt6.QtGui import QColor

COLORS = {
    "bg_primary": "#0F111A",      # Premium Deep Navy
    "bg_secondary": "#090B13",    # Darker Sidebar
    "bg_card": "#1A1F35",         # Solid Card Background
    "bg_card_hover": "#222841",   # Hover Highlight
    "accent_primary": "#7C3AED",  # Vibrant Purple
    "accent_secondary": "#A78BFA",# Lighter Purple
    "accent_glow": "rgba(124, 58, 237, 0.15)",
    "accent_red": "#EF4444",
    "accent_red_hover": "#DC2626",
    "accent_green": "#10B981",
    "accent_green_hover": "#059669",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#475569",
    "border": "#1E293B",
    "border_hover": "#334155",
}

STYLESHEET = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
    font-family: 'Segoe UI', 'Roboto', 'Inter', sans-serif;
}}

QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    padding: 12px 25px;
    margin-right: 5px;
    border-bottom: 2px solid transparent;
    font-weight: 500;
    font-size: 14px;
}}

QTabBar::tab:selected {{
    color: {COLORS["accent_primary"]};
    border-bottom: 2px solid {COLORS["accent_primary"]};
    font-weight: bold;
    background-color: transparent;
}}

QTabBar::tab:hover:!selected {{
    color: {COLORS["text_primary"]};
    background-color: {COLORS["bg_secondary"]};
    border-radius: 8px;
}}

QPushButton {{
    background-color: {COLORS["accent_primary"]};
    color: white;
    border: none;
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_secondary"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_primary"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}

QLineEdit {{
    background-color: {COLORS["bg_secondary"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border: 1px solid {COLORS["accent_primary"]};
    background-color: {COLORS["bg_card"]};
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 4px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["text_muted"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QProgressBar {{
    border: none;
    border-radius: 10px;
    background-color: {COLORS["bg_secondary"]};
    text-align: center;
    color: transparent;
    height: 8px;
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent_primary"]};
    border-radius: 10px;
}}

QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
}}

QFrame#Card {{
    background-color: {COLORS["bg_card"]};
    border-radius: 12px;
    border: 1px solid {COLORS["border"]};
}}

QFrame#Card:hover {{
    border: 1px solid {COLORS["accent_primary"]};
    background-color: {COLORS["bg_card_hover"]};
}}

QCheckBox {{
    color: {COLORS["text_primary"]};
    spacing: 10px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 2px solid {COLORS["border"]};
    background-color: {COLORS["bg_secondary"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent_primary"]};
    border-color: {COLORS["accent_primary"]};
}}
"""

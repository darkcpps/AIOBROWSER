# settings_tab.py
import os
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.core.components import InfoBanner
from ui.core.styles import (
    COLORS,
    THEMES,
    generate_stylesheet,
    get_colors,
    get_theme_preview_style,
    set_current_theme,
)


class ThemePreviewCard(QFrame):
    """A card that shows a preview of a theme"""

    clicked = pyqtSignal(str)

    def __init__(self, theme_key, theme_data, is_selected=False, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.theme_data = theme_data
        self.is_selected = is_selected
        self.setObjectName("MainCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 120)

        # Store references to widgets that need updates
        self.preview_frame = None
        self.label_frame = None
        self.name_label = None
        self.check_label = None

        self.initUI()

    def initUI(self):
        self.update_main_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Preview area
        self.preview_frame = QFrame()
        self.preview_frame.setFixedHeight(80)
        self.update_preview_style()

        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(5)

        # Mini accent bar
        accent_bar = QFrame()
        accent_bar.setFixedHeight(8)

        if self.theme_key == "black_gold":
            accent_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme_data["glossy_gradient_end"]},
                    stop:0.2 {self.theme_data["accent_primary"]},
                    stop:0.4 #FFFFFF,
                    stop:0.5 {self.theme_data["accent_secondary"]},
                    stop:0.6 #FFFFFF,
                    stop:0.8 {self.theme_data["accent_primary"]},
                    stop:1 {self.theme_data["glossy_gradient_end"]});
            """
        else:
            accent_style = f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme_data["glossy_gradient_end"]},
                    stop:0.3 {self.theme_data["accent_primary"]},
                    stop:0.5 {self.theme_data["accent_secondary"]},
                    stop:0.7 {self.theme_data["accent_primary"]},
                    stop:1 {self.theme_data["glossy_gradient_end"]});
            """

        accent_bar.setStyleSheet(f"""
            {accent_style}
            border-radius: 4px;
        """)
        preview_layout.addWidget(accent_bar)

        # Mini text preview
        text_preview = QLabel("Aa")
        text_preview.setStyleSheet(f"""
            color: {self.theme_data["text_primary"]};
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        """)
        text_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(text_preview)

        layout.addWidget(self.preview_frame)

        # Label area
        self.label_frame = QFrame()
        self.update_label_style()

        label_layout = QHBoxLayout(self.label_frame)
        label_layout.setContentsMargins(10, 8, 10, 8)

        self.name_label = QLabel(self.theme_data["name"])
        self.update_name_style()
        label_layout.addWidget(self.name_label)

        self.check_label = QLabel("✓")
        self.check_label.setStyleSheet(f"""
            color: {self.theme_data["accent_primary"]};
            font-size: 16px;
            font-weight: bold;
            background: transparent;
        """)
        self.check_label.setVisible(self.is_selected)
        label_layout.addWidget(self.check_label)

        layout.addWidget(self.label_frame)

    def update_main_style(self):
        border_color = (
            self.theme_data["accent_primary"]
            if self.is_selected
            else self.theme_data["border"]
        )

        self.setStyleSheet(f"""
            QFrame#MainCard {{
                background: transparent;
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
        """)

    def update_preview_style(self):
        if self.preview_frame:
            if self.theme_key == "black_gold":
                # Special radial preview for Royal Obsidian
                bg_style = f"""
                    background: qradialgradient(cx:0.5, cy:0, radius:1, fx:0.5, fy:0,
                        stop:0 rgba(212, 175, 55, 0.2),
                        stop:0.4 {self.theme_data["bg_primary"]},
                        stop:1 {self.theme_data["bg_secondary"]});
                """
            else:
                bg_style = f"""
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.theme_data["bg_card_hover"]},
                        stop:0.3 {self.theme_data["bg_primary"]},
                        stop:1 {self.theme_data["bg_secondary"]});
                """

            self.preview_frame.setStyleSheet(f"""
                QFrame {{
                    {bg_style}
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    border: none;
                }}
            """)

    def update_label_style(self):
        if self.label_frame:
            if self.theme_key == "black_gold":
                bg_style = f"background: {self.theme_data['bg_secondary']};"
            else:
                bg_style = f"""
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.theme_data["bg_card"]},
                        stop:1 {self.theme_data["bg_secondary"]});
                """

            self.label_frame.setStyleSheet(f"""
                QFrame {{
                    {bg_style}
                    border-bottom-left-radius: 10px;
                    border-bottom-right-radius: 10px;
                    border: none;
                    border-top: 1px solid {self.theme_data["border"]};
                }}
            """)

    def update_name_style(self):
        if self.name_label:
            color = (
                self.theme_data["accent_primary"]
                if self.is_selected
                else self.theme_data["text_primary"]
            )
            if self.theme_key == "black_gold" and not self.is_selected:
                color = self.theme_data["text_secondary"]

            self.name_label.setStyleSheet(f"""
                color: {color};
                font-size: 13px;
                font-weight: {"bold" if self.is_selected else "normal"};
                background: transparent;
            """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.theme_key)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        # Update styles without recreating widgets
        self.update_main_style()
        self.update_preview_style()
        self.update_label_style()
        self.update_name_style()
        if self.check_label:
            self.check_label.setVisible(self.is_selected)


class SettingsTab(QWidget):
    theme_changed = pyqtSignal(str)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = parent
        self.theme_cards = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Header
        title = QLabel("Settings")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 900;
            color: {COLORS["text_primary"]};
        """)
        layout.addWidget(title)

        layout.addWidget(
            InfoBanner(
                title="Quick info",
                body_lines=[
                    "Change themes, default download folder, and emulator identity settings here.",
                ],
                icon="⚙️",
                object_name="SettingsInfoBanner",
                compact=True,
            )
        )

        # ============ THEME SECTION ============
        theme_container = QWidget()
        theme_layout = QVBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(15)

        theme_title = QLabel("APPEARANCE")
        theme_title.setStyleSheet(
            f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
        )
        theme_layout.addWidget(theme_title)

        theme_desc = QLabel("Choose a theme for the application")
        theme_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        theme_layout.addWidget(theme_desc)

        # Theme cards container
        self.themes_frame = QFrame()
        self.themes_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS["bg_card"]},
                    stop:1 {COLORS["bg_secondary"]});
                border: 1px solid {COLORS["border"]};
                border-radius: 16px;
            }}
        """)
        themes_grid = QHBoxLayout(self.themes_frame)
        themes_grid.setContentsMargins(20, 20, 20, 20)
        themes_grid.setSpacing(20)

        current_theme = self.settings_manager.get("theme", "default")

        for theme_key, theme_data in THEMES.items():
            card = ThemePreviewCard(
                theme_key, theme_data, is_selected=(theme_key == current_theme)
            )
            card.clicked.connect(self.on_theme_selected)
            self.theme_cards[theme_key] = card
            themes_grid.addWidget(card)

        themes_grid.addStretch()
        theme_layout.addWidget(self.themes_frame)

        layout.addWidget(theme_container)

        # Separator
        self.sep1 = QFrame()
        self.sep1.setFrameShape(QFrame.Shape.HLine)
        self.sep1.setStyleSheet(
            f"background-color: {COLORS['border']}; max-height: 1px;"
        )
        layout.addWidget(self.sep1)

        # ============ GENERAL SECTION ============
        general_container = QWidget()
        general_layout = QVBoxLayout(general_container)
        general_layout.setContentsMargins(0, 0, 0, 0)
        general_layout.setSpacing(15)

        gen_title = QLabel("GENERAL")
        gen_title.setStyleSheet(
            f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
        )
        general_layout.addWidget(gen_title)

        self.splash_checkbox = QCheckBox("Disable startup splash screen")
        self.splash_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.splash_checkbox.stateChanged.connect(self.on_splash_changed)
        general_layout.addWidget(self.splash_checkbox)

        layout.addWidget(general_container)

        # Separator
        self.sep2 = QFrame()
        self.sep2.setFrameShape(QFrame.Shape.HLine)
        self.sep2.setStyleSheet(
            f"background-color: {COLORS['border']}; max-height: 1px;"
        )
        layout.addWidget(self.sep2)

        # ============ DOWNLOADS SECTION ============
        down_container = QWidget()
        down_layout = QVBoxLayout(down_container)
        down_layout.setContentsMargins(0, 0, 0, 0)
        down_layout.setSpacing(15)

        down_title = QLabel("DOWNLOADS")
        down_title.setStyleSheet(
            f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
        )
        down_layout.addWidget(down_title)

        path_label = QLabel("Default Download Directory")
        path_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        down_layout.addWidget(path_label)

        self.path_box = QFrame()
        self.path_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {COLORS["bg_card"]},
                stop:1 {COLORS["bg_secondary"]});
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
        """)
        path_box_layout = QHBoxLayout(self.path_box)
        path_box_layout.setContentsMargins(15, 10, 15, 10)

        self.path_display = QLabel(
            self.settings_manager.get("default_download_path", "Not set")
        )
        self.path_display.setStyleSheet(
            f"border: none; color: {COLORS['text_primary']}; font-size: 13px; background: transparent;"
        )
        self.path_display.setWordWrap(True)
        path_box_layout.addWidget(self.path_display, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedSize(90, 35)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_path)
        path_box_layout.addWidget(browse_btn)

        down_layout.addWidget(self.path_box)
        layout.addWidget(down_container)

        # Separator
        self.sep3 = QFrame()
        self.sep3.setFrameShape(QFrame.Shape.HLine)
        self.sep3.setStyleSheet(
            f"background-color: {COLORS['border']}; max-height: 1px;"
        )
        layout.addWidget(self.sep3)

        # ============ EMULATOR SECTION ============
        emu_container = QWidget()
        emu_layout = QVBoxLayout(emu_container)
        emu_layout.setContentsMargins(0, 0, 0, 0)
        emu_layout.setSpacing(15)

        emu_title = QLabel("EMULATOR IDENTITY")
        emu_title.setStyleSheet(
            f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
        )
        emu_layout.addWidget(emu_title)

        emu_fields = QHBoxLayout()
        emu_fields.setSpacing(20)

        # Nickname
        nick_v = QVBoxLayout()
        nick_l = QLabel("Nickname")
        nick_l.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("AIOUser")
        self.nick_input.setText(
            self.settings_manager.get("goldberg_nickname", "AIOUser")
        )
        self.nick_input.textChanged.connect(
            lambda t: self.settings_manager.update_setting("goldberg_nickname", t)
        )
        nick_v.addWidget(nick_l)
        nick_v.addWidget(self.nick_input)
        emu_fields.addLayout(nick_v, 1)

        # Language
        lang_v = QVBoxLayout()
        lang_l = QLabel("Language")
        lang_l.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.lang_input = QLineEdit()
        self.lang_input.setPlaceholderText("english")
        self.lang_input.setText(
            self.settings_manager.get("goldberg_language", "english")
        )
        self.lang_input.textChanged.connect(
            lambda t: self.settings_manager.update_setting("goldberg_language", t)
        )
        lang_v.addWidget(lang_l)
        lang_v.addWidget(self.lang_input)
        emu_fields.addLayout(lang_v, 1)

        emu_layout.addLayout(emu_fields)
        layout.addWidget(emu_container)

        # Add stretch at end
        layout.addStretch()

        self.setLayout(layout)
        self.load_ui_state()

    def load_ui_state(self):
        if self.settings_manager.get("disable_splash", False):
            self.splash_checkbox.setChecked(True)

        # Load saved theme
        saved_theme = self.settings_manager.get("theme", "default")
        if saved_theme in THEMES:
            set_current_theme(saved_theme)

    def on_splash_changed(self, state):
        self.settings_manager.update_setting(
            "disable_splash", state == Qt.CheckState.Checked.value
        )

    def on_theme_selected(self, theme_key):
        current_theme = self.settings_manager.get("theme", "default")
        if theme_key == current_theme:
            return

        reply = QMessageBox.question(
            self,
            "Restart Required",
            "Changing the theme requires restarting the application.\n\n"
            "⚠️ WARNING: Any active downloads will be cancelled!\n\n"
            "Do you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Update card selection states
            for key, card in self.theme_cards.items():
                card.set_selected(key == theme_key)

            # Save theme preference
            self.settings_manager.update_setting("theme", theme_key)

            # Restart application using Qt's detached process start for reliability on Windows/PyInstaller
            from PyQt6.QtCore import QProcess
            # Determine arguments for the detached process. In development we need to include the script path
            if getattr(sys, "frozen", False):
                args = sys.argv[1:]
            else:
                # Include the script (usually main_pyqt.py) when running via python interpreter
                args = [sys.argv[0]] + sys.argv[1:]
            # Start a detached copy of the executable with the arguments and current working dir
            QProcess.startDetached(sys.executable, args, os.getcwd())
            QApplication.quit()

    def refresh_theme(self):
        """Refresh all color references in the settings tab"""
        from ui.core.styles import get_colors, get_current_theme

        colors = get_colors()
        theme_key = get_current_theme()

        # Update section titles and containers
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # Find all QLabel widgets that are section titles
                if hasattr(widget, "findChildren"):
                    for label in widget.findChildren(QLabel):
                        text = label.text()
                        if text in [
                            "APPEARANCE",
                            "GENERAL",
                            "DOWNLOADS",
                            "EMULATOR IDENTITY",
                        ]:
                            label.setStyleSheet(
                                f"color: {colors['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
                            )
                        elif text in [
                            "Choose a theme for the application",
                            "Default Download Directory",
                            "Nickname",
                            "Language",
                        ]:
                            label.setStyleSheet(
                                f"color: {colors['text_secondary']}; font-size: 14px;"
                            )

        # Update the main settings title
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                if item.widget().text() == "Settings":
                    item.widget().setStyleSheet(f"""
                        font-size: 28px;
                        font-weight: 900;
                        color: {colors["text_primary"]};
                    """)
                    break

        # Update specific containers
        if hasattr(self, "themes_frame"):
            self.themes_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {colors["bg_card"]},
                        stop:1 {colors["bg_secondary"]});
                    border: 1px solid {colors["border"]};
                    border-radius: 16px;
                }}
            """)

        if hasattr(self, "path_box"):
            self.path_box.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {colors["bg_card"]},
                        stop:1 {colors["bg_secondary"]});
                    border: 1px solid {colors["border"]};
                    border-radius: 12px;
                }}
            """)

        if hasattr(self, "sep1"):
            self.sep1.setStyleSheet(
                f"background-color: {colors['border']}; max-height: 1px;"
            )
        if hasattr(self, "sep2"):
            self.sep2.setStyleSheet(
                f"background-color: {colors['border']}; max-height: 1px;"
            )
        if hasattr(self, "sep3"):
            self.sep3.setStyleSheet(
                f"background-color: {colors['border']}; max-height: 1px;"
            )

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Download Folder",
            self.settings_manager.get("default_download_path", ""),
        )
        if path:
            self.settings_manager.update_setting("default_download_path", path)
            self.path_display.setText(path)

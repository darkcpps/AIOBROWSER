# settings_tab.py
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
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

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
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(180, 120)

        # Store references to widgets that need updates
        self.preview_frame = None
        self.label_frame = None
        self.name_label = None
        self.check_label = None

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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
        accent_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {self.theme_data["glossy_gradient_end"]},
                stop:0.3 {self.theme_data["accent_primary"]},
                stop:0.5 {self.theme_data["accent_secondary"]},
                stop:0.7 {self.theme_data["accent_primary"]},
                stop:1 {self.theme_data["glossy_gradient_end"]});
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

    def update_preview_style(self):
        if self.preview_frame:
            self.preview_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.theme_data["bg_card_hover"]},
                        stop:0.3 {self.theme_data["bg_primary"]},
                        stop:1 {self.theme_data["bg_secondary"]});
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                    border: 2px solid {self.theme_data["accent_primary"] if self.is_selected else self.theme_data["border"]};
                    border-bottom: none;
                }}
            """)

    def update_label_style(self):
        if self.label_frame:
            self.label_frame.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.theme_data["bg_card"]},
                        stop:1 {self.theme_data["bg_secondary"]});
                    border-bottom-left-radius: 12px;
                    border-bottom-right-radius: 12px;
                    border: 2px solid {self.theme_data["accent_primary"] if self.is_selected else self.theme_data["border"]};
                    border-top: 1px solid {self.theme_data["border"]};
                }}
            """)

    def update_name_style(self):
        if self.name_label:
            self.name_label.setStyleSheet(f"""
                color: {self.theme_data["accent_primary"] if self.is_selected else self.theme_data["text_primary"]};
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
        themes_frame = QFrame()
        themes_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS["bg_card"]},
                    stop:1 {COLORS["bg_secondary"]});
                border: 1px solid {COLORS["border"]};
                border-radius: 16px;
            }}
        """)
        themes_grid = QHBoxLayout(themes_frame)
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
        theme_layout.addWidget(themes_frame)

        layout.addWidget(theme_container)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(sep1)

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
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(sep2)

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

        path_box = QFrame()
        path_box.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {COLORS["bg_card"]},
                stop:1 {COLORS["bg_secondary"]});
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
        """)
        path_box_layout = QHBoxLayout(path_box)
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

        down_layout.addWidget(path_box)
        layout.addWidget(down_container)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(sep3)

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
        # Update card selection states
        for key, card in self.theme_cards.items():
            card.set_selected(key == theme_key)

        # Save theme preference
        self.settings_manager.update_setting("theme", theme_key)

        # Set the new theme globally
        set_current_theme(theme_key)

        # Update the global COLORS dictionary
        from ui.core.styles import update_colors

        update_colors()

        # Apply theme to the main window
        if self.main_window:
            # Generate fresh stylesheet with the new theme
            new_stylesheet = generate_stylesheet(theme_key)

            # Apply to entire application
            self.main_window.setStyleSheet("")  # Clear first
            QApplication.instance().processEvents()  # Process the clear
            self.main_window.setStyleSheet(new_stylesheet)  # Apply new

            # Force update all child widgets
            self._recursive_update(self.main_window)

            # Update sidebar specifically
            if hasattr(self.main_window, "sidebar"):
                self.main_window.sidebar.refresh_theme()

            # Get fresh colors
            from ui.core.styles import get_colors

            colors = get_colors()

            # Update specific components with inline styles
            if hasattr(self.main_window, "content_container"):
                self.main_window.content_container.setStyleSheet(
                    f"QWidget#ContentArea {{ background-color: {colors['bg_primary']}; }}"
                )

            if hasattr(self.main_window, "page_title"):
                self.main_window.page_title.setStyleSheet(
                    f"font-size: 20px; font-weight: 800; color: {colors['text_primary']};"
                )

            if self.main_window.statusBar():
                self.main_window.statusBar().setStyleSheet(
                    f"background-color: {colors['bg_secondary']}; color: {colors['text_secondary']}; border-top: 1px solid {colors['border']};"
                )

            # Refresh settings tab colors
            self.refresh_theme()

            # Final full repaint
            QApplication.instance().processEvents()
            self.main_window.repaint()

            # Emit signal
            self.theme_changed.emit(theme_key)

    def _recursive_update(self, widget):
        """Recursively update all child widgets to apply new styles"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
        for child in widget.findChildren(QWidget):
            child.style().unpolish(child)
            child.style().polish(child)
            child.update()

    def refresh_theme(self):
        """Refresh all color references in the settings tab"""
        from ui.core.styles import get_colors

        colors = get_colors()

        # Update section titles
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

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Download Folder",
            self.settings_manager.get("default_download_path", ""),
        )
        if path:
            self.settings_manager.update_setting("default_download_path", path)
            self.path_display.setText(path)

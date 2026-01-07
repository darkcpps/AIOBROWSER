# settings_tab.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, 
                             QFrame, QHBoxLayout, QPushButton, QFileDialog, QLineEdit)
from PyQt6.QtCore import Qt
from ui.core.styles import COLORS

class SettingsTab(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
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
        
        # General Section
        general_container = QWidget()
        general_layout = QVBoxLayout(general_container)
        general_layout.setContentsMargins(0, 0, 0, 0)
        general_layout.setSpacing(15)
        
        gen_title = QLabel("GENERAL")
        gen_title.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;")
        general_layout.addWidget(gen_title)
        
        self.splash_checkbox = QCheckBox("Disable startup splash screen")
        self.splash_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.splash_checkbox.stateChanged.connect(self.on_splash_changed)
        general_layout.addWidget(self.splash_checkbox)
        
        layout.addWidget(general_container)
        
        # Downloads Section
        down_container = QWidget()
        down_layout = QVBoxLayout(down_container)
        down_layout.setContentsMargins(0, 0, 0, 0)
        down_layout.setSpacing(15)
        
        down_title = QLabel("DOWNLOADS")
        down_title.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;")
        down_layout.addWidget(down_title)
        
        path_label = QLabel("Default Download Directory")
        path_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        down_layout.addWidget(path_label)
        
        path_box = QFrame()
        path_box.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;")
        path_box_layout = QHBoxLayout(path_box)
        path_box_layout.setContentsMargins(15, 10, 15, 10)
        
        self.path_display = QLabel(self.settings_manager.get("default_download_path", "Not set"))
        self.path_display.setStyleSheet(f"border: none; color: {COLORS['text_primary']}; font-size: 13px;")
        self.path_display.setWordWrap(True)
        path_box_layout.addWidget(self.path_display, 1)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedSize(90, 35)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_path)
        path_box_layout.addWidget(browse_btn)
        
        down_layout.addWidget(path_box)
        layout.addWidget(down_container)
        
        # Emulator Section
        emu_container = QWidget()
        emu_layout = QVBoxLayout(emu_container)
        emu_layout.setContentsMargins(0, 0, 0, 0)
        emu_layout.setSpacing(15)
        
        emu_title = QLabel("EMULATOR IDENTITY")
        emu_title.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 900; letter-spacing: 1px;")
        emu_layout.addWidget(emu_title)
        
        emu_fields = QHBoxLayout()
        emu_fields.setSpacing(20)
        
        # Nickname
        nick_v = QVBoxLayout()
        nick_l = QLabel("Nickname")
        nick_l.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("AIOUser")
        self.nick_input.setText(self.settings_manager.get("goldberg_nickname", "AIOUser"))
        self.nick_input.textChanged.connect(lambda t: self.settings_manager.update_setting("goldberg_nickname", t))
        nick_v.addWidget(nick_l)
        nick_v.addWidget(self.nick_input)
        emu_fields.addLayout(nick_v, 1)
        
        # Language
        lang_v = QVBoxLayout()
        lang_l = QLabel("Language")
        lang_l.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        self.lang_input = QLineEdit()
        self.lang_input.setPlaceholderText("english")
        self.lang_input.setText(self.settings_manager.get("goldberg_language", "english"))
        self.lang_input.textChanged.connect(lambda t: self.settings_manager.update_setting("goldberg_language", t))
        lang_v.addWidget(lang_l)
        lang_v.addWidget(self.lang_input)
        emu_fields.addLayout(lang_v, 1)
        
        emu_layout.addLayout(emu_fields)
        layout.addWidget(emu_container)
        
        self.setLayout(layout)
        self.load_ui_state()

    def load_ui_state(self):
        if self.settings_manager.get("disable_splash", False):
            self.splash_checkbox.setChecked(True)
    
    def on_splash_changed(self, state):
        self.settings_manager.update_setting("disable_splash", state == Qt.CheckState.Checked.value)
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Download Folder",
            self.settings_manager.get("default_download_path", "")
        )
        if path:
            self.settings_manager.update_setting("default_download_path", path)
            self.path_display.setText(path)

# info_tab.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.styles import COLORS

class InfoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("About AIO Browser")
        title.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {COLORS['text_primary']};"
        )
        layout.addWidget(title)

        description = QLabel(
            "AIO Browser is a comprehensive tool designed to simplify managing your Steam library and discovering new games.<br><br>"
            "<b>Key Features:</b><br>"
            "<ul>"
            "<li><b>Game Search:</b> Find and download games from various sources.</li>"
            "<li><b>Steam Patcher:</b> Apply the Goldberg Emulator to your installed Steam games to play them without the Steam client running.</li>"
            "<li><b>CreamAPI Patcher:</b> Unlock DLCs for your Steam games.</li>"
            "<li><b>Downloads Manager:</b> Keep track of your game downloads.</li>"
            "</ul><br>"
            "<b>Disclaimer:</b> This software is for educational purposes only. Please support game developers by purchasing the games you enjoy."
        )
        description.setStyleSheet(
            f"font-size: 14px; color: {COLORS['text_secondary']}; line-height: 1.5;"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.setLayout(layout)

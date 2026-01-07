# patcher_tab.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.tabs.patcher.goldberg_tab import GoldbergTab
from ui.tabs.patcher.greenluma_tab import GreenLumaTab

class PatcherTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.patcher_tabs = QTabWidget()

        # Goldberg sub-tab
        self.goldberg_tab = GoldbergTab(self.main_app)
        
        # GreenLuma sub-tab
        self.greenluma_tab = GreenLumaTab(self.main_app)

        self.patcher_tabs.addTab(self.goldberg_tab, "Goldberg (Emulator)")
        self.patcher_tabs.addTab(self.greenluma_tab, "GreenLuma (DLC/Steam Unlocker)")

        main_layout.addWidget(self.patcher_tabs)
        self.setLayout(main_layout)

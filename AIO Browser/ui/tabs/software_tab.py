# software_tab.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.tabs.software.monkrus_tab import MonkrusTab

class SoftwareTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)

        # Monkrus Software Subtab
        self.monkrus_tab = MonkrusTab(self.main_app)
        self.tabs.addTab(self.monkrus_tab, "Monkrus ✅")

        # Future software suites could be added here (e.g., Office, Dev Tools)

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

# search_main_tab.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.tabs.search.knaben_search import KnabenSearchTab


class SearchMainTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.search_tabs = QTabWidget()
        self.search_tabs.setStyleSheet(
            """
            QTabBar::tab { padding: 12px 25px; margin: 0px; }
            QTabBar { margin: 0px; padding: 0px; }
            QTabWidget::pane { border: none; margin: 0px; padding: 0px; background: transparent; }
            """
        )

        self.knaben_tab = KnabenSearchTab(self.main_app)
        self.search_tabs.addTab(self.knaben_tab, "Knaben ⚠️")

        main_layout.addWidget(self.search_tabs)
        self.setLayout(main_layout)

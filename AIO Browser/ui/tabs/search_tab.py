# search_tab.py
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.tabs.search.direct_search import DirectSearchTab
from ui.tabs.search.roms_search import RomsSearchTab
from ui.tabs.search.torrent_search import TorrentSearchTab

class SearchTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.search_tabs = QTabWidget()
        self.search_tabs.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)

        # Direct Results Page
        self.direct_tab = DirectSearchTab(self.main_app)
        
        # Torrent Results Page
        self.torrent_tab = TorrentSearchTab(self.main_app)

        self.search_tabs.addTab(self.direct_tab, "Direct")
        self.search_tabs.addTab(self.torrent_tab, "Torrent")
        self.roms_tab = RomsSearchTab(self.main_app)
        self.search_tabs.addTab(self.roms_tab, "ROMS")
        main_layout.addWidget(self.search_tabs)
        self.setLayout(main_layout)

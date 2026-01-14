# monkrus_tab.py
import threading
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from core import scraper
from ui.core.styles import COLORS
from ui.core.components import LoadingWidget, GameCardWidget, InfoBanner

class MonkrusTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.results = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search Bar Area
        search_container = QFrame()
        search_container.setFixedHeight(180)
        search_container.setStyleSheet(f"background-color: {COLORS['bg_primary']}; border-bottom: 1px solid {COLORS['border']};")
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(30, 20, 30, 20)
        search_layout.setSpacing(15)

        # 1. Info Banner (Placed at top of header)
        info = InfoBanner(
            "Monkrus ✅",
            [
                "Search for Adobe apps via Monkrus. All downloads are torrents via Uztracker.",
                "Download speeds will vary based on seeders.",
            ],
            icon="✅",
            accent_color=COLORS.get("accent_green", "#22C55E"),
            compact=True,
        )
        search_layout.addWidget(info)

        # 2. Input Row (Search bar)
        input_row = QHBoxLayout()
        input_row.setSpacing(15)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search Monkrus (e.g. Photoshop, Premiere)..."
        )
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
                padding: 0 15px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['accent_primary']};
            }}
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        input_row.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedSize(120, 45)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
        """)
        self.search_btn.clicked.connect(self.perform_search)
        input_row.addWidget(self.search_btn)
        
        search_layout.addLayout(input_row)
        layout.addWidget(search_container)

        # Content Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)
        
        self.scroll.setWidget(self.content_widget)
        layout.addWidget(self.scroll)

    def clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query: return
        
        self.clear_layout()
        self.loading = LoadingWidget(f"Searching Monkrus for '{query}'")
        self.content_layout.addWidget(self.loading)
        
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        try:
            results = scraper.search_monkrus(query)
            QMetaObject.invokeMethod(self, "display_results", Qt.ConnectionType.QueuedConnection, Q_ARG(list, results))
        except Exception as e:
            print(f"[DEBUG] Search Thread Error: {e}")
            QMetaObject.invokeMethod(self, "display_results", Qt.ConnectionType.QueuedConnection, Q_ARG(list, []))

    @pyqtSlot(list)
    def display_results(self, results):
        self.clear_layout()
        if not results:
            no_results = QLabel("No results found on Monkrus.")
            no_results.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 16px; margin-top: 50px;")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_results)
            return

        for i, res in enumerate(results):
            # We add a custom download handler to the card later in main_window
            # For now we create the widget. We'll need to override the download action.
            card = GameCardWidget(res, game_type="software", parent=self.main_app, delay=i*50)
            # Override specialized download for Monkrus
            card.download_btn.clicked.disconnect()
            card.download_btn.clicked.connect(lambda checked, r=res: self.main_app.initiate_monkrus_download(r))
            self.content_layout.addWidget(card)
        
        self.content_layout.addStretch()

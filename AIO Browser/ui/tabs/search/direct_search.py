# ui/search/direct_search.py
import threading

from core import scraper
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.components import GameCardWidget, InfoBanner, LoadingWidget
from ui.core.styles import COLORS


class DirectSearchTab(QWidget):
    results_ready = pyqtSignal(list, object)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.results = []
        self.current_page = 0
        self.page_size = 5
        self.anker_client = None

        self.results_ready.connect(self.display_results)
        self.initUI()
        self.setup_animations()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        layout.addWidget(
            InfoBanner(
                title="Direct Search",
                body_lines=[
                    "Search for direct download games. Use specific titles/keywords for better matches.",
                ],
                icon="🔎",
                object_name="DirectSearchInfoBanner",
                compact=True,
            )
        )

        self.search_bar = QFrame()
        self.search_bar.setFixedHeight(60)
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;"
        )
        sb_layout = QHBoxLayout(self.search_bar)
        sb_layout.setContentsMargins(10, 5, 10, 5)
        sb_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for direct download games...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet(
            "border: none; background: transparent; padding: 0 15px; font-size: 16px;"
        )
        self.search_input.returnPressed.connect(self.start_search)
        sb_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedSize(100, 40)
        self.search_btn.clicked.connect(self.start_search)
        sb_layout.addWidget(self.search_btn)
        layout.addWidget(self.search_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(15)
        self.scroll.setWidget(self.results_widget)
        layout.addWidget(self.scroll)

    def setup_animations(self):
        self.glow_timer = QTimer()
        self.glow_timer.setInterval(50)
        self.glow_value = 0
        self.glow_direction = 1
        self.glow_timer.timeout.connect(self.animate_glow)
        self.glow_effect = QGraphicsDropShadowEffect()

    def animate_glow(self):
        self.glow_value += self.glow_direction * 5
        if self.glow_value >= 100:
            self.glow_value = 100
            self.glow_direction = -1
        elif self.glow_value <= 0:
            self.glow_value = 0
            self.glow_direction = 1
        glow_intensity = self.glow_value / 100.0

        c = QColor(COLORS["accent_primary"])
        border_color = (
            f"rgba({c.red()}, {c.green()}, {c.blue()}, {0.3 + glow_intensity * 0.7})"
        )

        shadow_blur = 10 + int(glow_intensity * 20)
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 2px solid {border_color}; border-radius: 12px;"
        )
        if self.glow_effect:
            try:
                self.glow_effect.setBlurRadius(shadow_blur)
                self.glow_effect.setColor(
                    QColor(
                        c.red(), c.green(), c.blue(), int(100 + glow_intensity * 155)
                    )
                )
                self.glow_effect.setOffset(0, 0)
            except:
                self.glow_effect = QGraphicsDropShadowEffect()
                self.search_bar.setGraphicsEffect(self.glow_effect)

    def start_glow(self):
        self.glow_value = 0
        self.glow_direction = 1
        self.glow_effect = QGraphicsDropShadowEffect()
        self.search_bar.setGraphicsEffect(self.glow_effect)
        self.glow_timer.start()

    def stop_glow(self):
        self.glow_timer.stop()
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;"
        )
        try:
            self.search_bar.setGraphicsEffect(None)
            self.glow_effect = None
        except:
            pass

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.clear_layout(self.results_layout)
        self.loading_widget = LoadingWidget("Searching")
        self.results_layout.addWidget(
            self.loading_widget, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.start_glow()
        threading.Thread(target=self.perform_search, args=(query,), daemon=True).start()

    def perform_search(self, query):
        anker = scraper.AnkerClient()
        results = anker.search(query)
        self.results_ready.emit(results, anker)

    @pyqtSlot(list, object)
    def display_results(self, results, anker_client):
        if hasattr(self, "loading_widget") and self.loading_widget:
            self.loading_widget.stop()
            self.loading_widget.deleteLater()
            self.loading_widget = None
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.stop_glow()
        self.results = results
        self.anker_client = anker_client
        self.current_page = 0
        self.render_page()

    def render_page(self):
        self.clear_layout(self.results_layout)
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_results = self.results[start:end]
        if not page_results:
            empty = QLabel("No results found.")
            empty.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 16px; margin-top: 50px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(empty)
            return
        for i, game in enumerate(page_results):
            card = GameCardWidget(game, "direct", self.main_app, delay=i * 100)
            self.results_layout.addWidget(card)
        if hasattr(self.main_app, "create_pagination_controls"):
            self.main_app.create_pagination_controls(
                self.results_layout,
                len(self.results),
                self.current_page,
                self.page_size,
                self.change_page,
            )

    def change_page(self, new_page):
        self.current_page = new_page
        self.render_page()
        self.scroll.verticalScrollBar().setValue(0)

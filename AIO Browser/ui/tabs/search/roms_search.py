# ui/search/roms_search.py
import threading

from core import scraper
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.components import GameCardWidget, InfoBanner, LoadingWidget
from ui.core.styles import COLORS


class RomsSearchTab(QWidget):
    results_ready = pyqtSignal(list)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.raw_results = []
        self.results = []
        self.current_page = 0
        self.page_size = 5

        self.results_ready.connect(self.display_results)
        self.initUI()
        self.setup_animations()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        layout.addWidget(
            InfoBanner(
                title="ROMS (Axekin)",
                body_lines=[
                    "Search Axekin for ROM downloads. Pick a console to filter results, then click Download to add it to Downloads.",
                ],
                icon="🕹️",
                object_name="RomsSearchInfoBanner",
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
        self.search_input.setPlaceholderText("Search for ROMs...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet(
            "border: none; background: transparent; padding: 0 15px; font-size: 16px;"
        )
        self.search_input.returnPressed.connect(self.start_search)
        sb_layout.addWidget(self.search_input, 1)

        self.console_combo = QComboBox()
        self.console_combo.setFixedHeight(45)
        self.console_combo.setMinimumWidth(170)
        self.console_combo.setStyleSheet(
            f"border: none; background: transparent; padding: 0 10px; font-size: 14px; color: {COLORS['text_primary']};"
        )
        self.console_combo.addItem("Any Console", "any")
        self.console_combo.currentIndexChanged.connect(self.apply_platform_filter)
        sb_layout.addWidget(self.console_combo)

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
        results = scraper.search_axekin(query)
        self.results_ready.emit(results)

    @pyqtSlot(list)
    def display_results(self, results):
        if hasattr(self, "loading_widget") and self.loading_widget:
            self.loading_widget.stop()
            self.loading_widget.deleteLater()
            self.loading_widget = None
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.stop_glow()

        self.raw_results = results or []
        self.update_console_options_from_results()
        self.apply_platform_filter()

    def update_console_options_from_results(self):
        platforms = set()
        for item in self.raw_results:
            for p in item.get("platforms") or []:
                platforms.add(str(p).lower())

        if not platforms:
            return

        current_data = self.console_combo.currentData()
        existing = {self.console_combo.itemData(i) for i in range(self.console_combo.count())}

        self.console_combo.blockSignals(True)
        try:
            for p in sorted(platforms):
                if p not in existing:
                    self.console_combo.addItem(p.upper(), p)

            # Restore selection if possible
            if current_data in {self.console_combo.itemData(i) for i in range(self.console_combo.count())}:
                idx = next(
                    (i for i in range(self.console_combo.count()) if self.console_combo.itemData(i) == current_data),
                    0,
                )
                self.console_combo.setCurrentIndex(idx)
        finally:
            self.console_combo.blockSignals(False)

    def apply_platform_filter(self):
        desired = (self.console_combo.currentData() or "any").lower()
        if desired == "any":
            self.results = list(self.raw_results)
        else:
            self.results = [
                item
                for item in self.raw_results
                if desired in {str(p).lower() for p in (item.get("platforms") or [])}
            ]
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

        for i, item in enumerate(page_results):
            card = GameCardWidget(item, "roms", self.main_app, delay=i * 100)
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


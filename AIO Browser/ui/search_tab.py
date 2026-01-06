# search_tab.py
import threading
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.styles import COLORS
from ui.components import LoadingWidget, GameCardWidget
from core import scraper

class SearchTab(QWidget):
    # Signals for thread safety
    direct_results_ready = pyqtSignal(list, object)
    torrent_results_ready = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.direct_results = []
        self.direct_current_page = 0
        self.direct_page_size = 5
        self.direct_anker_client = None

        self.torrent_results = []
        self.torrent_current_page = 0
        self.torrent_page_size = 5

        self.direct_results_ready.connect(self.display_direct_results)
        self.torrent_results_ready.connect(self.display_torrent_results)

        self.initUI()
        self.setup_search_bar_animations()

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
        self.direct_page = QWidget()
        direct_layout = QVBoxLayout(self.direct_page)
        direct_layout.setContentsMargins(40, 40, 40, 40); direct_layout.setSpacing(12)

        self.direct_search_bar = QFrame(); self.direct_search_bar.setFixedHeight(60)
        self.direct_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;")
        direct_sb_layout = QHBoxLayout(self.direct_search_bar); direct_sb_layout.setContentsMargins(10, 5, 10, 5); direct_sb_layout.setSpacing(10)

        self.direct_search_input = QLineEdit(); self.direct_search_input.setPlaceholderText("Search for direct download games...")
        self.direct_search_input.setFixedHeight(45); self.direct_search_input.setStyleSheet("border: none; background: transparent; padding: 0 15px; font-size: 16px;")
        self.direct_search_input.returnPressed.connect(self.trigger_search)
        direct_sb_layout.addWidget(self.direct_search_input, 1)

        self.direct_search_btn = QPushButton("Search"); self.direct_search_btn.setFixedSize(100, 40); self.direct_search_btn.clicked.connect(self.trigger_search)
        direct_sb_layout.addWidget(self.direct_search_btn); direct_layout.addWidget(self.direct_search_bar)

        self.direct_scroll = QScrollArea(); self.direct_scroll.setWidgetResizable(True)
        self.direct_results_widget = QWidget(); self.direct_results_layout = QVBoxLayout(self.direct_results_widget)
        self.direct_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop); self.direct_results_layout.setSpacing(15)
        self.direct_scroll.setWidget(self.direct_results_widget); direct_layout.addWidget(self.direct_scroll)

        # Torrent Results Page
        self.torrent_page = QWidget()
        torrent_layout = QVBoxLayout(self.torrent_page)
        torrent_layout.setContentsMargins(40, 40, 40, 40); torrent_layout.setSpacing(12)

        self.torrent_search_bar = QFrame(); self.torrent_search_bar.setFixedHeight(60)
        self.torrent_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;")
        torrent_sb_layout = QHBoxLayout(self.torrent_search_bar); torrent_sb_layout.setContentsMargins(10, 5, 10, 5); torrent_sb_layout.setSpacing(10)

        self.torrent_search_input = QLineEdit(); self.torrent_search_input.setPlaceholderText("Search for torrent/fitgirl repacks...")
        self.torrent_search_input.setFixedHeight(45); self.torrent_search_input.setStyleSheet("border: none; background: transparent; padding: 0 15px; font-size: 16px;")
        self.torrent_search_input.returnPressed.connect(self.trigger_search)
        torrent_sb_layout.addWidget(self.torrent_search_input, 1)

        self.torrent_search_btn = QPushButton("Search"); self.torrent_search_btn.setFixedSize(100, 40); self.torrent_search_btn.clicked.connect(self.trigger_search)
        torrent_sb_layout.addWidget(self.torrent_search_btn); torrent_layout.addWidget(self.torrent_search_bar)

        self.torrent_scroll = QScrollArea(); self.torrent_scroll.setWidgetResizable(True)
        self.torrent_results_widget = QWidget(); self.torrent_results_layout = QVBoxLayout(self.torrent_results_widget)
        self.torrent_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop); self.torrent_results_layout.setSpacing(15)
        self.torrent_scroll.setWidget(self.torrent_results_widget); torrent_layout.addWidget(self.torrent_scroll)

        self.search_tabs.addTab(self.direct_page, "Direct")
        self.search_tabs.addTab(self.torrent_page, "Torrent")
        main_layout.addWidget(self.search_tabs)
        self.setLayout(main_layout)

    def setup_search_bar_animations(self):
        self.direct_glow_timer = QTimer(); self.direct_glow_timer.setInterval(50)
        self.direct_glow_value = 0; self.direct_glow_direction = 1
        self.direct_glow_timer.timeout.connect(self.animate_direct_glow)

        self.torrent_glow_timer = QTimer(); self.torrent_glow_timer.setInterval(50)
        self.torrent_glow_value = 0; self.torrent_glow_direction = 1
        self.torrent_glow_timer.timeout.connect(self.animate_torrent_glow)

        self.direct_glow_effect = QGraphicsDropShadowEffect()
        self.torrent_glow_effect = QGraphicsDropShadowEffect()

    def animate_direct_glow(self):
        try:
            self.direct_glow_value += self.direct_glow_direction * 5
            if self.direct_glow_value >= 100: self.direct_glow_value = 100; self.direct_glow_direction = -1
            elif self.direct_glow_value <= 0: self.direct_glow_value = 0; self.direct_glow_direction = 1
            glow_intensity = self.direct_glow_value / 100.0
            border_color = f"rgba(124, 58, 237, {0.3 + glow_intensity * 0.7})"
            shadow_blur = 10 + int(glow_intensity * 20)
            self.direct_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 2px solid {border_color}; border-radius: 12px;")
            if self.direct_glow_effect:
                try:
                    self.direct_glow_effect.setBlurRadius(shadow_blur)
                    self.direct_glow_effect.setColor(QColor(124, 58, 237, int(100 + glow_intensity * 155)))
                    self.direct_glow_effect.setOffset(0, 0)
                except RuntimeError:
                    self.direct_glow_effect = QGraphicsDropShadowEffect(); self.direct_search_bar.setGraphicsEffect(self.direct_glow_effect)
        except Exception as e: print(f"[DEBUG] Direct glow animation error: {e}")

    def animate_torrent_glow(self):
        try:
            self.torrent_glow_value += self.torrent_glow_direction * 5
            if self.torrent_glow_value >= 100: self.torrent_glow_value = 100; self.torrent_glow_direction = -1
            elif self.torrent_glow_value <= 0: self.torrent_glow_value = 0; self.torrent_glow_direction = 1
            glow_intensity = self.torrent_glow_value / 100.0
            border_color = f"rgba(124, 58, 237, {0.3 + glow_intensity * 0.7})"
            shadow_blur = 10 + int(glow_intensity * 20)
            self.torrent_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 2px solid {border_color}; border-radius: 12px;")
            if self.torrent_glow_effect:
                try:
                    self.torrent_glow_effect.setBlurRadius(shadow_blur)
                    self.torrent_glow_effect.setColor(QColor(124, 58, 237, int(100 + glow_intensity * 155)))
                    self.torrent_glow_effect.setOffset(0, 0)
                except RuntimeError:
                    self.torrent_glow_effect = QGraphicsDropShadowEffect(); self.torrent_search_bar.setGraphicsEffect(self.torrent_glow_effect)
        except Exception as e: print(f"[DEBUG] Torrent glow animation error: {e}")

    def start_direct_glow(self):
        self.direct_glow_value = 0; self.direct_glow_direction = 1
        self.direct_glow_effect = QGraphicsDropShadowEffect()
        self.direct_search_bar.setGraphicsEffect(self.direct_glow_effect)
        self.direct_glow_timer.start()

    def stop_direct_glow(self):
        self.direct_glow_timer.stop()
        self.direct_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;")
        try: self.direct_search_bar.setGraphicsEffect(None); self.direct_glow_effect = None
        except: pass

    def start_torrent_glow(self):
        self.torrent_glow_value = 0; self.torrent_glow_direction = 1
        self.torrent_glow_effect = QGraphicsDropShadowEffect()
        self.torrent_search_bar.setGraphicsEffect(self.torrent_glow_effect)
        self.torrent_glow_timer.start()

    def stop_torrent_glow(self):
        self.torrent_glow_timer.stop()
        self.torrent_search_bar.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;")
        try: self.torrent_search_bar.setGraphicsEffect(None); self.torrent_glow_effect = None
        except: pass

    def trigger_search(self):
        if self.search_tabs.currentIndex() == 0: self.start_direct_search()
        else: self.start_torrent_search()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()
                else: self.clear_layout(item.layout())

    def start_direct_search(self):
        query = self.direct_search_input.text().strip()
        if not query: return
        self.clear_layout(self.direct_results_layout)
        if hasattr(self, "direct_loading_widget") and self.direct_loading_widget:
            self.direct_loading_widget.stop(); self.direct_loading_widget.deleteLater(); self.direct_loading_widget = None
        self.direct_loading_widget = LoadingWidget("Searching")
        self.direct_results_layout.addWidget(self.direct_loading_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.direct_search_btn.setEnabled(False); self.direct_search_btn.setText("Searching...")
        self.start_direct_glow()
        threading.Thread(target=self.perform_direct_search, args=(query,), daemon=True).start()

    def perform_direct_search(self, query):
        anker = scraper.AnkerClient(); results = anker.search(query)
        self.direct_results_ready.emit(results, anker)

    @pyqtSlot(list, object)
    def display_direct_results(self, results, anker_client):
        if hasattr(self, "direct_loading_widget") and self.direct_loading_widget:
            self.direct_loading_widget.stop(); self.direct_loading_widget.deleteLater(); self.direct_loading_widget = None
        self.direct_search_btn.setEnabled(True); self.direct_search_btn.setText("Search")
        self.stop_direct_glow()
        self.direct_results = results; self.direct_anker_client = anker_client; self.direct_current_page = 0
        self.render_direct_page()

    def render_direct_page(self):
        self.clear_layout(self.direct_results_layout)
        start = self.direct_current_page * self.direct_page_size
        end = start + self.direct_page_size; page_results = self.direct_results[start:end]
        if not page_results:
            empty = QLabel("No results found."); empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; margin-top: 50px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); self.direct_results_layout.addWidget(empty); return
        for i, game in enumerate(page_results):
            card = GameCardWidget(game, "direct", self.main_app, delay=i * 100)
            self.direct_results_layout.addWidget(card)
        if hasattr(self.main_app, 'create_pagination_controls'):
             self.main_app.create_pagination_controls(self.direct_results_layout, len(self.direct_results), self.direct_current_page, self.direct_page_size, self.change_direct_page)

    def change_direct_page(self, new_page):
        self.direct_current_page = new_page; self.render_direct_page()
        self.direct_scroll.verticalScrollBar().setValue(0)

    def start_torrent_search(self):
        query = self.torrent_search_input.text().strip()
        if not query: return
        self.clear_layout(self.torrent_results_layout)
        if hasattr(self, "torrent_loading_widget") and self.torrent_loading_widget:
            self.torrent_loading_widget.stop(); self.torrent_loading_widget.deleteLater(); self.torrent_loading_widget = None
        self.torrent_loading_widget = LoadingWidget("Searching")
        self.torrent_results_layout.addWidget(self.torrent_loading_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.torrent_search_btn.setEnabled(False); self.torrent_search_btn.setText("Searching...")
        self.start_torrent_glow()
        threading.Thread(target=self.perform_torrent_search, args=(query,), daemon=True).start()

    def perform_torrent_search(self, query):
        results = scraper.search_fitgirl(query); self.torrent_results_ready.emit(results)

    @pyqtSlot(list)
    def display_torrent_results(self, results):
        if hasattr(self, "torrent_loading_widget") and self.torrent_loading_widget:
            self.torrent_loading_widget.stop(); self.torrent_loading_widget.deleteLater(); self.torrent_loading_widget = None
        self.torrent_search_btn.setEnabled(True); self.torrent_search_btn.setText("Search")
        self.stop_torrent_glow()
        self.torrent_results = results; self.torrent_current_page = 0
        self.render_torrent_page()

    def render_torrent_page(self):
        self.clear_layout(self.torrent_results_layout)
        start = self.torrent_current_page * self.torrent_page_size
        end = start + self.torrent_page_size; page_results = self.torrent_results[start:end]
        if not page_results:
            empty = QLabel("No results found."); empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 16px; margin-top: 50px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter); self.torrent_results_layout.addWidget(empty); return
        for i, game in enumerate(page_results):
            card = GameCardWidget(game, "torrent", self.main_app, delay=i * 100)
            self.torrent_results_layout.addWidget(card)
        if hasattr(self.main_app, 'create_pagination_controls'):
            self.main_app.create_pagination_controls(self.torrent_results_layout, len(self.torrent_results), self.torrent_current_page, self.torrent_page_size, self.change_torrent_page)

    def change_torrent_page(self, new_page):
        self.torrent_current_page = new_page; self.render_torrent_page()
        self.torrent_scroll.verticalScrollBar().setValue(0)

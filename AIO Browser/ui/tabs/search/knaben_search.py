# ui/search/knaben_search.py
import threading

from core import scraper
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.components import GameCardWidget, InfoBanner, LoadingWidget
from ui.core.styles import COLORS


class KnabenSearchTab(QWidget):
    results_ready = pyqtSignal(list)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.results = []
        self.current_page = 0
        self.page_size = 5
        self._warning_ack_session = False

        self.results_ready.connect(self.display_results)
        self.initUI()
        self.setup_animations()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        self._default_banner_title = "Knaben"
        self._default_banner_body_lines = [
            "Search Knaben for torrents and download via magnet links.",
            "<b>Will show everything so be specific on your searches.</b>",
            "<b style='color: #ff6b6b;'>⚠️ UNTRUSTED CONTENT - Only use if you know what you're doing.</b>",
        ]
        self._default_banner_icon = "🧲"

        self.banner = InfoBanner(
            title=self._default_banner_title,
            body_lines=self._default_banner_body_lines,
            icon=self._default_banner_icon,
            object_name="KnabenInfoBanner",
            compact=True,
        )
        layout.addWidget(self.banner)

        self.search_bar = QFrame()
        self.search_bar.setFixedHeight(60)
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;"
        )
        sb_layout = QHBoxLayout(self.search_bar)
        sb_layout.setContentsMargins(10, 5, 10, 5)
        sb_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Knaben...")
        self.search_input.setFixedHeight(45)
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
        if not self.isVisible():
            return
        self.glow_value += self.glow_direction * 5
        if self.glow_value >= 100:
            self.glow_value = 100
            self.glow_direction = -1
        elif self.glow_value <= 0:
            self.glow_value = 0
            self.glow_direction = 1

        glow_intensity = self.glow_value / 100.0
        c = QColor(COLORS["accent_primary"])
        shadow_blur = 10 + int(glow_intensity * 20)

        if self.glow_effect:
            try:
                self.glow_effect.setBlurRadius(shadow_blur)
                self.glow_effect.setColor(
                    QColor(
                        c.red(), c.green(), c.blue(), int(100 + glow_intensity * 155)
                    )
                )
                self.glow_effect.setOffset(0, 0)
            except Exception:
                pass

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
        except Exception:
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

    def _confirm_first_search_warning(self):
        if self._warning_ack_session:
            return True

        settings_manager = getattr(self.main_app, "settings_manager", None)
        acknowledged = False
        if settings_manager is not None:
            acknowledged = bool(
                settings_manager.get("knaben_warning_acknowledged", False)
                or settings_manager.get("btdigg_warning_acknowledged", False)
            )

        if acknowledged:
            self._warning_ack_session = True
            return True

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Warning")
        box.setText(
            "These results may be unsafe and could affect your computer.\n"
            "Only use if you know what you're doing."
        )
        box.setInformativeText("Do you want to continue with this Knaben search?")
        box.setStandardButtons(
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes
        )
        box.setDefaultButton(QMessageBox.StandardButton.Cancel)
        result = box.exec()
        if result != QMessageBox.StandardButton.Yes:
            return False

        if settings_manager is not None:
            # Write both keys for backwards compatibility with older settings.json
            settings_manager.update_setting("knaben_warning_acknowledged", True)
            settings_manager.update_setting("btdigg_warning_acknowledged", True)
        self._warning_ack_session = True
        return True

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        if not self._confirm_first_search_warning():
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
        results = scraper.search_knaben(query)
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
        self.results = results or []
        self.current_page = 0

        if (
            len(self.results) == 1
            and isinstance(self.results[0], dict)
            and "blocked" in str(self.results[0].get("title", "")).lower()
        ):
            self.banner.set_content(
                title="Knaben (Blocked)",
                body_lines=[
                    "Knaben returned an unsupported response, so the app can't scrape magnets right now.",
                    "Click the result below to open the search in your browser, then try again later.",
                ],
                icon="⚠️",
            )
        else:
            self.banner.set_content(
                title=self._default_banner_title,
                body_lines=self._default_banner_body_lines,
                icon=self._default_banner_icon,
            )
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
            card = GameCardWidget(item, "torrent", self.main_app, delay=i * 100)
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

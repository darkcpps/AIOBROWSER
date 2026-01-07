# gui_pyqt.py
# PyQt6 Graphical User Interface refactored
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

from core import downloader, scraper
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.components import (
    AnimatedStackedWidget,
    GoldParticleBackground,
    ModernSidebar,
)
from ui.core.splash_screen import SplashScreen
from ui.core.styles import (
    COLORS,
    STYLESHEET,
    THEMES,
    generate_stylesheet,
    set_current_theme,
)
from ui.dialogs.settings_dialog import SettingsManager
from ui.tabs.downloads_page import DownloadsPage
from ui.tabs.info_tab import InfoTab
from ui.tabs.patcher_tab import PatcherTab
from ui.tabs.search_tab import SearchTab
from ui.tabs.settings_tab import SettingsTab

# =========================================================================
# MAIN APPLICATION WINDOW
# =========================================================================


class GameSearchApp(QMainWindow):
    # Custom Signals for Thread Safety
    download_prompt_ready = pyqtSignal(
        str, str, object, str
    )  # url, name, session, download_id
    download_status_updated = pyqtSignal(
        str, str, float
    )  # download_id, status, progress
    download_finished = pyqtSignal(str, str, str)  # download_id, result, save_path

    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.image_cache = {}

        # Connect Signals
        self.download_prompt_ready.connect(self.prompt_download)
        self.download_status_updated.connect(self.update_download_status)
        self.download_finished.connect(self.on_download_finished)

        self.initUI()

        # Load saved theme and apply it properly
        saved_theme = self.settings_manager.get("theme", "default")
        if saved_theme in THEMES:
            set_current_theme(saved_theme)
            # Update global colors
            from ui.core.styles import update_colors

            update_colors()
            # Apply stylesheet
            self.setStyleSheet(generate_stylesheet(saved_theme))

        if not self.settings_manager.get("disable_splash", False):
            self.show_splash()
        else:
            self.show_main_interface()

    def initUI(self):
        self.setWindowTitle("🎮 AIO Browser")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet(STYLESHEET)

        # Initialize and style StatusBar
        status = self.statusBar()
        status.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; color: {COLORS['text_secondary']}; border-top: 1px solid {COLORS['border']};"
        )
        status.showMessage("Ready")

    def show_splash(self):
        self.splash = SplashScreen(on_finished_callback=self.transition_to_main)
        self.splash.start_animation()

    def transition_to_main(self):
        self.show_main_interface()
        self.show()

    def show_main_interface(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = ModernSidebar(self)
        self.sidebar.setObjectName("Sidebar")
        layout.addWidget(self.sidebar)

        # Content Area
        self.content_container = QWidget()
        self.content_container.setObjectName("ContentArea")

        # Add background particles if in black_gold theme
        if self.settings_manager.get("theme", "default") == "black_gold":
            self.content_particles = GoldParticleBackground(self.content_container)
            self.content_particles.lower()

        self.content_container.setStyleSheet(
            f"QWidget#ContentArea {{ background-color: {COLORS['bg_primary']}; }}"
        )
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setObjectName("Header")
        self.header.setFixedHeight(70)
        self.header.setStyleSheet(
            f"QFrame#Header {{ background-color: {COLORS['bg_primary']}; border-bottom: 1px solid {COLORS['border']}; }}"
        )
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(30, 0, 30, 0)
        self.page_title = QLabel("Search")
        self.page_title.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {COLORS['text_primary']};"
        )
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        self.header.setLayout(header_layout)
        content_layout.addWidget(self.header)

        # Main Stack
        self.main_stack = AnimatedStackedWidget()

        # Tabs
        self.search_tab = SearchTab(self)
        self.main_stack.addWidget(self.search_tab)

        self.downloads_tab = DownloadsPage(self)
        self.main_stack.addWidget(self.downloads_tab)

        self.patcher_tab = PatcherTab(self)
        self.main_stack.addWidget(self.patcher_tab)

        self.info_tab = InfoTab(self)
        self.main_stack.addWidget(self.info_tab)

        self.settings_tab = SettingsTab(self.settings_manager, self)
        self.main_stack.addWidget(self.settings_tab)

        content_layout.addWidget(self.main_stack)
        self.content_container.setLayout(content_layout)
        layout.addWidget(self.content_container)
        central.setLayout(layout)

        self.sidebar.set_active("search")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "content_particles"):
            self.content_particles.setGeometry(self.content_container.rect())

    def refresh_content_particles(self):
        """Toggle content area particles based on theme"""
        is_gold = self.settings_manager.get("theme", "default") == "black_gold"
        if is_gold:
            if not hasattr(self, "content_particles"):
                self.content_particles = GoldParticleBackground(self.content_container)
                self.content_particles.lower()
                self.content_particles.setGeometry(self.content_container.rect())
            self.content_particles.show()
        elif hasattr(self, "content_particles"):
            self.content_particles.hide()

    def create_pagination_controls(
        self, layout, total_items, current_page, page_size, callback
    ):
        total_pages = (total_items + page_size - 1) // page_size
        if total_pages <= 1:
            return
        footer = QWidget()
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(40, 40)
        prev_btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border-radius: 8px; }} QPushButton:hover {{ background-color: {COLORS['bg_card_hover']}; }}"
        )
        if current_page > 0:
            prev_btn.clicked.connect(lambda: callback(current_page - 1))
        else:
            prev_btn.setEnabled(False)
        footer_layout.addWidget(prev_btn)
        start_page = max(0, current_page - 2)
        end_page = min(total_pages, start_page + 5)
        if end_page - start_page < 5:
            start_page = max(0, end_page - 5)
        for p in range(start_page, end_page):
            page_btn = QPushButton(str(p + 1))
            page_btn.setFixedSize(40, 40)
            if p == current_page:
                page_btn.setStyleSheet(
                    f"QPushButton {{ background-color: {COLORS['accent_primary']}; color: white; border-radius: 8px; }}"
                )
            else:
                page_btn.setStyleSheet(
                    f"QPushButton {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border-radius: 8px; }} QPushButton:hover {{ background-color: {COLORS['bg_card_hover']}; }}"
                )
            page_btn.clicked.connect(lambda checked, page=p: callback(page))
            footer_layout.addWidget(page_btn)
        next_btn = QPushButton(">")
        next_btn.setFixedSize(40, 40)
        next_btn.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['bg_card']}; color: {COLORS['text_primary']}; border-radius: 8px; }} QPushButton:hover {{ background-color: {COLORS['bg_card_hover']}; }}"
        )
        if current_page < total_pages - 1:
            next_btn.clicked.connect(lambda: callback(current_page + 1))
        else:
            next_btn.setEnabled(False)
        footer_layout.addWidget(next_btn)
        footer.setLayout(footer_layout)
        layout.addWidget(footer)

    def initiate_anker_download(self, game):
        import uuid

        download_id = str(uuid.uuid4())
        self.downloads_tab.add_download(download_id, game["title"])
        self.sidebar.set_active("downloads")
        threading.Thread(
            target=self.process_anker_download_flow,
            args=(
                game["link"],
                game["title"],
                self.search_tab.direct_tab.anker_client,
                download_id,
            ),
            daemon=True,
        ).start()

    def process_anker_download_flow(self, game_url, game_title, anker, download_id):
        self.download_status_updated.emit(
            download_id, "🔗 Fetching direct link...", 0.1
        )
        try:
            final_url, error = anker.get_download_link(game_url)
            if error or not final_url:
                self.download_status_updated.emit(
                    download_id, f"❌ Error: {error}. Opening page...", 0
                )
                time.sleep(2)
                webbrowser.open(game_url)
                return
            self.download_status_updated.emit(
                download_id, "🔍 Resolving final link...", 0.3
            )
            real_file_url, suggested_name = anker.resolve_final_link(final_url)
            if not suggested_name:
                suggested_name = game_title.strip()
            self.download_prompt_ready.emit(
                real_file_url, suggested_name, anker.session, download_id
            )
        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            self.download_status_updated.emit(download_id, f"❌ Error: {str(e)}", 0)

    @pyqtSlot(str, str, object, str)
    def prompt_download(self, url, default_name, session, download_id):
        if "ankergames.net" in url and "treasure-box" in url:
            self.download_status_updated.emit(
                download_id, "⚠ Opening manual download page...", 1.0
            )
            time.sleep(1)
            webbrowser.open(url)
            return
        initial_dir = self.settings_manager.get("default_download_path", "")
        if not os.path.exists(initial_dir):
            initial_dir = str(Path.home() / "Downloads")
        save_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", initial_dir
        )
        if save_path:
            item_widget = self.downloads_tab.items.get(download_id)

            def progress_callback(text, progress):
                self.download_status_updated.emit(download_id, text, progress)

            def run_download():
                self.download_status_updated.emit(
                    download_id, "⏳ Preparing download...", 0
                )
                time.sleep(0.5)
                if session and "Referer" in session.headers:
                    del session.headers["Referer"]
                if session and "X-Requested-With" in session.headers:
                    del session.headers["X-Requested-With"]
                result = downloader.download_file(
                    url,
                    save_path,
                    progress_callback,
                    item_widget.control_flags
                    if item_widget
                    else {"paused": False, "stopped": False},
                    session=session,
                )
                self.download_finished.emit(download_id, result, save_path)

            threading.Thread(target=run_download, daemon=True).start()
        else:
            self.download_status_updated.emit(download_id, "❌ Download cancelled", 0)

    @pyqtSlot(str, str, float)
    def update_download_status(self, download_id, text, progress):
        item = self.downloads_tab.items.get(download_id)
        if item:
            item.update_progress(text, progress)

    @pyqtSlot(str, str, str)
    def on_download_finished(self, download_id, result, save_path):
        if result == "SUCCESS":
            self.update_download_status(
                download_id, f"✅ Complete: {os.path.basename(save_path)}", 1.0
            )

            def final_cleanup():
                try:
                    os.startfile(os.path.dirname(save_path))
                except:
                    pass

            QTimer.singleShot(2000, final_cleanup)
        elif result == "STOPPED":
            self.update_download_status(download_id, "⏹ Download Stopped", 0)
        elif result == "ERROR":
            self.update_download_status(download_id, "❌ Error occurred", 0)

    def open_settings(self):
        self.sidebar.set_active("settings")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = GameSearchApp()
    screen = QApplication.primaryScreen().geometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)
    if window.settings_manager.get("disable_splash", False):
        window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

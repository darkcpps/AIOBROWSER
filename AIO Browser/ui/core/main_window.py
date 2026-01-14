# gui_pyqt.py
# PyQt6 Graphical User Interface refactored
import os
import sys
import threading
import time
import webbrowser
import requests
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
from ui.core.titlebar import CustomTitleBar
from ui.dialogs.settings_dialog import SettingsManager
from ui.tabs.downloads_page import DownloadsPage
from ui.tabs.emulators_tab import EmulatorsTab
from ui.tabs.info_tab import InfoTab
from ui.tabs.patcher_tab import PatcherTab
from ui.tabs.games_tab import GamesTab
from ui.tabs.search_main_tab import SearchMainTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.downloader_hub import DownloaderHub
from ui.tabs.software_tab import SoftwareTab

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

        # Load saved theme and apply it BEFORE initUI
        saved_theme = self.settings_manager.get("theme", "default")
        if saved_theme in THEMES:
            set_current_theme(saved_theme)
            from ui.core.styles import update_colors
            update_colors()
            
        # Apply initial stylesheet to the application
        app = QApplication.instance()
        if app:
            app.setStyleSheet(generate_stylesheet(saved_theme if saved_theme in THEMES else "default"))

        self.initUI()

        if not self.settings_manager.get("disable_splash", False):
            self.show_splash()
        else:
            self.show_main_interface()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("🎮 AIO Browser v0.1.3")
        self.setGeometry(100, 100, 1100, 750)

        # Initialize and style StatusBar
        status = self.statusBar()
        status.showMessage("Ready")
        status.addPermanentWidget(QSizeGrip(self))

    def show_splash(self):
        self.splash = SplashScreen(on_finished_callback=self.transition_to_main)
        self.splash.start_animation()

    def transition_to_main(self):
        self.show_main_interface()
        self.show()

    def show_main_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Main vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Horizontal container for Sidebar + Content
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self.sidebar = ModernSidebar(self)
        self.sidebar.setObjectName("Sidebar")
        body_layout.addWidget(self.sidebar)

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
        self.header.setFixedHeight(80)
        self.header.setStyleSheet(
            f"QFrame#Header {{ background-color: {COLORS['bg_primary']}; border-bottom: 1px solid {COLORS['border']}; }}"
        )
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(40, 0, 40, 0)
        self.page_title = QLabel("Games")
        self.page_title.setStyleSheet(
            f"font-size: 26px; font-weight: 1000; color: {COLORS['text_primary']}; letter-spacing: -0.5px;"
        )
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        
        self.header.setLayout(header_layout)
        content_layout.addWidget(self.header)

        # Main Stack
        self.main_stack = AnimatedStackedWidget()

        # Tabs
        self.games_tab = GamesTab(self)
        self.main_stack.addWidget(self.games_tab)

        self.downloads_tab = DownloadsPage(self)
        self.main_stack.addWidget(self.downloads_tab)

        self.patcher_tab = PatcherTab(self)
        self.main_stack.addWidget(self.patcher_tab)

        self.downloader_tab = DownloaderHub(self)
        self.main_stack.addWidget(self.downloader_tab)

        self.emulators_tab = EmulatorsTab(self)
        self.main_stack.addWidget(self.emulators_tab)

        self.info_tab = InfoTab(self)
        self.main_stack.addWidget(self.info_tab)

        self.settings_tab = SettingsTab(self.settings_manager, self)
        self.main_stack.addWidget(self.settings_tab)

        self.software_tab = SoftwareTab(self)
        self.main_stack.addWidget(self.software_tab)

        self.search_tab = SearchMainTab(self)
        self.main_stack.addWidget(self.search_tab)

        content_layout.addWidget(self.main_stack)
        self.content_container.setLayout(content_layout)
        body_layout.addWidget(self.content_container)

        main_layout.addLayout(body_layout)
        central.setLayout(main_layout)

        self.sidebar.set_active("games")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "content_particles"):
            self.content_particles.setGeometry(self.content_container.rect())

    def closeEvent(self, event):
        if hasattr(self, "downloads_tab") and self.downloads_tab.has_active_downloads():
            reply = QMessageBox.question(
                self,
                "Warning: Active Downloads",
                "There are downloads currently in progress.\n\n"
                "If you close the application now, these downloads will be CANCELLED and incomplete files will be removed.\n\n"
                "Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.cleanup_active_downloads()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def cleanup_active_downloads(self):
        """Attempts to stop all active downloads before closing."""
        if hasattr(self, "downloads_tab"):
            for item in self.downloads_tab.items.values():
                if not item.control_flags["stopped"]:
                    item.control_flags["stopped"] = True

            # Give threads a short moment to process the stop flag and delete files
            loop = QEventLoop()
            QTimer.singleShot(1000, loop.quit)
            loop.exec()

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
                self.games_tab.direct_tab.anker_client,
                download_id,
            ),
            daemon=True,
        ).start()

    def initiate_axekin_download(self, item):
        import uuid

        try:
            url = item.get("link") if isinstance(item, dict) else None
            title = item.get("title") if isinstance(item, dict) else None
        except Exception:
            url = None
            title = None

        if not url:
            return
        if not title:
            title = "ROM Download"

        download_id = str(uuid.uuid4())
        self.downloads_tab.add_download(download_id, title)
        self.sidebar.set_active("downloads")
        self.download_prompt_ready.emit(url, title, None, download_id)

    def initiate_torrent_download(self, magnet_link, title):
        """Start a BitTorrent download directly from a magnet link."""
        if not self.settings_manager.get("enable_bittorrent", False):
            QMessageBox.information(
                self,
                "BitTorrent Disabled",
                "Enable the BitTorrent client in Settings to download magnet links.",
            )
            return

        from core.bittorrent_downloader import download_torrent, is_available, list_torrent_files

        if not is_available():
            QMessageBox.warning(
                self,
                "libtorrent Not Installed",
                "The BitTorrent client requires the Python package 'libtorrent'.",
            )
            return

        file_entries = self._prompt_torrent_file_selection(
            magnet_link, title, list_torrent_files=list_torrent_files
        )
        if file_entries is None:
            return

        selected_indices = self._prompt_torrent_file_choices(title, file_entries)
        if not selected_indices:
            return

        initial_dir = self.settings_manager.get("default_download_path", "")
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = str(Path(sys.argv[0]).resolve().parent)
        save_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", initial_dir
        )
        if not save_path:
            return

        import uuid

        download_id = str(uuid.uuid4())
        self.downloads_tab.add_download(download_id, title)
        self.sidebar.set_active("downloads")
        item_widget = self.downloads_tab.items.get(download_id)

        def progress_callback(text, progress):
            self.download_status_updated.emit(download_id, text, progress)

        def run_torrent():
            result = download_torrent(
                magnet_link,
                save_path,
                progress_callback,
                item_widget.control_flags
                if item_widget
                else {"paused": False, "stopped": False},
                selected_file_indices=selected_indices,
            )
            self.download_finished.emit(download_id, result, save_path)

        threading.Thread(target=run_torrent, daemon=True).start()

    def prompt_torrent_download(self):
        if not self.settings_manager.get("enable_bittorrent", False):
            QMessageBox.information(
                self,
                "BitTorrent Disabled",
                "Enable the BitTorrent client in Settings to download magnet links.",
            )
            return

        from core.bittorrent_downloader import download_torrent, is_available, list_torrent_files

        if not is_available():
            QMessageBox.warning(
                self,
                "libtorrent Not Installed",
                "The BitTorrent client requires the Python package 'libtorrent'.",
            )
            return

        chooser = QMessageBox(self)
        chooser.setWindowTitle("Add Torrent")
        chooser.setText("How would you like to add a torrent?")
        magnet_btn = chooser.addButton("Magnet link", QMessageBox.ButtonRole.AcceptRole)
        file_btn = chooser.addButton(".torrent file", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = chooser.addButton(QMessageBox.StandardButton.Cancel)
        chooser.exec()

        clicked = chooser.clickedButton()
        if clicked == cancel_btn or clicked is None:
            return

        source = ""
        title = "Torrent Download"
        if clicked == magnet_btn:
            link, ok = QInputDialog.getText(
                self, "Add Magnet Link", "Paste Magnet Link:"
            )
            if not ok or not link:
                return
            source = link.strip()
            title = "Magnet Download"
        elif clicked == file_btn:
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Select Torrent", "", "Torrent Files (*.torrent)"
            )
            if not file_name:
                return
            source = file_name
            title = os.path.basename(file_name)
        else:
            return

        file_entries = self._prompt_torrent_file_selection(
            source, title, list_torrent_files=list_torrent_files
        )
        if file_entries is None:
            return

        selected_indices = self._prompt_torrent_file_choices(title, file_entries)
        if not selected_indices:
            return

        initial_dir = self.settings_manager.get("default_download_path", "")
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = str(Path(sys.argv[0]).resolve().parent)
        save_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", initial_dir
        )
        if not save_path:
            return

        import uuid

        download_id = str(uuid.uuid4())
        self.downloads_tab.add_download(download_id, title)
        self.sidebar.set_active("downloads")
        item_widget = self.downloads_tab.items.get(download_id)

        def progress_callback(text, progress):
            self.download_status_updated.emit(download_id, text, progress)

        def run_torrent():
            result = download_torrent(
                source,
                save_path,
                progress_callback,
                item_widget.control_flags
                if item_widget
                else {"paused": False, "stopped": False},
                selected_file_indices=selected_indices,
            )
            self.download_finished.emit(download_id, result, save_path)

        threading.Thread(target=run_torrent, daemon=True).start()

    def initiate_monkrus_download(self, item):
        """Starts the multi-step resolution for Monkrus software."""
        print(f"[DEBUG] Initiating Monkrus Download for: {item['title']}")
        import uuid
        download_id = str(uuid.uuid4())
        self.downloads_tab.add_download(download_id, item["title"])
        self.sidebar.set_active("downloads")

        def run_resolution():
            print(f"[DEBUG] [{download_id}] Thread started for resolution")
            self.download_status_updated.emit(download_id, "🔗 Finding tracker link...", 0.1)
            final_torrent_url, error = scraper.resolve_monkrus_to_torrent(item["link"])
            
            if error or not final_torrent_url:
                print(f"[DEBUG] [{download_id}] Resolution failed: {error}")
                self.download_status_updated.emit(download_id, f"❌ Error: {error or 'Link not found'}", 0)
                return
            
            print(f"[DEBUG] [{download_id}] Torrent URL resolved: {final_torrent_url}")
            self.download_status_updated.emit(download_id, "📥 Downloading .torrent...", 0.4)
            
            try:
                # 1. Download the .torrent file to a temporary location
                import tempfile
                temp_dir = tempfile.gettempdir()
                torrent_file_path = os.path.join(temp_dir, f"{download_id}.torrent")
                
                print(f"[DEBUG] [{download_id}] Saving temp torrent file to: {torrent_file_path}")
                resp = requests.get(final_torrent_url, headers=scraper.HEADERS, stream=True)
                with open(torrent_file_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"[DEBUG] [{download_id}] .torrent file downloaded successfully.")
                self.download_status_updated.emit(download_id, "📁 Select save folder...", 0.6)
                
                # 2. Ask user for save directory
                QMetaObject.invokeMethod(self, "_finish_monkrus_on_main_thread", 
                                       Qt.ConnectionType.QueuedConnection, 
                                       Q_ARG(str, torrent_file_path),
                                       Q_ARG(str, item["title"]),
                                       Q_ARG(str, download_id))
                                       
            except Exception as e:
                print(f"[DEBUG] [{download_id}] Exception during .torrent download: {str(e)}")
                self.download_status_updated.emit(download_id, f"❌ Download Error: {str(e)}", 0)

        threading.Thread(target=run_resolution, daemon=True).start()

    @pyqtSlot(str, str, str)
    def _finish_monkrus_on_main_thread(self, torrent_path, title, download_id):
        print(f"[DEBUG] [{download_id}] UI Prompt triggered for save folder.")
        initial_dir = self.settings_manager.get("default_download_path", "")
        # ... remainder preserved ...
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = str(Path(sys.argv[0]).resolve().parent)
            
        from core.bittorrent_downloader import download_torrent, list_torrent_files

        file_entries = self._prompt_torrent_file_selection(
            torrent_path, title, list_torrent_files=list_torrent_files
        )
        if file_entries is None:
            self.download_status_updated.emit(download_id, "❌ Cancelled", 0)
            try:
                os.remove(torrent_path)
            except Exception:
                pass
            return

        selected_indices = self._prompt_torrent_file_choices(title, file_entries)
        if not selected_indices:
            self.download_status_updated.emit(download_id, "❌ Cancelled", 0)
            try:
                os.remove(torrent_path)
            except Exception:
                pass
            return

        save_path = QFileDialog.getExistingDirectory(self, "Select Download Folder", initial_dir)
        if not save_path:
            self.download_status_updated.emit(download_id, "❌ Cancelled", 0)
            try:
                os.remove(torrent_path)
            except Exception:
                pass
            return

        item_widget = self.downloads_tab.items.get(download_id)

        def progress_callback(text, progress):
            self.download_status_updated.emit(download_id, text, progress)

        def run_torrent():
            result = download_torrent(
                torrent_path,
                save_path,
                progress_callback,
                item_widget.control_flags if item_widget else {"paused": False, "stopped": False},
                selected_file_indices=selected_indices,
            )
            self.download_finished.emit(download_id, result, save_path)
            # Cleanup temp torrent file
            try: os.remove(torrent_path)
            except: pass

        threading.Thread(target=run_torrent, daemon=True).start()

    def _prompt_torrent_file_choices(self, title: str, file_entries: list[dict]) -> list[int] | None:
        from ui.dialogs.torrent_file_selector_dialog import TorrentFileSelectorDialog

        dlg = TorrentFileSelectorDialog(title, file_entries, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        selected = dlg.selected_file_indices()
        return selected or None

    def _prompt_torrent_file_selection(
        self,
        source: str,
        title: str,
        list_torrent_files,
    ) -> list[dict] | None:
        progress = QProgressDialog("Loading torrent metadata...", "Cancel", 0, 0, self)
        progress.setWindowTitle("Preparing Torrent")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()

        cancel_flags = {"stopped": False}

        loop = QEventLoop(self)
        result: dict = {"files": None, "error": None}

        def on_cancel():
            cancel_flags["stopped"] = True
            try:
                progress.setLabelText("Cancelling...")
            except Exception:
                pass
            loop.quit()

        progress.canceled.connect(on_cancel)

        def status(text: str):
            try:
                QMetaObject.invokeMethod(
                    progress,
                    "setLabelText",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, text),
                )
            except Exception:
                pass

        def worker():
            try:
                files = list_torrent_files(
                    source,
                    status_callback=status,
                    cancel_flags=cancel_flags,
                )
                result["files"] = files
            except Exception as exc:
                if cancel_flags.get("stopped", False) and str(exc).lower().startswith("cancel"):
                    result["files"] = None
                else:
                    result["error"] = str(exc)
            finally:
                try:
                    QMetaObject.invokeMethod(loop, "quit", Qt.ConnectionType.QueuedConnection)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()
        loop.exec()

        try:
            progress.close()
        except Exception:
            pass

        if cancel_flags.get("stopped", False) and result.get("files") is None:
            return None

        error = result.get("error")
        if error:
            QMessageBox.warning(self, "Torrent Metadata Error", error)
            return None

        files = result.get("files") or []
        if not files:
            QMessageBox.warning(self, "Torrent Metadata Error", "No files found in torrent metadata.")
            return None

        return files

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
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = str(Path(sys.argv[0]).resolve().parent)
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

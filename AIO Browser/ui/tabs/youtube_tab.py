import os
import threading
from pathlib import Path

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from tools.ffmpeg_setup import ensure_ffmpeg

from ui.core.styles import get_colors
from ui.tabs.youtube import VideoTab, AudioTab

try:
    from core.youtube_downloader import YoutubeDownloader, get_video_info

    YOUTUBE_SUPPORTED = True
except ImportError:
    YOUTUBE_SUPPORTED = False


class YoutubeTab(QWidget):
    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.downloader = (
            YoutubeDownloader(self.update_progress) if YOUTUBE_SUPPORTED else None
        )
        self.initUI()

    def initUI(self):
        colors = get_colors()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab Widget for Video/Audio modes
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)

        # Create Video and Audio tabs
        self.video_tab = VideoTab(self)
        self.audio_tab = AudioTab(self)

        # Add tabs to tab widget
        self.tab_widget.addTab(self.video_tab, "Video")
        self.tab_widget.addTab(self.audio_tab, "Audio")

        main_layout.addWidget(self.tab_widget)

        # Progress Section (Hidden by default, overlays on top)
        self.progress_container = QFrame()
        self.progress_container.setObjectName("ProgressCard")
        self.progress_container.hide()
        self.progress_container.setStyleSheet(f"""
            QFrame#ProgressCard {{
                background-color: {colors['bg_secondary']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        self.progress_container.setFixedHeight(150)
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(20, 20, 20, 20)
        progress_layout.setSpacing(12)

        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet(
            f"color: {colors['text_primary']}; font-weight: 600; font-size: 14px;"
        )
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(30)
        progress_layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['accent_red']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #d32f2f;
            }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_download)
        progress_layout.addWidget(self.cancel_btn)

        main_layout.addWidget(self.progress_container)

        self.setLayout(main_layout)

    def update_progress(self, text, progress):
        """Callback for the downloader core."""
        # Ensure we are on the UI thread
        QMetaObject.invokeMethod(
            self,
            "_do_update_progress",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, text),
            Q_ARG(float, progress),
        )

    @pyqtSlot(str, float)
    def _do_update_progress(self, text, progress):
        self.status_label.setText(text)
        self.progress_bar.setValue(int(progress * 100))

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
        self.status_label.setText("Stopping...")
        self.cancel_btn.setEnabled(False)

    def start_download_flow(self, mode):
        if not YOUTUBE_SUPPORTED:
            QMessageBox.critical(
                self,
                "Error",
                "yt-dlp is not installed. Please run 'pip install yt-dlp' to use this feature.",
            )
            return

        # Get URL from the appropriate tab
        if mode == "video":
            url = self.video_tab.get_url()
            quality = self.video_tab.get_quality()
        else:  # audio
            url = self.audio_tab.get_url()
            quality = self.audio_tab.get_quality()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid YouTube URL.")
            return

        # Prepare UI
        self.video_tab.set_enabled(False)
        self.audio_tab.set_enabled(False)
        self.tab_widget.setEnabled(False)
        self.progress_container.show()
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Checking dependencies...")

        threading.Thread(
            target=self._run_pre_download_checks, args=(url, mode, quality), daemon=True
        ).start()

    def _run_pre_download_checks(self, url, mode, quality):
        # 1. Ensure FFmpeg
        if not ensure_ffmpeg(self.update_progress):
            QMetaObject.invokeMethod(
                self,
                "finalize_download",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "ERROR: FFmpeg is required but could not be installed."),
                Q_ARG(str, "N/A"),
            )
            return

        # 2. Proceed to directory selection on UI thread
        QMetaObject.invokeMethod(
            self,
            "_prompt_save_location",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, url),
            Q_ARG(str, mode),
            Q_ARG(str, quality),
        )

    @pyqtSlot(str, str, str)
    def _prompt_save_location(self, url, mode, quality):
        # Select save directory
        initial_dir = self.main_app.settings_manager.get("default_download_path", "")
        if not os.path.exists(initial_dir):
            initial_dir = str(Path.home() / "Downloads")

        save_path = QFileDialog.getExistingDirectory(
            self, "Select Save Folder", initial_dir
        )

        if not save_path:
            self.video_tab.set_enabled(True)
            self.audio_tab.set_enabled(True)
            self.tab_widget.setEnabled(True)
            self.progress_container.hide()
            return

        self.status_label.setText("Initializing...")

        # Run in thread
        threading.Thread(
            target=self.run_download, args=(url, save_path, mode, quality), daemon=True
        ).start()

    def run_download(self, url, save_path, mode, quality):
        try:
            # 1. Get info first (optional, for better UI)
            info = get_video_info(url)
            title = info["title"] if info else "YouTube Video"

            # 2. Start the actual download via downloader core
            result = self.downloader.download(
                url, save_path, mode=mode, quality=quality
            )

            # 3. Handle result back on UI thread
            QMetaObject.invokeMethod(
                self,
                "finalize_download",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, result),
                Q_ARG(str, title),
            )
        except Exception as e:
            QMetaObject.invokeMethod(
                self,
                "finalize_download",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"ERROR: {str(e)}"),
                Q_ARG(str, "Unknown"),
            )

    @pyqtSlot(str, str)
    def finalize_download(self, result, title):
        self.video_tab.set_enabled(True)
        self.audio_tab.set_enabled(True)
        self.tab_widget.setEnabled(True)

        if result == "SUCCESS":
            self.status_label.setText(f"✅ Downloaded: {title}")
            QTimer.singleShot(5000, self.progress_container.hide)

            # Optional: Show a small toast or notification
            msg = QMessageBox(self)
            msg.setWindowTitle("Download Finished")
            msg.setText(f"Successfully downloaded:\n{title}")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.show()
        elif result == "STOPPED":
            self.status_label.setText("❌ Download cancelled.")
            QTimer.singleShot(3000, self.progress_container.hide)
        else:
            self.status_label.setText(f"❌ Error occurred.")
            QMessageBox.critical(self, "Download Error", result)
            self.progress_container.hide()

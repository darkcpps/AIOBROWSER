import os
import threading
from pathlib import Path

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from tools.ffmpeg_setup import ensure_ffmpeg

from ui.core.styles import COLORS, get_colors

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
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title/Description
        info_label = QLabel("YouTube Downloader")
        info_label.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {colors['accent_primary']};"
        )
        layout.addWidget(info_label)

        desc_label = QLabel(
            "Enter a YouTube URL to download the video or extract high-quality MP3 audio."
        )
        desc_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 14px;")
        layout.addWidget(desc_label)

        # Input Section
        input_container = QFrame()
        input_container.setObjectName("Card")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        input_layout.addWidget(self.url_input)

        options_layout = QHBoxLayout()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Video (MP4)", "Audio (MP3)"])
        self.mode_selector.currentTextChanged.connect(self.update_quality_options)
        options_layout.addWidget(self.mode_selector)

        self.quality_selector = QComboBox()
        options_layout.addWidget(self.quality_selector)
        self.update_quality_options()

        self.download_btn = QPushButton("🚀 Start Download")
        self.download_btn.setFixedHeight(45)
        self.download_btn.clicked.connect(self.start_download_flow)
        options_layout.addWidget(self.download_btn, 1)

        input_layout.addLayout(options_layout)
        layout.addWidget(input_container)

        # Progress Section (Hidden by default)
        self.progress_container = QFrame()
        self.progress_container.setObjectName("Card")
        self.progress_container.hide()
        progress_layout = QVBoxLayout(self.progress_container)

        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet(
            f"color: {colors['text_primary']}; font-weight: 600;"
        )
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            f"background-color: {colors['accent_red']}; color: white;"
        )
        self.cancel_btn.clicked.connect(self.cancel_download)
        progress_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.progress_container)
        layout.addStretch()

        self.setLayout(layout)

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

    def update_quality_options(self):
        self.quality_selector.clear()
        if "Video" in self.mode_selector.currentText():
            self.quality_selector.addItems(
                ["Best Available", "1080p", "720p", "480p", "360p"]
            )
        else:
            self.quality_selector.addItems(["320kbps", "192kbps", "128kbps"])

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
        self.status_label.setText("Stopping...")
        self.cancel_btn.setEnabled(False)

    def start_download_flow(self):
        if not YOUTUBE_SUPPORTED:
            QMessageBox.critical(
                self,
                "Error",
                "yt-dlp is not installed. Please run 'pip install yt-dlp' to use this feature.",
            )
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid YouTube URL.")
            return

        # Prepare UI
        self.download_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.mode_selector.setEnabled(False)
        self.progress_container.show()
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Checking dependencies...")
        self.quality_selector.setEnabled(False)

        threading.Thread(
            target=self._run_pre_download_checks, args=(url,), daemon=True
        ).start()

    def _run_pre_download_checks(self, url):
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
        )

    @pyqtSlot(str)
    def _prompt_save_location(self, url):
        mode = "audio" if "Audio" in self.mode_selector.currentText() else "video"
        quality = self.quality_selector.currentText()

        # Select save directory
        initial_dir = self.main_app.settings_manager.get("default_download_path", "")
        if not os.path.exists(initial_dir):
            initial_dir = str(Path.home() / "Downloads")

        save_path = QFileDialog.getExistingDirectory(
            self, "Select Save Folder", initial_dir
        )

        if not save_path:
            self.download_btn.setEnabled(True)
            self.url_input.setEnabled(True)
            self.mode_selector.setEnabled(True)
            self.quality_selector.setEnabled(True)
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
        self.download_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.mode_selector.setEnabled(True)
        self.quality_selector.setEnabled(True)

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

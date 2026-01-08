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

        # Video Tab
        self.video_tab = QWidget()
        video_layout = QVBoxLayout(self.video_tab)
        video_layout.setContentsMargins(40, 40, 40, 40)
        video_layout.setSpacing(20)

        # Video Header
        video_header = QHBoxLayout()
        video_title_layout = QVBoxLayout()

        video_title = QLabel("📹  Video Download")
        video_title.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {colors['text_primary']};"
        )
        video_title_layout.addWidget(video_title)

        video_subtitle = QLabel("Download YouTube videos in your preferred quality.")
        video_subtitle.setStyleSheet(f"font-size: 14px; color: {colors['text_secondary']};")
        video_title_layout.addWidget(video_subtitle)
        video_header.addLayout(video_title_layout)
        video_header.addStretch()
        video_layout.addLayout(video_header)

        # Video URL Input Card
        video_input_card = QFrame()
        video_input_card.setObjectName("Card")
        video_input_card.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {colors['bg_secondary']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        video_input_layout = QVBoxLayout(video_input_card)
        video_input_layout.setContentsMargins(20, 20, 20, 20)
        video_input_layout.setSpacing(15)

        self.video_url_input = QLineEdit()
        self.video_url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.video_url_input.setFixedHeight(45)
        self.video_url_input.setStyleSheet(
            f"background-color: {colors['bg_primary']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 0 15px;"
        )
        video_input_layout.addWidget(self.video_url_input)

        video_layout.addWidget(video_input_card)

        # Video Quality Selection Card
        video_quality_card = QFrame()
        video_quality_card.setObjectName("QualityCard")
        video_quality_card.setStyleSheet(f"""
            QFrame#QualityCard {{
                background-color: {colors['bg_secondary']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        video_quality_layout = QVBoxLayout(video_quality_card)
        video_quality_layout.setContentsMargins(20, 20, 20, 20)
        video_quality_layout.setSpacing(15)

        quality_label = QLabel("Select Video Quality")
        quality_label.setStyleSheet(f"color: {colors['text_primary']}; font-weight: 700; font-size: 16px;")
        video_quality_layout.addWidget(quality_label)

        # Video quality buttons grid
        self.video_quality_group = QButtonGroup(self)
        video_qualities = ["Best Available", "1080p", "720p", "480p", "360p"]
        video_buttons_layout = QGridLayout()
        video_buttons_layout.setSpacing(10)

        for idx, quality in enumerate(video_qualities):
            btn = QPushButton(quality)
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {colors['bg_primary']};
                    color: {colors['text_primary']};
                    border: 2px solid {colors['border']};
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: {colors['bg_card_hover']};
                    border: 2px solid {colors['accent_primary']};
                }}
                QPushButton:checked {{
                    background: {colors['accent_primary']};
                    color: white;
                    border: 2px solid {colors['accent_primary']};
                }}
            """)
            self.video_quality_group.addButton(btn)
            row = idx // 3
            col = idx % 3
            video_buttons_layout.addWidget(btn, row, col)

        self.video_quality_group.buttons()[0].setChecked(True)
        video_quality_layout.addLayout(video_buttons_layout)
        video_layout.addWidget(video_quality_card)

        # Video Download Button
        self.video_download_btn = QPushButton("🚀  Start Download")
        self.video_download_btn.setFixedHeight(50)
        self.video_download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.video_download_btn.clicked.connect(lambda: self.start_download_flow("video"))
        video_layout.addWidget(self.video_download_btn)
        video_layout.addStretch()

        # Audio Tab
        self.audio_tab = QWidget()
        audio_layout = QVBoxLayout(self.audio_tab)
        audio_layout.setContentsMargins(40, 40, 40, 40)
        audio_layout.setSpacing(20)

        # Audio Header
        audio_header = QHBoxLayout()
        audio_title_layout = QVBoxLayout()

        audio_title = QLabel("🎵  Audio Download")
        audio_title.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {colors['text_primary']};"
        )
        audio_title_layout.addWidget(audio_title)

        audio_subtitle = QLabel("Extract high-quality MP3 audio from YouTube videos.")
        audio_subtitle.setStyleSheet(f"font-size: 14px; color: {colors['text_secondary']};")
        audio_title_layout.addWidget(audio_subtitle)
        audio_header.addLayout(audio_title_layout)
        audio_header.addStretch()
        audio_layout.addLayout(audio_header)

        # Audio URL Input Card
        audio_input_card = QFrame()
        audio_input_card.setObjectName("Card")
        audio_input_card.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {colors['bg_secondary']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        audio_input_layout = QVBoxLayout(audio_input_card)
        audio_input_layout.setContentsMargins(20, 20, 20, 20)
        audio_input_layout.setSpacing(15)

        self.audio_url_input = QLineEdit()
        self.audio_url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.audio_url_input.setFixedHeight(45)
        self.audio_url_input.setStyleSheet(
            f"background-color: {colors['bg_primary']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 0 15px;"
        )
        audio_input_layout.addWidget(self.audio_url_input)

        audio_layout.addWidget(audio_input_card)

        # Audio Quality Selection Card
        audio_quality_card = QFrame()
        audio_quality_card.setObjectName("QualityCard")
        audio_quality_card.setStyleSheet(f"""
            QFrame#QualityCard {{
                background-color: {colors['bg_secondary']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        audio_quality_layout = QVBoxLayout(audio_quality_card)
        audio_quality_layout.setContentsMargins(20, 20, 20, 20)
        audio_quality_layout.setSpacing(15)

        bitrate_label = QLabel("Select Audio Bitrate")
        bitrate_label.setStyleSheet(f"color: {colors['text_primary']}; font-weight: 700; font-size: 16px;")
        audio_quality_layout.addWidget(bitrate_label)

        # Audio bitrate buttons
        self.audio_quality_group = QButtonGroup(self)
        audio_qualities = ["320kbps", "192kbps", "128kbps"]
        audio_buttons_layout = QHBoxLayout()
        audio_buttons_layout.setSpacing(10)

        for quality in audio_qualities:
            btn = QPushButton(quality)
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {colors['bg_primary']};
                    color: {colors['text_primary']};
                    border: 2px solid {colors['border']};
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: {colors['bg_card_hover']};
                    border: 2px solid {colors['accent_primary']};
                }}
                QPushButton:checked {{
                    background: {colors['accent_primary']};
                    color: white;
                    border: 2px solid {colors['accent_primary']};
                }}
            """)
            self.audio_quality_group.addButton(btn)
            audio_buttons_layout.addWidget(btn)

        self.audio_quality_group.buttons()[0].setChecked(True)
        audio_quality_layout.addLayout(audio_buttons_layout)
        audio_layout.addWidget(audio_quality_card)

        # Audio Download Button
        self.audio_download_btn = QPushButton("🚀  Start Download")
        self.audio_download_btn.setFixedHeight(50)
        self.audio_download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.audio_download_btn.clicked.connect(lambda: self.start_download_flow("audio"))
        audio_layout.addWidget(self.audio_download_btn)
        audio_layout.addStretch()

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

        # Get URL from the appropriate tab's input field
        if mode == "video":
            url = self.video_url_input.text().strip()
        else:  # audio
            url = self.audio_url_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid YouTube URL.")
            return

        # Get selected quality from appropriate button group
        if mode == "video":
            selected_btn = self.video_quality_group.checkedButton()
            quality = selected_btn.text() if selected_btn else "Best Available"
        else:  # audio
            selected_btn = self.audio_quality_group.checkedButton()
            quality = selected_btn.text() if selected_btn else "320kbps"

        # Prepare UI
        self.video_download_btn.setEnabled(False)
        self.audio_download_btn.setEnabled(False)
        self.video_url_input.setEnabled(False)
        self.audio_url_input.setEnabled(False)
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
            self.video_download_btn.setEnabled(True)
            self.audio_download_btn.setEnabled(True)
            self.video_url_input.setEnabled(True)
            self.audio_url_input.setEnabled(True)
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
        self.video_download_btn.setEnabled(True)
        self.audio_download_btn.setEnabled(True)
        self.video_url_input.setEnabled(True)
        self.audio_url_input.setEnabled(True)
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

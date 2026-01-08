from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.styles import get_colors
from ui.tabs.youtube import VideoTab
from ui.tabs.youtube_tab import YoutubeTab


class VideoHub(QWidget):
    """Top-level Video hub containing video-related subtabs (e.g., YouTube Downloader)"""

    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.initUI()

    def initUI(self):
        colors = get_colors()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab widget for video subtabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)

        # Create a hidden Youtube helper instance to host the download logic for video
        self._yt_helper = YoutubeTab(self.main_app)
        self._yt_helper.hide()

        # Add YouTube Video subtab (uses the real downloader via the hidden helper)
        self.youtube_video_tab = VideoTab(self._yt_helper)
        self.tab_widget.addTab(self.youtube_video_tab, "YouTube")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

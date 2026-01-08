from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.styles import get_colors
from ui.tabs.monochrome_tab import MonochromeTab
from ui.tabs.youtube import AudioTab
from ui.tabs.youtube_tab import YoutubeTab


class AudioHub(QWidget):
    """Top-level Audio hub containing audio-related subtabs (e.g., Monochrome)"""

    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.initUI()

    def initUI(self):
        colors = get_colors()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab widget for audio subtabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)

        # Create a hidden Youtube helper instance to host the download logic for audio
        self._yt_helper = YoutubeTab(self.main_app)
        self._yt_helper.hide()

        # Add YouTube Audio subtab (uses the real downloader via the hidden helper)
        self.youtube_audio_tab = AudioTab(self._yt_helper)
        self.tab_widget.addTab(self.youtube_audio_tab, "YouTube (Audio)")

        # Add Monochrome as an audio subtab
        self.monochrome_tab = MonochromeTab(self.main_app)
        self.tab_widget.addTab(self.monochrome_tab, "Monochrome")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

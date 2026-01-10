from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from ui.core.styles import get_colors
from ui.core.components import InfoBanner


class VideoTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        colors = get_colors()
        video_layout = QVBoxLayout(self)
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

        video_title_layout.addWidget(
            InfoBanner(
                title="",
                body_lines=["Download YouTube videos in your preferred quality."],
                icon="💡",
                object_name="YouTubeVideoInfoBanner",
                compact=True,
            )
        )
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
        # Pass URL and quality from the visible tab to the helper to avoid hidden-tab mismatch
        self.video_download_btn.clicked.connect(lambda: self.parent.start_download_flow("video", self.get_url(), self.get_quality()))
        video_layout.addWidget(self.video_download_btn)
        video_layout.addStretch()

        self.setLayout(video_layout)

    def get_url(self):
        return self.video_url_input.text().strip()

    def get_quality(self):
        selected_btn = self.video_quality_group.checkedButton()
        return selected_btn.text() if selected_btn else "Best Available"

    def set_enabled(self, enabled):
        self.video_url_input.setEnabled(enabled)
        self.video_download_btn.setEnabled(enabled)

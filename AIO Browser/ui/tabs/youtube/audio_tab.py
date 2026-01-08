from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *
from ui.core.styles import get_colors


class AudioTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        colors = get_colors()
        audio_layout = QVBoxLayout(self)
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
        # Pass URL and quality from the visible tab to the helper to avoid hidden-tab mismatch
        self.audio_download_btn.clicked.connect(lambda: self.parent.start_download_flow("audio", self.get_url(), self.get_quality()))
        audio_layout.addWidget(self.audio_download_btn)
        audio_layout.addStretch()

        self.setLayout(audio_layout)

    def get_url(self):
        return self.audio_url_input.text().strip()

    def get_quality(self):
        selected_btn = self.audio_quality_group.checkedButton()
        return selected_btn.text() if selected_btn else "320kbps"

    def set_enabled(self, enabled):
        self.audio_url_input.setEnabled(enabled)
        self.audio_download_btn.setEnabled(enabled)

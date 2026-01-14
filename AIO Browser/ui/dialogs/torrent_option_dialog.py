from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
)
from ui.core.styles import COLORS

class TorrentOptionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.choice = None  # 'aio' or 'own'
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Torrent Client Selection")
        self.setFixedSize(500, 350)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main container with border radius and styling
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setStyleSheet(f"""
            QFrame#Container {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 20px;
            }}
        """)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Title
        title = QLabel("Choose Your Torrent Client")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 800;
            color: {COLORS["text_primary"]};
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "It looks like this is your first time downloading a torrent or magnet link. "
            "Would you like to use the built-in AIO Browser BitTorrent client, or would you "
            "prefer to use your own installed client?"
        )
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc)

        # Buttons Container
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        # AIO Browser Button
        self.aio_btn = QPushButton("Use AIO Browser")
        self.aio_btn.setFixedHeight(100)
        self.aio_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aio_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_card"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
                border: 1px solid {COLORS["accent_primary"]};
            }}
        """)
        self.aio_btn.clicked.connect(self.select_aio)
        btn_layout.addWidget(self.aio_btn, 1)

        # Own Client Button
        self.own_btn = QPushButton("Use My Own Client")
        self.own_btn.setFixedHeight(100)
        self.own_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.own_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_card"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
                color: {COLORS["text_primary"]};
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
                border: 1px solid {COLORS["accent_primary"]};
            }}
        """)
        self.own_btn.clicked.connect(self.select_own)
        btn_layout.addWidget(self.own_btn, 1)

        main_layout.addLayout(btn_layout)

        # Information footer
        footer = QLabel("You can change this anytime in Settings.")
        footer.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)

        # Layout for the shadow effect
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(self.container)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.container.setGraphicsEffect(shadow)

    def select_aio(self):
        self.choice = 'aio'
        self.accept()

    def select_own(self):
        self.choice = 'own'
        self.accept()

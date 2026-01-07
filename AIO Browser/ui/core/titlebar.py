from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.core.styles import COLORS


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.start_pos = None
        self.pressing = False
        self.maximized = False

        # Default fixed height for titlebar
        self.setFixedHeight(35)

        self.initUI()
        self.update_styles()

    def initUI(self):
        # Main layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # Title Label
        self.title_label = QLabel("🎮 AIO Browser")
        self.title_label.setObjectName("TitleLabel")
        self.layout.addWidget(self.title_label)

        self.layout.addStretch()

        # Window Controls Container
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(0)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        # Minimize Button
        self.btn_minimize = QPushButton("−")
        self.btn_minimize.setFixedSize(45, 35)
        self.btn_minimize.clicked.connect(self.minimize_window)
        self.controls_layout.addWidget(self.btn_minimize)

        # Maximize/Restore Button
        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setFixedSize(45, 35)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.controls_layout.addWidget(self.btn_maximize)

        # Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(45, 35)
        self.btn_close.clicked.connect(self.close_window)
        self.controls_layout.addWidget(self.btn_close)

        self.layout.addLayout(self.controls_layout)

    def update_styles(self):
        """Update styles based on current theme COLORS"""
        # Background and border
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["bg_secondary"]};
                border-bottom: 1px solid {COLORS["border"]};
            }}
            QLabel#TitleLabel {{
                color: {COLORS["text_primary"]};
                font-weight: bold;
                font-size: 13px;
                border: none;
                background: transparent;
            }}
            QPushButton {{
                background-color: transparent;
                color: {COLORS["text_secondary"]};
                border: none;
                border-radius: 0px;
                font-family: 'Segoe UI Symbol', 'Segoe UI', sans-serif;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
                color: {COLORS["text_primary"]};
            }}
        """)

        # Special style for close button hover
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS["text_secondary"]};
                border: none;
                border-radius: 0px;
                font-family: 'Segoe UI Symbol', 'Segoe UI', sans-serif;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_red"]};
                color: white;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressing = True
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.pressing and not self.maximized:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.pressing = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()

    def minimize_window(self):
        self.parent.showMinimized()

    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximized = False
            self.btn_maximize.setText("□")
        else:
            self.parent.showMaximized()
            self.maximized = True
            self.btn_maximize.setText("❐")

    def close_window(self):
        self.parent.close()

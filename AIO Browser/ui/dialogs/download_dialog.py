# download_ui.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar, 
                             QWidget, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QColor
from ui.core.styles import COLORS

class DownloadDialog(QDialog):
    def __init__(self, game_title, parent=None):
        super().__init__(parent)
        self.game_title = game_title
        self.control_flags = {"paused": False, "stopped": False}
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Preparing Download")
        self.setFixedSize(550, 300)
        # Frameless and modern
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 20px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        
        # Header / Title
        display_title = self.game_title[:45] + "..." if len(self.game_title) > 45 else self.game_title
        self.title_label = QLabel(f"Downloading {display_title}")
        self.title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 800;
            color: {COLORS["text_primary"]};
        """)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Progress section
        self.progress_label = QLabel("Initializing connection...")
        self.progress_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS["text_secondary"]};
        """)
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS["bg_secondary"]};
                border-radius: 6px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {COLORS["accent_primary"]}, 
                    stop:1 {COLORS["accent_secondary"]});
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Control buttons container
        self.btn_frame = QWidget()
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(15)
        
        self.pause_btn = QPushButton("⏸  Pause")
        self.pause_btn.setFixedHeight(45)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_card"]};
                color: white;
                border: 1px solid {COLORS["border"]};
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
            }}
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        
        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["accent_red"]};
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_red_hover"]};
            }}
        """)
        self.stop_btn.clicked.connect(self.stop_download)
        
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        self.btn_frame.hide() # Hidden until download actually starts
        
        layout.addWidget(self.btn_frame)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(shadow)
    
    def toggle_pause(self):
        self.control_flags["paused"] = not self.control_flags["paused"]
        if self.control_flags["paused"]:
            self.pause_btn.setText("▶  Resume")
            self.progress_label.setText("⏸  Download Paused")
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["accent_green"]};
                    color: white;
                    font-weight: bold;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["accent_green_hover"]};
                }}
            """)
        else:
            self.pause_btn.setText("⏸  Pause")
            self.progress_label.setText("▶  Resuming...")
            self.pause_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["bg_card"]};
                    color: white;
                    border: 1px solid {COLORS["border"]};
                    font-weight: bold;
                    border-radius: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["bg_card_hover"]};
                }}
            """)
    
    def stop_download(self):
        self.control_flags["stopped"] = True
        self.pause_btn.setEnabled(False)
        self.progress_label.setText("⏹  Stopping...")
    
    def show_controls(self):
        self.btn_frame.show()

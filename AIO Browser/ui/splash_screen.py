# splash_screen.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from ui.styles import COLORS

class SplashScreen(QWidget):
    def __init__(self, on_finished_callback):
        super().__init__()
        self.on_finished_callback = on_finished_callback
        self.initUI()
        
    def initUI(self):
        # 1. Window Setup
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 2. Outer Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20) # Space for shadow
        
        # 3. Main Container (Rounded)
        self.main_container = QWidget()
        self.main_container.setObjectName("SplashContainer")
        self.main_container.setFixedSize(400, 300)
        self.main_container.setStyleSheet(f"""
            QWidget#SplashContainer {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 25px;
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        
        # 4. Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        self.main_container.setGraphicsEffect(shadow)
        
        # 5. Content Layout (inside container)
        content_layout = QVBoxLayout(self.main_container)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 6. UI Elements
        # Icon
        icon_label = QLabel("🎮")
        icon_label.setStyleSheet(f"font-size: 72px; color: {COLORS['accent_primary']};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(icon_label)
        
        # Title (typed effect)
        self.splash_title = QLabel("")
        self.splash_title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLORS['text_primary']}; margin: 15px 0;")
        self.splash_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.splash_title)
        
        # Subtitle
        self.splash_subtitle = QLabel("")
        self.splash_subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        self.splash_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.splash_subtitle)
        
        content_layout.addStretch()
        
        # Version
        version_label = QLabel("Early Access - V1")
        version_label.setStyleSheet(f"font-size: 10px; color: {COLORS['text_secondary']};")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(version_label)
        
        outer_layout.addWidget(self.main_container)
        
        # 7. Position & Show
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        
    def start_animation(self):
        self.show()
        # Start typing animation
        self.type_animation("AIO Browser", self.splash_title, 0)
    
    def type_animation(self, text, label, index):
        if index <= len(text):
            label.setText(text[:index] + "▌")
            QTimer.singleShot(50, lambda: self.type_animation(text, label, index + 1))
        else:
            label.setText(text)
            if label == self.splash_title:
                QTimer.singleShot(200, lambda: self.type_animation("The All-In-One Browser", self.splash_subtitle, 0))
            else:
                QTimer.singleShot(600, self.finish)
    
    def finish(self):
        self.close()
        if self.on_finished_callback:
            self.on_finished_callback()

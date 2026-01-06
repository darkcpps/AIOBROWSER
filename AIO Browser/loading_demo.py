# loading_demo.py
# Standalone demo to showcase the cool loading animation

import math
import sys

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

COLORS = {
    "bg_primary": "#0F111A",
    "bg_secondary": "#090B13",
    "bg_card": "#1A1F35",
    "accent_primary": "#7C3AED",
    "accent_secondary": "#A78BFA",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "border": "#1E293B",
}


class SpinnerWidget(QWidget):
    """Custom rotating spinner with smooth animation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(80, 80)

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16)  # ~60 FPS

    def rotate(self):
        self.angle = (self.angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center point
        center_x, center_y = self.width() // 2, self.height() // 2

        # Draw rotating arc with solid color
        pen = QPen(
            QColor(COLORS["accent_primary"]),
            4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(pen)
        # Rotate the arc itself by changing the start angle
        start_angle = self.angle * 16  # Qt uses 1/16th degree units
        span_angle = 270 * 16  # 270 degrees arc
        painter.drawArc(10, 10, 60, 60, start_angle, span_angle)

        # Draw a second arc with secondary color for gradient effect
        pen2 = QPen(
            QColor(COLORS["accent_secondary"]),
            4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(pen2)
        painter.drawArc(10, 10, 60, 60, start_angle + 200 * 16, 70 * 16)

    def stop(self):
        self.timer.stop()


class ParticleWidget(QWidget):
    """Animated particles floating around"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.init_particles()

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(30)  # ~33 FPS

    def init_particles(self):
        import random

        for _ in range(15):
            self.particles.append(
                {
                    "x": random.randint(0, 400),
                    "y": random.randint(0, 300),
                    "vx": random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-0.8, -0.3),
                    "size": random.randint(2, 5),
                    "opacity": random.randint(100, 200),
                }
            )

    def update_particles(self):
        import random

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["opacity"] -= 1

            # Reset particle if it fades out or goes off screen
            if p["opacity"] <= 0 or p["y"] < -10:
                p["x"] = random.randint(0, self.width())
                p["y"] = self.height() + 10
                p["vx"] = random.uniform(-0.5, 0.5)
                p["vy"] = random.uniform(-0.8, -0.3)
                p["opacity"] = random.randint(150, 255)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for p in self.particles:
            color = QColor(COLORS["accent_primary"])
            color.setAlpha(max(0, min(255, int(p["opacity"]))))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(p["x"]), int(p["y"]), p["size"], p["size"])

    def stop(self):
        self.timer.stop()


class LoadingWidget(QWidget):
    def __init__(self, text="Searching"):
        super().__init__()
        self.text = text
        self.dot_count = 0
        self.initUI()

        # Dot animation timer
        self.dot_timer = QTimer()
        self.dot_timer.timeout.connect(self.animate_dots)
        self.dot_timer.start(400)

        # Fade in animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.start()

    def initUI(self):
        # Use a grid layout to overlay particles and container
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Glass morphism container
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS["bg_secondary"]},
                    stop:1 {COLORS["bg_primary"]});
                border: 2px solid {COLORS["border"]};
                border-radius: 20px;
                padding: 40px;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setSpacing(25)

        # Particle background
        self.particles = ParticleWidget()
        self.particles.setFixedSize(400, 300)

        # Spinner
        self.spinner = SpinnerWidget()

        # Subtext with pulsing effect
        self.subtext = QLabel("Please wait while we fetch results...")
        self.subtext.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS["text_secondary"]};
            font-weight: 500;
        """)
        self.subtext.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Pulsing animation for subtext
        self.subtext_opacity = QGraphicsOpacityEffect(self.subtext)
        self.subtext.setGraphicsEffect(self.subtext_opacity)
        self.pulse_anim = QPropertyAnimation(self.subtext_opacity, b"opacity")
        self.pulse_anim.setDuration(1500)
        self.pulse_anim.setStartValue(0.5)
        self.pulse_anim.setEndValue(1.0)
        self.pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.start()

        # Main text with dots
        self.text_label = QLabel(self.text)
        self.text_label.setStyleSheet(f"""
            font-size: 18px;
            color: {COLORS["text_primary"]};
            letter-spacing: 1px;
            font-weight: bold;
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add widgets to container
        container_layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.text_label)
        container_layout.addWidget(self.subtext)

        # Add both to the same grid cell to overlay them
        layout.addWidget(self.particles, 0, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(container, 0, 0, Qt.AlignmentFlag.AlignCenter)

        # Ensure container stays on top of particles
        container.raise_()

        self.setLayout(layout)

    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_label.setText(f"{self.text}{dots}")

    def stop(self):
        self.dot_timer.stop()
        self.pulse_anim.stop()
        self.spinner.stop()
        self.particles.stop()

        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.start()


class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cool Loading Animation Demo")
        self.setGeometry(100, 100, 800, 600)

        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS["bg_primary"]};
            }}
            QPushButton {{
                background-color: {COLORS["accent_primary"]};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_secondary"]};
            }}
        """)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("🎨 Cool Loading Animation Demo")
        title.setStyleSheet(f"""
            font-size: 28px;
            color: {COLORS["text_primary"]};
            font-weight: bold;
            margin-bottom: 20px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Description
        desc = QLabel(
            "This is the new loading animation for the AIO Browser search feature!"
        )
        desc.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS["text_secondary"]};
            margin-bottom: 30px;
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(desc)

        # Loading widget
        self.loading = LoadingWidget("Searching for games")
        layout.addWidget(self.loading)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(15)

        restart_btn = QPushButton("🔄 Restart Animation")
        restart_btn.clicked.connect(self.restart_animation)

        stop_btn = QPushButton("⏹ Stop Animation")
        stop_btn.clicked.connect(self.loading.stop)

        button_layout.addWidget(restart_btn)
        button_layout.addWidget(stop_btn)

        layout.addSpacing(30)
        layout.addLayout(button_layout)

    def restart_animation(self):
        # Remove old loading widget
        old_loading = self.loading
        old_loading.stop()
        old_loading.deleteLater()

        # Create new loading widget
        self.loading = LoadingWidget("Searching for games")
        self.centralWidget().layout().insertWidget(2, self.loading)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set font
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = DemoWindow()
    window.show()

    sys.exit(app.exec())

# components.py
import math
import random
import io
import requests
import webbrowser
import threading
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PIL import Image
from ui.core.styles import COLORS

# =========================================================================
# ANIMATED LOADING WIDGET WITH COOL EFFECTS
# =========================================================================
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

    def initUI(self):
        # Use a grid layout to overlay particles and container
        # This keeps the loading animation compact and at the top
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Align content to the top so it's directly under the search bar
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
        # Particles first (bottom layer), then container (top layer)
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

# =========================================================================
# GAME PATCHER CARD (Used in Patcher Tab)
# =========================================================================
class GamePatcherCard(QFrame):
    def __init__(self, game, type="CreamAPI", patch_callback=None, revert_callback=None, parent=None):
        super().__init__(parent)
        self.game = game
        self.type = type
        self.patch_callback = patch_callback
        self.revert_callback = revert_callback
        self.initUI()

    def initUI(self):
        self.setObjectName("SteamCard")
        self.setFixedHeight(85)
        self.setStyleSheet(f"""
            QFrame#SteamCard {{
                background-color: {COLORS["bg_card"]};
                border-radius: 12px;
                border: 1px solid {COLORS["border"]};
            }}
            QFrame#SteamCard:hover {{
                border: 1px solid {COLORS["accent_primary"]};
                background-color: #1E243A;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 25, 0)
        layout.setSpacing(15)

        # Game Image (if available)
        if self.game.get("image"):
            import requests
            img_container = QLabel()
            img_container.setFixedSize(50, 50)
            img_container.setStyleSheet("border-radius: 6px; background: #222;")
            def load_img():
                try:
                    res = requests.get(self.game["image"], timeout=5)
                    pixmap = QPixmap()
                    pixmap.loadFromData(res.content)
                    QMetaObject.invokeMethod(img_container, "setPixmap", Qt.ConnectionType.QueuedConnection, Q_ARG(QPixmap, pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)))
                except: pass
            import threading
            threading.Thread(target=load_img, daemon=True).start()
            layout.addWidget(img_container)
        
        # Info
        info = QVBoxLayout(); info.setAlignment(Qt.AlignmentFlag.AlignVCenter); info.setSpacing(2)
        name_text = self.game["name"]
        if len(name_text) > 40: name_text = name_text[:37] + "..."
        name = QLabel(name_text); name.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
        info.addWidget(name)
        
        meta_layout = QHBoxLayout(); meta_layout.setSpacing(15)
        id_lbl = QLabel(f"🆔 {self.game['id']}"); id_lbl.setStyleSheet("color: #6366F1; font-weight: bold; font-size: 11px; background: transparent;")
        meta_layout.addWidget(id_lbl)
        
        install_path = self.game.get("install_dir", "Remote / Steam Store")
        if len(install_path) > 40: install_path = "..." + install_path[-37:]
        path_lbl = QLabel(f"📁 {install_path}"); path_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        meta_layout.addWidget(path_lbl); meta_layout.addStretch()
        info.addLayout(meta_layout)
        layout.addLayout(info, 1)
        
        # Actions
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
        # Only show revert for installed games or Goldberg
        if self.game.get("install_dir"):
            revert_btn = QPushButton("Revert"); revert_btn.setFixedSize(80, 32); revert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            revert_btn.setStyleSheet(f"QPushButton {{ background: {COLORS['bg_secondary']}; color: {COLORS['text_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }} QPushButton:hover {{ background: #ff4444; color: white; }}")
            revert_btn.clicked.connect(lambda: self.revert_callback(self.game))
            btn_layout.addWidget(revert_btn)
        
        patch_btn = QPushButton("Patch"); patch_btn.setFixedSize(80, 32); patch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        patch_btn.setStyleSheet(f"QPushButton {{ background: {COLORS['accent_primary']}; color: white; font-weight: bold; border-radius: 6px; }} QPushButton:hover {{ background: {COLORS['accent_secondary']}; }}")
        patch_btn.clicked.connect(lambda: self.patch_callback(self.game))
        btn_layout.addWidget(patch_btn)
        layout.addLayout(btn_layout)


# =========================================================================
# GAME CARD WIDGET
# =========================================================================
class GameCardWidget(QFrame):
    def __init__(self, game, game_type="direct", parent=None, delay=0):
        super().__init__(parent)
        self.game = game
        self.game_type = game_type
        self.parent = parent
        self.setObjectName("Card")
        self.initUI()

        # Entrance Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.group = QParallelAnimationGroup(self)

        # Fade In
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(600)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide In
        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(600)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self.group.addAnimation(self.fade_anim)
        self.group.finished.connect(self.on_entrance_finished)

        # We start the slide relative to the current layout pos
        QTimer.singleShot(delay, self.start_entrance_animation)

    def start_entrance_animation(self):
        start_pos = self.pos()
        self.slide_anim.setStartValue(QPoint(start_pos.x(), start_pos.y() + 50))
        self.slide_anim.setEndValue(start_pos)
        self.group.start()

    def on_entrance_finished(self):
        # Swap opacity effect for shadow effect now that entrance is done
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)

        # Re-enable hover signals/checks if needed
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def initUI(self):
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 20, 12)
        layout.setSpacing(20)

        # Image with container
        self.img_container = QWidget()
        self.img_container.setFixedSize(90, 125)
        img_container_layout = QVBoxLayout(self.img_container)
        img_container_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setFixedSize(90, 125)
        self.image_label.setStyleSheet(f"""
            background-color: {COLORS["bg_secondary"]};
            border-radius: 10px;
            font-size: 28px;
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("🎮")
        img_container_layout.addWidget(self.image_label)

        layout.addWidget(self.img_container)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        self.title_label = QLabel(self.game["title"])
        self.title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 800;
            color: {COLORS["text_primary"]};
            background-color: transparent;
        """)
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        # Metadata / Badges
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(10)

        source_label = QLabel(f"📍 {self.game.get('source', 'Unknown')}")
        source_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 500; background-color: transparent;"
        )
        badge_layout.addWidget(source_label)

        if self.game.get("size"):
            size_label = QLabel(f"📦 {self.game['size']}")
            size_label.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 500; background-color: transparent;"
            )
            badge_layout.addWidget(size_label)

        badge_layout.addStretch()
        info_layout.addLayout(badge_layout)
        info_layout.addStretch()

        layout.addLayout(info_layout, 1)

        # Action Button
        if self.game_type == "direct":
            btn_text = "Download"
            btn_color = COLORS["accent_primary"]
            btn_hover = COLORS["accent_secondary"]
            btn_icon = "📥"
            callback = self.start_direct_download
        else:
            has_magnet = self.game.get("magnet")
            btn_text = "Magnet Link" if has_magnet else "Visit Page"
            btn_color = COLORS["accent_green"]
            btn_hover = COLORS["accent_green_hover"]
            btn_icon = "🧲" if has_magnet else "🔗"
            callback = self.open_torrent_link

        self.download_btn = QPushButton(f"{btn_icon}  {btn_text}")
        self.download_btn.setFixedSize(150, 45)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)
        self.download_btn.clicked.connect(callback)
        layout.addWidget(self.download_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.setLayout(layout)

        # Load image in background
        if self.game.get("image"):
            threading.Thread(target=self.load_image, daemon=True).start()

    def enterEvent(self, event):
        if hasattr(self, "shadow") and self.graphicsEffect() == self.shadow:
            self.shadow.setBlurRadius(30)
            self.shadow.setColor(QColor(124, 58, 237, 40))  # Accent primary glow
            self.shadow.setYOffset(8)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, "shadow") and self.graphicsEffect() == self.shadow:
            self.shadow.setBlurRadius(20)
            self.shadow.setColor(QColor(0, 0, 0, 80))
            self.shadow.setYOffset(4)
        super().leaveEvent(event)

    def load_image(self):
        try:
            response = requests.get(self.game["image"], timeout=5)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((80, 110), Image.Resampling.LANCZOS)

            if img.mode == "RGB":
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            elif img.mode == "RGBA":
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
            else:
                img = img.convert("RGB")
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(qimg)
            QMetaObject.invokeMethod(self, "set_pixmap", Qt.ConnectionType.QueuedConnection, Q_ARG(QPixmap, pixmap))
        except:
            pass

    @pyqtSlot(QPixmap)
    def set_pixmap(self, pixmap):
        self.image_label.setPixmap(pixmap.scaled(80, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_label.setText("")

    def start_direct_download(self):
        # We'll use a signal or callback here usually, but for now we follow the existing pattern
        if hasattr(self.parent, 'initiate_anker_download'):
            self.parent.initiate_anker_download(self.game)

    def open_torrent_link(self):
        has_magnet = self.game.get("magnet")
        url = self.game["magnet"] if has_magnet else self.game["link"]
        webbrowser.open(url)


# =========================================================================
# ANIMATED STACKED WIDGET (FADING)
# =========================================================================
class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.p_opacity = 1.0
        self.anim = QPropertyAnimation(self, b"opacity")
        self.anim.setDuration(400)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.opacity_effect = None

    @pyqtProperty(float)
    def opacity(self):
        return self.p_opacity

    @opacity.setter
    def opacity(self, value):
        self.p_opacity = value
        if self.opacity_effect:
            self.opacity_effect.setOpacity(value)

    def setCurrentIndex(self, index):
        if index == self.currentIndex():
            return
        self.anim.stop()
        if self.graphicsEffect():
            self.setGraphicsEffect(None)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)

        def on_fade_in_done():
            self.setGraphicsEffect(None)
            self.opacity_effect = None
            try: self.anim.finished.disconnect()
            except: pass

        def on_fade_out():
            super(AnimatedStackedWidget, self).setCurrentIndex(index)
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            try: self.anim.finished.disconnect()
            except: pass
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.finished.connect(on_fade_in_done)
            self.anim.start()

        try: self.anim.finished.disconnect()
        except: pass
        self.anim.finished.connect(on_fade_out)
        self.anim.start()


class SidebarButton(QPushButton):
    def __init__(self, text, icon_text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon_text
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()

    def update_style(self):
        choice = "selected" if self.isChecked() else "normal"
        styles = {
            "normal": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS["text_secondary"]};
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["bg_card"]};
                    color: {COLORS["text_primary"]};
                }}
            """,
            "selected": f"""
                QPushButton {{
                    background-color: {COLORS["accent_primary"]};
                    color: white;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 10px;
                }}
            """,
        }
        self.setStyleSheet(styles[choice])

class ModernSidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.buttons = {}
        self.initUI()

    def initUI(self):
        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            background-color: {COLORS["bg_secondary"]};
            border-right: 1px solid {COLORS["border"]};
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 30, 15, 30)
        layout.setSpacing(10)

        # Logo / Brand
        logo_label = QLabel("🎮  AIO BROWSER")
        logo_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 900;
            color: {COLORS["text_primary"]};
            margin-bottom: 30px;
            letter-spacing: 1px;
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        self.setLayout(layout)

        # Navigation
        self.add_nav_item("search", "🔍  Search")
        self.add_nav_item("patcher", "🛠  Patcher")

        layout.addStretch()

        # Bottom Actions
        self.add_nav_item("info", "ℹ️  Info")
        self.add_nav_item("downloads", "📥  Downloads")
        self.add_nav_item("settings", "⚙  Settings")

    def add_nav_item(self, key, label):
        btn = SidebarButton(label, "")
        btn.clicked.connect(lambda: self.on_click(key))
        self.layout().addWidget(btn)
        self.buttons[key] = btn

    def on_click(self, key):
        for k, b in self.buttons.items():
            b.setChecked(k == key)
            b.update_style()

        if key == "search":
            self.parent.main_stack.setCurrentIndex(0)
            self.parent.page_title.setText("Search")
        elif key == "downloads":
            self.parent.main_stack.setCurrentIndex(1)
            self.parent.page_title.setText("Downloads")
        elif key == "patcher":
            self.parent.main_stack.setCurrentIndex(2)
            self.parent.page_title.setText("Steam Patcher")
        elif key == "info":
            self.parent.main_stack.setCurrentIndex(3)
            self.parent.page_title.setText("Information")
        elif key == "settings":
            self.parent.main_stack.setCurrentIndex(4)
            self.parent.page_title.setText("Settings")

    def set_active(self, key):
        self.on_click(key)

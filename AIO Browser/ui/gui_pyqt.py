# gui_pyqt.py
# PyQt6 Graphical User Interface
import sys
import json
import os
import time
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote

import requests
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from core import downloader
from core import scraper
from core import steam_utils
from core import patcher
from PIL import Image
import io

from ui.styles import COLORS, STYLESHEET
from ui.settings import SettingsManager, SettingsDialog
from ui.splash_screen import SplashScreen
from ui.downloads import DownloadsPage

# Styles and Settings are now imported from styles.py and settings.py


# =========================================================================
# ANIMATED LOADING WIDGET
# =========================================================================
class LoadingWidget(QWidget):
    def __init__(self, text="Searching"):
        super().__init__()
        self.text = text
        self.dot_count = 0
        self.initUI()
        
        # Animations
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_dots)
        self.timer.start(400)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.spinner_label)
        self.spinner_label.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_timer = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_timer.setDuration(1000)
        self.pulse_timer.setStartValue(0.4)
        self.pulse_timer.setEndValue(1.0)
        self.pulse_timer.setLoopCount(-1)
        self.pulse_timer.start()
    
    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        # Modern Spinner
        self.spinner_label = QLabel("󱑮")
        self.spinner_label.setStyleSheet(f"""
            font-size: 40px;
            color: {COLORS["accent_primary"]};
        """)
        self.spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Text
        self.text_label = QLabel(self.text)
        self.text_label.setStyleSheet(f"""
            font-size: 15px;
            color: {COLORS["text_secondary"]};
            letter-spacing: 1px;
            text-transform: uppercase;
            font-weight: bold;
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.spinner_label)
        layout.addWidget(self.text_label)
        layout.addStretch()
        self.setLayout(layout)
    
    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_label.setText(f"{self.text}{dots}")
        
        frames = ["󱑮", "󱑯", "󱑰", "󱑱", "󱑲", "󱑳", "󱑴", "󱑵"]
        self.spinner_label.setText(frames[self.dot_count % len(frames)])
    
    def stop(self):
        self.timer.stop()
        self.pulse_timer.stop()



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
        # This prevents nested effect conflicts and fixes the deletion crash
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
        img_container_layout.setContentsMargins(0,0,0,0)
        
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
        
        self.title_label = QLabel(self.game['title'])
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
        source_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 500; background-color: transparent;")
        badge_layout.addWidget(source_label)
        
        if self.game.get('size'):
            size_label = QLabel(f"📦 {self.game['size']}")
            size_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 500; background-color: transparent;")
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
            has_magnet = self.game.get('magnet')
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

        # Prepare Hover & Shadow (will be applied after entrance)
        # We don't set the effect here because entrance animation uses OpacityEffect
        
        # Hover scaling setup
        self.hover_anim = QPropertyAnimation(self, b"maximumHeight")
        self.hover_anim.setDuration(200)

        # Load image in background
        if self.game.get('image'):
            threading.Thread(target=self.load_image, daemon=True).start()
            
    def enterEvent(self, event):
        if hasattr(self, 'shadow') and self.graphicsEffect() == self.shadow:
            self.shadow.setBlurRadius(30)
            self.shadow.setColor(QColor(124, 58, 237, 40)) # Accent primary glow
            self.shadow.setYOffset(8)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if hasattr(self, 'shadow') and self.graphicsEffect() == self.shadow:
            self.shadow.setBlurRadius(20)
            self.shadow.setColor(QColor(0, 0, 0, 80))
            self.shadow.setYOffset(4)
        super().leaveEvent(event)


    
    def load_image(self):
        try:
            response = requests.get(self.game['image'], timeout=5)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((80, 110), Image.Resampling.LANCZOS)
            
            # Convert PIL to QImage
            if img.mode == 'RGB':
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            elif img.mode == 'RGBA':
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 4, QImage.Format.Format_RGBA8888)
            else:
                img = img.convert('RGB')
                qimg = QImage(img.tobytes(), img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimg)
            
            # Update UI in main thread
            QMetaObject.invokeMethod(self, "set_pixmap", Qt.ConnectionType.QueuedConnection, Q_ARG(QPixmap, pixmap))
        except:
            pass
    
    @pyqtSlot(QPixmap)
    def set_pixmap(self, pixmap):
        self.image_label.setPixmap(pixmap.scaled(80, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.image_label.setText("")
    
    def start_direct_download(self):
        if self.parent:
            self.parent.initiate_anker_download(self.game)
    
    def open_torrent_link(self):
        has_magnet = self.game.get('magnet')
        url = self.game['magnet'] if has_magnet else self.game['link']
        webbrowser.open(url)

# =========================================================================
# DOWNLOAD DIALOG
# =========================================================================
# DownloadDialog has been moved to download_ui.py


# =========================================================================
# SETTINGS DIALOG
# =========================================================================
# SettingsDialog has been moved to settings.py

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
        
        # Stop any existing effect to prevent painter clashes
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
            # Re-apply effect for fade in
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

# =========================================================================
# MODERN SIDEBAR COMPONENTS
# =========================================================================

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
            """
        }
        self.setStyleSheet(styles[choice])

    def paintEvent(self, event):
        super().paintEvent(event)
        # We could draw an icon here if we wanted, but for now we rely on text

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
        elif key == "settings":
            self.parent.open_settings()
            # Reset checks to search/patcher
            self.on_click("search" if self.parent.main_stack.currentIndex() == 0 else "patcher")


    def set_active(self, key):
        self.on_click(key)

# =========================================================================
# MAIN APPLICATION WINDOW
# =========================================================================

class GameSearchApp(QMainWindow):
    # Custom Signals for Thread Safety
    search_direct_results_ready = pyqtSignal(list, object)
    search_torrent_results_ready = pyqtSignal(list)
    download_prompt_ready = pyqtSignal(str, str, object, str) # url, name, session, download_id
    download_status_updated = pyqtSignal(str, str, float) # download_id, status, progress
    download_finished = pyqtSignal(str, str, str) # download_id, result, save_path

    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.image_cache = {}
        
        # Pagination state
        self.direct_results = []
        self.direct_current_page = 0
        self.direct_page_size = 5
        self.direct_anker_client = None
        
        self.torrent_results = []
        self.torrent_current_page = 0
        self.torrent_page_size = 5
        
        # Connect Signals
        self.search_direct_results_ready.connect(self.display_direct_results)
        self.search_torrent_results_ready.connect(self.display_torrent_results)
        self.download_prompt_ready.connect(self.prompt_download)
        self.download_status_updated.connect(self.update_download_status)
        self.download_finished.connect(self.on_download_finished)

        self.initUI()
        
        if not self.settings_manager.get("disable_splash", False):
            self.show_splash()
        else:
            self.show_main_interface()
    
    def initUI(self):
        self.setWindowTitle("🎮 AIO Browser")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet(STYLESHEET)
        
        # Initialize and style StatusBar
        status = self.statusBar()
        status.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; color: {COLORS['text_secondary']}; border-top: 1px solid {COLORS['border']};")
        status.showMessage("Ready")
    
    # Basic internal settings methods are now in SettingsManager
    
    def show_splash(self):
        self.splash = SplashScreen(on_finished_callback=self.transition_to_main)
        self.splash.start_animation()
    
    def transition_to_main(self):
        self.show_main_interface()
        self.show()
    
    def show_main_interface(self):
        # Central widget with horizontal layout for sidebar + content
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = ModernSidebar(self)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setStyleSheet(f"QFrame#Sidebar {{ background-color: {COLORS['bg_secondary']}; border-right: 1px solid {COLORS['border']}; }}")
        layout.addWidget(self.sidebar)
        
        # Content Area
        self.content_container = QWidget()
        self.content_container.setObjectName("ContentArea")
        self.content_container.setStyleSheet(f"QWidget#ContentArea {{ background-color: {COLORS['bg_primary']}; }}")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setObjectName("Header")
        self.header.setFixedHeight(70)
        self.header.setStyleSheet(f"""
            QFrame#Header {{
                background-color: {COLORS["bg_primary"]};
                border-bottom: 1px solid {COLORS["border"]};
            }}
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        self.page_title = QLabel("Search")
        self.page_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 800;
            color: {COLORS["text_primary"]};
        """)
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        
        # Quick indicators or user profile could go here
        
        self.header.setLayout(header_layout)
        content_layout.addWidget(self.header)
        
        # Main Stack
        self.main_stack = AnimatedStackedWidget()
        
        # Search page
        self.search_page = QWidget()
        self.setup_search_tab()
        self.main_stack.addWidget(self.search_page)
        
        # Downloads page
        self.downloads_tab = DownloadsPage(self)
        self.main_stack.addWidget(self.downloads_tab)
        
        # Patcher page
        self.patcher_tab = QWidget()
        self.setup_patcher_tab()
        self.main_stack.addWidget(self.patcher_tab)
        
        content_layout.addWidget(self.main_stack)
        self.content_container.setLayout(content_layout)
        
        layout.addWidget(self.content_container)
        central.setLayout(layout)
        
        # Set initial page
        self.sidebar.set_active("search")
    
    def setup_search_tab(self):
        # Create a layout for the search tab to hold the sub-tabs (similar to patcher tab)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Tab widget to hold Direct/Torrent result pages
        self.search_tabs = QTabWidget()
        # Make the tab bar visually flush/left-aligned and remove extra pane padding
        self.search_tabs.setStyleSheet(f"""
            QTabBar::tab {{ padding: 12px 25px; margin: 0px; }}
            QTabBar {{ margin: 0px; padding: 0px; }}
            QTabWidget::pane {{ border: none; margin: 0px; padding: 0px; background: transparent; }}
        """)
        
        # Direct Results Page (now includes its own search bar at the top)
        self.direct_page = QWidget()
        direct_layout = QVBoxLayout(self.direct_page)
        direct_layout.setContentsMargins(40, 40, 40, 40)
        direct_layout.setSpacing(12)

        direct_search_bar = QFrame()
        direct_search_bar.setFixedHeight(60)
        direct_search_bar.setStyleSheet(f"""
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
        """
        )
        direct_sb_layout = QHBoxLayout(direct_search_bar)
        direct_sb_layout.setContentsMargins(10, 5, 10, 5)
        direct_sb_layout.setSpacing(10)


        self.direct_search_input = QLineEdit()
        self.direct_search_input.setPlaceholderText("Search for direct download games...")
        self.direct_search_input.setFixedHeight(45)
        self.direct_search_input.setStyleSheet("border: none; background: transparent; padding: 0 15px; font-size: 16px;")
        self.direct_search_input.returnPressed.connect(self.trigger_search)
        direct_sb_layout.addWidget(self.direct_search_input, 1)

        self.direct_search_btn = QPushButton("Search")
        self.direct_search_btn.setFixedSize(100, 40)
        self.direct_search_btn.clicked.connect(self.trigger_search)
        direct_sb_layout.addWidget(self.direct_search_btn)

        direct_layout.addWidget(direct_search_bar)

        self.direct_scroll = QScrollArea()
        self.direct_scroll.setWidgetResizable(True)
        self.direct_results_widget = QWidget()
        self.direct_results_layout = QVBoxLayout(self.direct_results_widget)
        self.direct_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.direct_results_layout.setSpacing(15)
        self.direct_scroll.setWidget(self.direct_results_widget)
        direct_layout.addWidget(self.direct_scroll)

        # Torrent Results Page (now includes its own search bar at the top)
        self.torrent_page = QWidget()
        torrent_layout = QVBoxLayout(self.torrent_page)
        torrent_layout.setContentsMargins(40, 40, 40, 40)
        torrent_layout.setSpacing(12)

        torrent_search_bar = QFrame()
        torrent_search_bar.setFixedHeight(60)
        torrent_search_bar.setStyleSheet(f"""
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
        """
        )
        torrent_sb_layout = QHBoxLayout(torrent_search_bar)
        torrent_sb_layout.setContentsMargins(10, 5, 10, 5)
        torrent_sb_layout.setSpacing(10)


        self.torrent_search_input = QLineEdit()
        self.torrent_search_input.setPlaceholderText("Search for torrent/fitgirl repacks...")
        self.torrent_search_input.setFixedHeight(45)
        self.torrent_search_input.setStyleSheet("border: none; background: transparent; padding: 0 15px; font-size: 16px;")
        self.torrent_search_input.returnPressed.connect(self.trigger_search)
        torrent_sb_layout.addWidget(self.torrent_search_input, 1)

        self.torrent_search_btn = QPushButton("Search")
        self.torrent_search_btn.setFixedSize(100, 40)
        self.torrent_search_btn.clicked.connect(self.trigger_search)
        torrent_sb_layout.addWidget(self.torrent_search_btn)

        torrent_layout.addWidget(torrent_search_bar)

        self.torrent_scroll = QScrollArea()
        self.torrent_scroll.setWidgetResizable(True)
        self.torrent_results_widget = QWidget()
        self.torrent_results_layout = QVBoxLayout(self.torrent_results_widget)
        self.torrent_results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.torrent_results_layout.setSpacing(15)
        self.torrent_scroll.setWidget(self.torrent_results_widget)
        torrent_layout.addWidget(self.torrent_scroll)

        self.search_tabs.addTab(self.direct_page, "Direct")
        self.search_tabs.addTab(self.torrent_page, "Torrent")
        self.search_tabs.currentChanged.connect(self.on_search_tab_changed)
        
        main_layout.addWidget(self.search_tabs)
        self.search_page.setLayout(main_layout)
        # Default to Direct tab
        self.search_tabs.setCurrentIndex(0)

    def on_search_tab_changed(self, idx):
        # Focus the search input for the active tab
        if idx == 0:
            if hasattr(self, 'direct_search_input'):
                self.direct_search_input.setFocus()
        else:
            if hasattr(self, 'torrent_search_input'):
                self.torrent_search_input.setFocus()

    def trigger_search(self):

        # Use the current tab to decide which search to run
        if getattr(self, 'search_tabs', None) and self.search_tabs.currentIndex() == 0:
            self.start_direct_search()
        else:
            self.start_torrent_search()

    def setup_direct_tab(self):
        pass # Integrated into setup_search_tab now

    def setup_torrent_tab(self):
        pass # Integrated into setup_search_tab now

    
    def setup_patcher_tab(self):
        # Create a layout for the patcher tab to hold the sub-tabs
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.patcher_tabs = QTabWidget()
        
        # Create the Goldberg sub-tab
        self.goldberg_tab = QWidget()
        self.setup_goldberg_subtab()
        
        # Create the CreamAPI sub-tab
        self.creamapi_tab = QWidget()
        self.setup_creamapi_subtab()
        
        self.patcher_tabs.addTab(self.goldberg_tab, "Goldberg")
        self.patcher_tabs.addTab(self.creamapi_tab, "CreamAPI")
        
        main_layout.addWidget(self.patcher_tabs)
        self.patcher_tab.setLayout(main_layout)

    def setup_goldberg_subtab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header + Refresh
        header_layout = QHBoxLayout()
        title_vlayout = QVBoxLayout()
        
        title = QLabel("🛠  Steam Patcher")
        title.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['text_primary']};")
        title_vlayout.addWidget(title)
        
        subtitle = QLabel("Apply Goldberg Emulator to your installed Steam games in one click.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        title_vlayout.addWidget(subtitle)
        header_layout.addLayout(title_vlayout)
        
        header_layout.addStretch()
        
        self.refresh_steam_btn = QPushButton("🔄  Scan Library")
        self.refresh_steam_btn.setFixedSize(140, 40)
        self.refresh_steam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_steam_btn.clicked.connect(self.load_steam_games)
        header_layout.addWidget(self.refresh_steam_btn)
        
        layout.addLayout(header_layout)
        
        # Search for installed games
        self.steam_search_input = QLineEdit()
        self.steam_search_input.setPlaceholderText("Filter your Steam library...")
        self.steam_search_input.setFixedHeight(45)
        self.steam_search_input.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;")
        self.steam_search_input.textChanged.connect(self.filter_steam_games)
        layout.addWidget(self.steam_search_input)
        
        # Scroll Area for games
        self.steam_scroll = QScrollArea()
        self.steam_scroll.setWidgetResizable(True)
        self.steam_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.steam_container = QWidget()
        self.steam_container_layout = QVBoxLayout(self.steam_container)
        self.steam_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steam_container_layout.setSpacing(12)
        
        self.steam_scroll.setWidget(self.steam_container)
        layout.addWidget(self.steam_scroll)
        
        self.goldberg_tab.setLayout(layout)
        
        self.installed_steam_games = []
        # Initial load after interface is fully ready
        QTimer.singleShot(1000, self.load_steam_games)

    def setup_creamapi_subtab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header + Refresh
        header_layout = QHBoxLayout()
        title_vlayout = QVBoxLayout()
        
        title = QLabel("🍦  CreamAPI Patcher")
        title.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['text_primary']};")
        title_vlayout.addWidget(title)
        
        subtitle = QLabel("Unlock DLC for your installed Steam games using CreamAPI.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        title_vlayout.addWidget(subtitle)
        header_layout.addLayout(title_vlayout)
        
        header_layout.addStretch()
        
        self.refresh_steam_btn_creamapi = QPushButton("🔄  Scan Library")
        self.refresh_steam_btn_creamapi.setFixedSize(140, 40)
        self.refresh_steam_btn_creamapi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_steam_btn_creamapi.clicked.connect(self.load_steam_games_creamapi)
        header_layout.addWidget(self.refresh_steam_btn_creamapi)
        
        layout.addLayout(header_layout)
        
        # Search for installed games
        self.steam_search_input_creamapi = QLineEdit()
        self.steam_search_input_creamapi.setPlaceholderText("Filter your Steam library...")
        self.steam_search_input_creamapi.setFixedHeight(45)
        self.steam_search_input_creamapi.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;")
        self.steam_search_input_creamapi.textChanged.connect(self.filter_steam_games_creamapi)
        layout.addWidget(self.steam_search_input_creamapi)
        
        # Scroll Area for games
        self.steam_scroll_creamapi = QScrollArea()
        self.steam_scroll_creamapi.setWidgetResizable(True)
        self.steam_scroll_creamapi.setStyleSheet("background: transparent; border: none;")
        
        self.steam_container_creamapi = QWidget()
        self.steam_container_layout_creamapi = QVBoxLayout(self.steam_container_creamapi)
        self.steam_container_layout_creamapi.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steam_container_layout_creamapi.setSpacing(12)
        
        self.steam_scroll_creamapi.setWidget(self.steam_container_creamapi)
        layout.addWidget(self.steam_scroll_creamapi)
        
        self.creamapi_tab.setLayout(layout)
        
        self.installed_steam_games_creamapi = []
        # Initial load after interface is fully ready
        QTimer.singleShot(1000, self.load_steam_games_creamapi)

    def load_steam_games(self):
        self.clear_layout(self.steam_container_layout)
        state_label = QLabel("Scanning Steam libraries...")
        state_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_container_layout.addWidget(state_label)
        
        def run_scan():
            try:
                self.installed_steam_games = steam_utils.get_installed_games()
                QMetaObject.invokeMethod(self, "display_steam_games", Qt.ConnectionType.QueuedConnection)
            except Exception as e:
                print(f"[ERROR] Scan failed: {e}")
            
        threading.Thread(target=run_scan, daemon=True).start()

    @pyqtSlot()
    def display_steam_games(self):
        self.render_steam_games(self.installed_steam_games)

    def filter_steam_games(self, text):
        filtered = [g for g in self.installed_steam_games if text.lower() in g['name'].lower()]
        self.render_steam_games(filtered)

    def render_steam_games(self, games):
        self.clear_layout(self.steam_container_layout)
        
        if not games:
            empty = QLabel("No games found or Steam not detected.")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; margin-top: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout.addWidget(empty)
            return
            
        for game in games:
            card = QFrame()
            card.setObjectName("SteamCard")
            card.setFixedHeight(85)
            card.setStyleSheet(f"""
                QFrame#SteamCard {{ 
                    background-color: {COLORS['bg_card']}; 
                    border-radius: 12px; 
                    border: 1px solid {COLORS['border']}; 
                }}
                QFrame#SteamCard:hover {{
                    border: 1px solid {COLORS['accent_primary']};
                    background-color: {COLORS['bg_card_hover']};
                }}
            """)
            
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(25, 0, 25, 0)
            
            # Info Section
            info = QVBoxLayout()
            info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            info.setSpacing(2)
            
            name = QLabel(game['name'])
            name.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
            info.addWidget(name)
            
            meta_layout = QHBoxLayout()
            meta_layout.setSpacing(15)
            
            appid = QLabel(f"🆔 {game['id']}")
            appid.setStyleSheet(f"font-size: 11px; color: {COLORS['accent_secondary']}; background: transparent; font-weight: 600;")
            meta_layout.addWidget(appid)
            
            dir_name = os.path.basename(str(game['full_path']))
            path = QLabel(f"📂 {dir_name}")
            path.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
            meta_layout.addWidget(path)
            meta_layout.addStretch()
            
            info.addLayout(meta_layout)
            c_layout.addLayout(info, 1)
            
            # Action Buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            
            revert_btn = QPushButton("↩")
            revert_btn.setFixedSize(40, 40)
            revert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            revert_btn.setToolTip("Revert patch (restore backups)")
            revert_btn.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']};")
            revert_btn.clicked.connect(lambda checked, g=game: self.trigger_revert(g))
            btn_layout.addWidget(revert_btn)
            
            apply_btn = QPushButton("Apply Goldberg")
            apply_btn.setFixedSize(140, 40)
            apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_secondary']};
                }}
            """)
            apply_btn.clicked.connect(lambda checked, g=game: self.trigger_patch(g))
            btn_layout.addWidget(apply_btn)
            
            c_layout.addLayout(btn_layout)
            
            self.steam_container_layout.addWidget(card)

    def trigger_patch(self, game):
        # Confirmation
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Apply Patch")
        msg_box.setText(f"Apply Goldberg Emulator to {game['name']}?")
        msg_box.setInformativeText("This will replace original Steam DLLs with emulator versions (backups will be created).")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.setStyleSheet(STYLESHEET)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            # Show progress
            self.statusBar().showMessage(f"Patching {game['name']}...")
            
            def run():
                nick = self.settings_manager.get("goldberg_nickname", "AIOUser")
                lang = self.settings_manager.get("goldberg_language", "english")
                success, log_msg = patcher.patch_game(game['full_path'], game['id'], "tools", nickname=nick, language=lang)
                QMetaObject.invokeMethod(self, "on_patch_finished", Qt.ConnectionType.QueuedConnection, 
                                       Q_ARG(bool, success), Q_ARG(str, log_msg))
            
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished(self, success, log_msg):
        self.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(self, "Patch Successful", 
                                  "The Goldberg patch has been applied successfully!\n\n" + log_msg)
        else:
            QMessageBox.critical(self, "Patch Failed", 
                               "Failed to apply patch:\n\n" + log_msg)

    def trigger_revert(self, game):
        # Confirmation
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Revert Patch")
        msg_box.setText(f"Restore original files for {game['name']}?")
        msg_box.setInformativeText("This will restore the .bak files and remove Goldberg settings. It only works if a backup exists.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setStyleSheet(STYLESHEET)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage(f"Reverting {game['name']}...")
            
            def run():
                success, log_msg = patcher.revert_patch(game['full_path'])
                QMetaObject.invokeMethod(self, "on_revert_finished", Qt.ConnectionType.QueuedConnection, 
                                       Q_ARG(bool, success), Q_ARG(str, log_msg))
            
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_revert_finished(self, success, log_msg):
        self.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(self, "Revert Successful", 
                                  "Original files have been restored!\n\n" + log_msg)
        else:
            QMessageBox.warning(self, "Revert Failed", 
                               "Could not revert patch:\n\n" + log_msg)

    def load_steam_games_creamapi(self):
        self.clear_layout(self.steam_container_layout_creamapi)
        state_label = QLabel("Scanning Steam libraries...")
        state_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_container_layout_creamapi.addWidget(state_label)
        
        def run_scan():
            try:
                self.installed_steam_games_creamapi = steam_utils.get_installed_games()
                QMetaObject.invokeMethod(self, "display_steam_games_creamapi", Qt.ConnectionType.QueuedConnection)
            except Exception as e:
                print(f"[ERROR] Scan failed: {e}")
            
        threading.Thread(target=run_scan, daemon=True).start()

    @pyqtSlot()
    def display_steam_games_creamapi(self):
        self.render_steam_games_creamapi(self.installed_steam_games_creamapi)

    def filter_steam_games_creamapi(self, text):
        filtered = [g for g in self.installed_steam_games_creamapi if text.lower() in g['name'].lower()]
        self.render_steam_games_creamapi(filtered)

    def render_steam_games_creamapi(self, games):
        self.clear_layout(self.steam_container_layout_creamapi)
        
        if not games:
            empty = QLabel("No games found or Steam not detected.")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; margin-top: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout_creamapi.addWidget(empty)
            return
            
        for game in games:
            card = QFrame()
            card.setObjectName("SteamCard")
            card.setFixedHeight(85)
            card.setStyleSheet(f"""
                QFrame#SteamCard {{ 
                    background-color: {COLORS['bg_card']}; 
                    border-radius: 12px; 
                    border: 1px solid {COLORS['border']}; 
                }}
                QFrame#SteamCard:hover {{
                    border: 1px solid {COLORS['accent_primary']};
                    background-color: {COLORS['bg_card_hover']};
                }}
            """)
            
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(25, 0, 25, 0)
            
            # Info Section
            info = QVBoxLayout()
            info.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            info.setSpacing(2)
            
            name = QLabel(game['name'])
            name.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
            info.addWidget(name)
            
            meta_layout = QHBoxLayout()
            meta_layout.setSpacing(15)
            
            appid = QLabel(f"🆔 {game['id']}")
            appid.setStyleSheet(f"font-size: 11px; color: {COLORS['accent_secondary']}; background: transparent; font-weight: 600;")
            meta_layout.addWidget(appid)
            
            dir_name = os.path.basename(str(game['full_path']))
            path = QLabel(f"📂 {dir_name}")
            path.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
            meta_layout.addWidget(path)
            meta_layout.addStretch()
            
            info.addLayout(meta_layout)
            c_layout.addLayout(info, 1)
            
            # Action Buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)
            
            revert_btn = QPushButton("↩")
            revert_btn.setFixedSize(40, 40)
            revert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            revert_btn.setToolTip("Revert patch (restore backups)")
            revert_btn.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']};")
            revert_btn.clicked.connect(lambda checked, g=game: self.trigger_revert_creamapi(g))
            btn_layout.addWidget(revert_btn)
            
            apply_btn = QPushButton("Apply CreamAPI")
            apply_btn.setFixedSize(140, 40)
            apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_secondary']};
                }}
            """)
            apply_btn.clicked.connect(lambda checked, g=game: self.trigger_patch_creamapi(g))
            btn_layout.addWidget(apply_btn)
            
            c_layout.addLayout(btn_layout)
            
            self.steam_container_layout_creamapi.addWidget(card)

    def trigger_patch_creamapi(self, game):
        # DLC ID input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("CreamAPI - DLC Configuration")
        dialog.setFixedSize(500, 300)
        dialog.setStyleSheet(STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        info_label = QLabel(f"Enter DLC IDs for {game['name']}:")
        info_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_primary']};")
        layout.addWidget(info_label)
        
        help_label = QLabel("Enter one DLC ID per line (e.g., 123456, 789012)")
        help_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(help_label)
        
        dlc_input = QTextEdit()
        dlc_input.setPlaceholderText("123456\n789012\n345678")
        dlc_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }}
        """)
        layout.addWidget(dlc_input)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedSize(100, 35)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
        """)
        apply_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(apply_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dlc_text = dlc_input.toPlainText().strip()
            dlc_ids = [line.strip() for line in dlc_text.split('\n') if line.strip()] if dlc_text else None
            
            # Confirmation
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Apply Patch")
            msg_msg = f"Apply CreamAPI to {game['name']}?"
            if dlc_ids:
                msg_msg += f"\n\nDLC IDs: {', '.join(dlc_ids[:5])}"
                if len(dlc_ids) > 5:
                    msg_msg += f" (+{len(dlc_ids) - 5} more)"
            msg_box.setText(msg_msg)
            msg_box.setInformativeText("This will replace original Steam DLLs with CreamAPI versions (backups will be created).")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            msg_box.setStyleSheet(STYLESHEET)
            
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                # Show progress
                self.statusBar().showMessage(f"Patching {game['name']} with CreamAPI...")
                
                def run():
                    success, log_msg = patcher.patch_game_creamapi(game['full_path'], game['id'], "tools", dlc_ids=dlc_ids)
                    QMetaObject.invokeMethod(self, "on_patch_finished_creamapi", Qt.ConnectionType.QueuedConnection, 
                                           Q_ARG(bool, success), Q_ARG(str, log_msg))
                
                threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished_creamapi(self, success, log_msg):
        self.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(self, "Patch Successful", 
                                  "The CreamAPI patch has been applied successfully!\n\n" + log_msg)
        else:
            QMessageBox.critical(self, "Patch Failed", 
                               "Failed to apply patch:\n\n" + log_msg)

    def trigger_revert_creamapi(self, game):
        # Confirmation
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Revert Patch")
        msg_box.setText(f"Restore original files for {game['name']}?")
        msg_box.setInformativeText("This will restore the .bak files and remove CreamAPI configuration. It only works if a backup exists.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setStyleSheet(STYLESHEET)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.statusBar().showMessage(f"Reverting {game['name']}...")
            
            def run():
                success, log_msg = patcher.revert_creamapi_patch(game['full_path'])
                QMetaObject.invokeMethod(self, "on_revert_finished_creamapi", Qt.ConnectionType.QueuedConnection, 
                                       Q_ARG(bool, success), Q_ARG(str, log_msg))
            
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_revert_finished_creamapi(self, success, log_msg):
        self.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(self, "Revert Successful", 
                                  "Original files have been restored!\n\n" + log_msg)
        else:
            QMessageBox.warning(self, "Revert Failed", 
                               "Could not revert patch:\n\n" + log_msg)
    
    def start_direct_search(self):
        query = self.direct_search_input.text().strip()
        if not query:
            return
        
        # Clear previous results & loading state
        self.clear_layout(self.direct_results_layout)
        if hasattr(self, 'direct_loading_widget') and self.direct_loading_widget:
            self.direct_loading_widget.stop()
            self.direct_loading_widget.deleteLater()
            self.direct_loading_widget = None

        # Show loading widget
        self.direct_loading_widget = LoadingWidget("Searching AnkerGames")
        self.direct_results_layout.addWidget(self.direct_loading_widget)
        
        self.direct_search_btn.setEnabled(False)
        self.direct_search_btn.setText("Searching...")
        
        threading.Thread(target=self.perform_direct_search, args=(query,), daemon=True).start()
    
    def perform_direct_search(self, query):
        anker = scraper.AnkerClient()
        results = anker.search(query)
        self.search_direct_results_ready.emit(results, anker)
    
    @pyqtSlot(list, object)
    def display_direct_results(self, results, anker_client):
        # Remove loading widget
        if hasattr(self, 'direct_loading_widget') and self.direct_loading_widget:
            self.direct_loading_widget.stop()
            self.direct_loading_widget.deleteLater()
            self.direct_loading_widget = None
        
        self.direct_results = results
        self.direct_anker_client = anker_client
        self.direct_current_page = 0
        
        self.direct_search_btn.setEnabled(True)
        self.direct_search_btn.setText("Search")

        
        if not results:
            no_results = QLabel("😕 No results found")
            no_results.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {COLORS["text_secondary"]};
            """)
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.direct_results_layout.addWidget(no_results)
            return
        
        self.render_direct_page()
    
    def render_direct_page(self):
        self.clear_layout(self.direct_results_layout)
        
        start = self.direct_current_page * self.direct_page_size
        end = start + self.direct_page_size
        page_results = self.direct_results[start:end]
        
        for i, game in enumerate(page_results):
            delay = i * 100 # 100ms staggered delay
            card = GameCardWidget(game, "direct", self, delay=delay)
            self.direct_results_layout.addWidget(card)
        
        self.direct_results_layout.addStretch()
        
        # Pagination controls
        self.create_pagination_controls(self.direct_results_layout, len(self.direct_results), 
                                       self.direct_current_page, self.direct_page_size, 
                                       self.change_direct_page)
    
    def start_torrent_search(self):
        query = self.torrent_search_input.text().strip()
        if not query:
            return
        
        # Clear previous results
        self.clear_layout(self.torrent_results_layout)
        if hasattr(self, 'torrent_loading_widget') and self.torrent_loading_widget:
            self.torrent_loading_widget.stop()
            self.torrent_loading_widget.deleteLater()
            self.torrent_loading_widget = None

        # Show loading widget
        self.torrent_loading_widget = LoadingWidget("Searching FitGirl Repacks")
        self.torrent_results_layout.addWidget(self.torrent_loading_widget)
        
        self.torrent_search_btn.setEnabled(False)
        self.torrent_search_btn.setText("Searching...")
        
        threading.Thread(target=self.perform_torrent_search, args=(query,), daemon=True).start()
    
    def perform_torrent_search(self, query):
        results = scraper.search_fitgirl(query)
        self.search_torrent_results_ready.emit(results)
    
    @pyqtSlot(list)
    def display_torrent_results(self, results):
        # Remove loading widget
        if hasattr(self, 'torrent_loading_widget') and self.torrent_loading_widget:
            self.torrent_loading_widget.stop()
            self.torrent_loading_widget.deleteLater()
            self.torrent_loading_widget = None
        
        self.torrent_results = results
        self.torrent_current_page = 0
        
        self.torrent_search_btn.setEnabled(True)
        self.torrent_search_btn.setText("Search")

        
        if not results:
            no_results = QLabel("😕 No results found")
            no_results.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {COLORS["text_secondary"]};
            """)
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.torrent_results_layout.addWidget(no_results)
            return
        
        self.render_torrent_page()
    
    def render_torrent_page(self):
        self.clear_layout(self.torrent_results_layout)
        
        start = self.torrent_current_page * self.torrent_page_size
        end = start + self.torrent_page_size
        page_results = self.torrent_results[start:end]
        
        for i, game in enumerate(page_results):
            delay = i * 100 # 100ms staggered delay
            card = GameCardWidget(game, "torrent", self, delay=delay)
            self.torrent_results_layout.addWidget(card)
        
        self.torrent_results_layout.addStretch()
        
        # Pagination controls
        self.create_pagination_controls(self.torrent_results_layout, len(self.torrent_results), 
                                       self.torrent_current_page, self.torrent_page_size, 
                                       self.change_torrent_page)
    
    def create_pagination_controls(self, layout, total_items, current_page, page_size, callback):
        total_pages = (total_items + page_size - 1) // page_size
        if total_pages <= 1:
            return
        
        footer = QWidget()
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Previous button
        prev_btn = QPushButton("<")
        prev_btn.setFixedSize(40, 40)
        prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_card"]};
                color: {COLORS["text_primary"]};
                border-radius: 8px;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
            }}
        """)
        if current_page > 0:
            prev_btn.clicked.connect(lambda: callback(current_page - 1))
        else:
            prev_btn.setEnabled(False)
        footer_layout.addWidget(prev_btn)
        
        # Page numbers
        start_page = max(0, current_page - 2)
        end_page = min(total_pages, start_page + 5)
        if end_page - start_page < 5:
            start_page = max(0, end_page - 5)
        
        for p in range(start_page, end_page):
            page_btn = QPushButton(str(p + 1))
            page_btn.setFixedSize(40, 40)
            if p == current_page:
                page_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS["accent_primary"]};
                        color: white;
                        border-radius: 8px;
                        padding: 0;
                    }}
                """)
            else:
                page_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS["bg_card"]};
                        color: {COLORS["text_primary"]};
                        border-radius: 8px;
                        padding: 0;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS["bg_card_hover"]};
                    }}
                """)
            page_btn.clicked.connect(lambda checked, page=p: callback(page))
            footer_layout.addWidget(page_btn)
        
        # Next button
        next_btn = QPushButton(">")
        next_btn.setFixedSize(40, 40)
        next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_card"]};
                color: {COLORS["text_primary"]};
                border-radius: 8px;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {COLORS["bg_card_hover"]};
            }}
        """)
        if current_page < total_pages - 1:
            next_btn.clicked.connect(lambda: callback(current_page + 1))
        else:
            next_btn.setEnabled(False)
        footer_layout.addWidget(next_btn)
        
        footer.setLayout(footer_layout)
        layout.addWidget(footer)
    
    def change_direct_page(self, new_page):
        self.direct_current_page = new_page
        self.render_direct_page()
        # Scroll to top
        self.direct_scroll.verticalScrollBar().setValue(0)
    
    def change_torrent_page(self, new_page):
        self.torrent_current_page = new_page
        self.render_torrent_page()
        # Scroll to top
        self.torrent_scroll.verticalScrollBar().setValue(0)
    
    def initiate_anker_download(self, game):
        import uuid
        download_id = str(uuid.uuid4())
        
        # Add to downloads tab
        self.downloads_tab.add_download(download_id, game['title'])
        self.sidebar.set_active("downloads")
        
        threading.Thread(target=self.process_anker_download_flow,
                        args=(game['link'], game['title'], self.direct_anker_client, download_id),
                        daemon=True).start()
    
    def process_anker_download_flow(self, game_url, game_title, anker, download_id):
        self.download_status_updated.emit(download_id, "🔗 Fetching direct link...", 0.1)
        
        try:
            final_url, error = anker.get_download_link(game_url)
            
            if error or not final_url:
                self.download_status_updated.emit(download_id, f"❌ Error: {error}. Opening page...", 0)
                time.sleep(2)
                webbrowser.open(game_url)
                return
            
            self.download_status_updated.emit(download_id, "🔍 Resolving final link...", 0.3)
            real_file_url, suggested_name = anker.resolve_final_link(final_url)
            
            if not suggested_name:
                suggested_name = game_title.strip()
            
            self.download_prompt_ready.emit(real_file_url, suggested_name, anker.session, download_id)
            
        except Exception as e:
            print(f"[DEBUG] Error: {e}")
            self.download_status_updated.emit(download_id, f"❌ Error: {str(e)}", 0)
    
    @pyqtSlot(str, str, object, str)
    def prompt_download(self, url, default_name, session, download_id):
        if "ankergames.net" in url and "treasure-box" in url:
            self.download_status_updated.emit(download_id, "⚠ Opening manual download page...", 1.0)
            time.sleep(1)
            webbrowser.open(url)
            return
        
        initial_dir = self.settings_manager.get("default_download_path", "")
        if not os.path.exists(initial_dir):
            initial_dir = str(Path.home() / "Downloads")
        
        save_path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            initial_dir
        )

        if save_path:
            item_widget = self.downloads_tab.items.get(download_id)
            
            def progress_callback(text, progress):
                self.download_status_updated.emit(download_id, text, progress)
            
            def run_download():
                self.download_status_updated.emit(download_id, "⏳ Preparing download...", 0)
                time.sleep(0.5)
                
                if session:
                    if "Referer" in session.headers:
                        del session.headers["Referer"]
                    if "X-Requested-With" in session.headers:
                        del session.headers["X-Requested-With"]
                
                result = downloader.download_file(url, save_path, progress_callback, 
                                                 item_widget.control_flags if item_widget else {"paused": False, "stopped": False}, 
                                                 session=session)
                
                self.download_finished.emit(download_id, result, save_path)
            
            threading.Thread(target=run_download, daemon=True).start()
        else:
            self.download_status_updated.emit(download_id, "❌ Download cancelled", 0)

    @pyqtSlot(str, str, float)
    def update_download_status(self, download_id, text, progress):
        item = self.downloads_tab.items.get(download_id)
        if item:
            item.update_progress(text, progress)

    @pyqtSlot(str, str, str)
    def on_download_finished(self, download_id, result, save_path):
        if result == "SUCCESS":
            self.update_download_status(download_id, f"✅ Complete: {os.path.basename(save_path)}", 1.0)
            
            def final_cleanup():
                try:
                    os.startfile(os.path.dirname(save_path))
                except:
                    pass
                # Keep it there for a bit then maybe allow removal?
            
            QTimer.singleShot(2000, final_cleanup)
        elif result == "STOPPED":
            self.update_download_status(download_id, "⏹ Download Stopped", 0)
        elif result == "ERROR":
            self.update_download_status(download_id, "❌ Error occurred", 0)
        elif result.startswith("ERROR"):
             # Show error for a moment then close
             pass # The download item will show the error
    
    def handle_html_fallback(self, url):
        print(f"[ERROR] Download URL returned HTML: {url}")
        webbrowser.open(url)
    
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.exec()
    
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

# =========================================================================
# APPLICATION ENTRY POINT
# =========================================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    window = GameSearchApp()
    
    # Center window
    screen = QApplication.primaryScreen().geometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)
    
    if window.settings_manager.get("disable_splash", False):
        window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
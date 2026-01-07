# ui/patcher/goldberg_tab.py
import threading

from core import patcher, steam_utils
from core.path_utils import get_tools_dir
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from ui.core.components import GamePatcherCard, LoadingWidget
from ui.core.styles import COLORS, STYLESHEET


class GoldbergTab(QWidget):
    patch_finished = pyqtSignal(bool, str)
    revert_finished = pyqtSignal(bool, str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self._shared_steam_games = []
        self._is_scanning = False

        self.patch_finished.connect(self.on_patch_finished)
        self.revert_finished.connect(self.on_revert_finished)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header + Refresh
        header_layout = QHBoxLayout()
        title_vlayout = QVBoxLayout()

        title = QLabel("🛠  Steam Patcher")
        title.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {COLORS['text_primary']};"
        )
        title_vlayout.addWidget(title)

        subtitle = QLabel(
            "Apply Goldberg Emulator to your installed Steam games in one click."
        )
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        title_vlayout.addWidget(subtitle)
        header_layout.addLayout(title_vlayout)

        # Info Toggle
        self.info_visible = False
        self.toggle_info_btn = QPushButton("❔ What is Goldberg?")
        self.toggle_info_btn.setFixedSize(160, 40)
        self.toggle_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_info_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: {COLORS['bg_secondary']}; 
                color: {COLORS['text_primary']}; 
                border-radius: 8px; 
                font-weight: 600; 
                border: 1px solid {COLORS['border']};
            }}
            QPushButton:hover {{ 
                background: {COLORS['bg_card_hover']};
                border: 1px solid {COLORS['accent_primary']};
            }}
        """)
        header_layout.addWidget(self.toggle_info_btn)

        header_layout.addStretch()

        self.manual_patch_btn = QPushButton("📂  Manual Path")
        self.manual_patch_btn.setFixedSize(140, 40)
        self.manual_patch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.manual_patch_btn.clicked.connect(self.manual_folder_patch)
        header_layout.addWidget(self.manual_patch_btn)

        self.refresh_steam_btn = QPushButton("🔄  Scan Library")
        self.refresh_steam_btn.setFixedSize(140, 40)
        self.refresh_steam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_steam_btn.clicked.connect(self.request_library_scan)
        header_layout.addWidget(self.refresh_steam_btn)

        layout.addLayout(header_layout)

        # Info Frame (Collapsible)
        self.info_frame = QFrame()
        self.info_frame.setVisible(False)
        self.info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS["bg_secondary"]}, stop:1 {COLORS["bg_primary"]});
                border: 1px solid {COLORS["accent_primary"]};
                border-radius: 12px;
            }}
        """)
        if_layout = QVBoxLayout(self.info_frame)
        if_layout.setContentsMargins(20, 20, 20, 20)

        if_title = QLabel("🚀 Goldberg Steam Emulator")
        if_title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        if_layout.addWidget(if_title)

        if_content = QLabel(
            "The <b>Goldberg Emulator</b> is a high-performance Steam API emulator. It allows you to:<br><br>"
            "• <b>Play games without Steam:</b> Run your installed games without the Steam client background processes.<br>"
            "• <b>LAN Support:</b> Easily play multiplayer games over a Local Area Network.<br>"
            "• <b>Privacy & Portability:</b> Keep your game library portable and run games offline with zero client tracking.<br><br>"
            "<i style='color: #888;'>How it works: It replaces steam_api.dll or steam_api64.dll with a specialized version that handles Steam calls directly.</i>"
        )
        if_content.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 14px; line-height: 1.6;"
        )
        if_content.setWordWrap(True)
        if_layout.addWidget(if_content)

        layout.addWidget(self.info_frame)

        def toggle_info():
            self.info_visible = not self.info_visible
            self.info_frame.setVisible(self.info_visible)
            self.toggle_info_btn.setText(
                "❌ Close Info" if self.info_visible else "❔ What is Goldberg?"
            )

        self.toggle_info_btn.clicked.connect(toggle_info)

        # Search for installed games
        self.steam_search_input = QLineEdit()
        self.steam_search_input.setPlaceholderText("Filter your Steam library...")
        self.steam_search_input.setFixedHeight(45)
        self.steam_search_input.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;"
        )
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

        self.setLayout(layout)
        QTimer.singleShot(500, self.request_library_scan)

    def manual_folder_patch(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Game Folder (must contain steam_api.dll or steam_api64.dll)"
        )
        if not folder:
            return

        import os

        # We need an AppID for Goldberg.
        appid, ok = QInputDialog.getInt(
            self, "AppID Required", "Enter Steam AppID for this game:", 0, 0, 9999999
        )
        if not ok:
            return

        game = {"name": os.path.basename(folder), "id": appid, "full_path": folder}
        self.trigger_patch(game)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def request_library_scan(self):
        if self._is_scanning:
            return
        self._is_scanning = True
        self.steam_search_input.setText("")
        self.clear_layout(self.steam_container_layout)
        self.loader = LoadingWidget("Scanning Steam Libraries")
        self.steam_container_layout.addWidget(self.loader)

        def scan():
            try:
                games = steam_utils.get_installed_games()
                games.sort(key=lambda x: x["name"])
                QMetaObject.invokeMethod(
                    self,
                    "on_scan_completed",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(list, games),
                )
            except Exception as e:
                print(f"[ERROR] Goldberg scan failed: {e}")
                QMetaObject.invokeMethod(
                    self,
                    "on_scan_failed",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, str(e)),
                )
            finally:
                self._is_scanning = False

        threading.Thread(target=scan, daemon=True).start()

    @pyqtSlot(list)
    def on_scan_completed(self, games):
        if hasattr(self, "loader"):
            self.loader.stop()
            self.loader.setParent(None)
            del self.loader
        self._shared_steam_games = games
        self.display_steam_games()

    @pyqtSlot(str)
    def on_scan_failed(self, error_msg):
        if hasattr(self, "loader"):
            self.loader.stop()
            self.loader.setParent(None)
            del self.loader

        self.clear_layout(self.steam_container_layout)
        err_label = QLabel(
            f"❌ Scan Failed: {error_msg}\n\nPlease check your Steam installation."
        )
        err_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-weight: bold;")
        err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_container_layout.addWidget(err_label)

    def display_steam_games(self, filtered_list=None):
        self.clear_layout(self.steam_container_layout)
        games = filtered_list if filtered_list is not None else self._shared_steam_games
        if not games:
            empty = QLabel("No games found or Steam not detected.")
            empty.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 14px; margin-top: 40px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout.addWidget(empty)
            return
        for game in games:
            card = GamePatcherCard(
                game, "Goldberg", self.trigger_patch, self.trigger_revert
            )
            self.steam_container_layout.addWidget(card)

    def filter_steam_games(self, text):
        if self._is_scanning:
            return
        filtered = [
            g for g in self._shared_steam_games if text.lower() in g["name"].lower()
        ]
        self.display_steam_games(filtered)

    def trigger_patch(self, game):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Apply Patch")
        msg_box.setText(f"Apply Goldberg Emulator to {game['name']}?")
        msg_box.setInformativeText(
            "This will replace original Steam DLLs with emulator versions (backups will be created)."
        )
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app:
                self.main_app.statusBar().showMessage(f"Patching {game['name']}...")

            def run():
                nick = (
                    self.main_app.settings_manager.get("goldberg_nickname", "AIOUser")
                    if self.main_app
                    else "AIOUser"
                )
                lang = (
                    self.main_app.settings_manager.get("goldberg_language", "english")
                    if self.main_app
                    else "english"
                )
                success, log_msg = patcher.patch_game(
                    game["full_path"],
                    game["id"],
                    get_tools_dir(),
                    nickname=nick,
                    language=lang,
                )
                self.patch_finished.emit(success, log_msg)

            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished(self, success, log_msg):
        if self.main_app:
            self.main_app.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(
                self,
                "Patch Successful",
                "The Goldberg patch has been applied successfully!\n\n" + log_msg,
            )
        else:
            QMessageBox.critical(
                self, "Patch Failed", "Failed to apply patch:\n\n" + log_msg
            )

    def trigger_revert(self, game):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Revert Patch")
        msg_box.setText(f"Restore original files for {game['name']}?")
        msg_box.setInformativeText(
            "This will restore the .bak files and remove Goldberg settings. It only works if a backup exists."
        )
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app:
                self.main_app.statusBar().showMessage(f"Reverting {game['name']}...")

            def run():
                success, log_msg = patcher.revert_patch(game["full_path"])
                self.revert_finished.emit(success, log_msg)

            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_revert_finished(self, success, log_msg):
        if self.main_app:
            self.main_app.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(
                self,
                "Revert Successful",
                "Original files have been restored!\n\n" + log_msg,
            )
        else:
            QMessageBox.warning(
                self, "Revert Failed", "Could not revert patch:\n\n" + log_msg
            )

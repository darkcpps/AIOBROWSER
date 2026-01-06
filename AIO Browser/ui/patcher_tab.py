# patcher_tab.py
import threading
import os
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.styles import COLORS, STYLESHEET
from core import patcher, steam_utils

class PatcherTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent # Reference to GameSearchApp for status bar and signals
        self.initUI()

    def initUI(self):
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
        self.setLayout(main_layout)

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
        QTimer.singleShot(1000, self.load_steam_games_creamapi)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

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
        filtered = [g for g in self.installed_steam_games if text.lower() in g["name"].lower()]
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
                    background-color: {COLORS["bg_card"]};
                    border-radius: 12px;
                    border: 1px solid {COLORS["border"]};
                }}
                QFrame#SteamCard:hover {{
                    border: 1px solid {COLORS["accent_primary"]};
                    background-color: {COLORS["bg_card_hover"]};
                }}
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(25, 0, 25, 0)
            info = QVBoxLayout(); info.setAlignment(Qt.AlignmentFlag.AlignVCenter); info.setSpacing(2)
            name = QLabel(game["name"]); name.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;")
            info.addWidget(name)
            meta_layout = QHBoxLayout(); meta_layout.setSpacing(15)
            appid = QLabel(f"🆔 {game['id']}"); appid.setStyleSheet(f"font-size: 11px; color: {COLORS['accent_secondary']}; background: transparent; font-weight: 600;")
            meta_layout.addWidget(appid)
            dir_name = os.path.basename(str(game["full_path"]))
            path = QLabel(f"📂 {dir_name}"); path.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;")
            meta_layout.addWidget(path); meta_layout.addStretch()
            info.addLayout(meta_layout); c_layout.addLayout(info, 1)
            btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
            revert_btn = QPushButton("↩"); revert_btn.setFixedSize(40, 40); revert_btn.setCursor(Qt.CursorShape.PointingHandCursor); revert_btn.setToolTip("Revert patch (restore backups)")
            revert_btn.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']};")
            revert_btn.clicked.connect(lambda checked, g=game: self.trigger_revert(g))
            btn_layout.addWidget(revert_btn)
            apply_btn = QPushButton("Apply Patcher"); apply_btn.setFixedSize(140, 40); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['accent_primary']}; color: white; border-radius: 8px; font-weight: 600; }} QPushButton:hover {{ background-color: {COLORS['accent_secondary']}; }}")
            apply_btn.clicked.connect(lambda checked, g=game: self.trigger_patch(g))
            btn_layout.addWidget(apply_btn); c_layout.addLayout(btn_layout)
            self.steam_container_layout.addWidget(card)

    def trigger_patch(self, game):
        msg_box = QMessageBox(self); msg_box.setWindowTitle("Apply Patch"); msg_box.setText(f"Apply Goldberg Emulator to {game['name']}?"); msg_box.setInformativeText("This will replace original Steam DLLs with emulator versions (backups will be created).")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.Yes); msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app: self.main_app.statusBar().showMessage(f"Patching {game['name']}...")
            def run():
                nick = self.main_app.settings_manager.get("goldberg_nickname", "AIOUser") if self.main_app else "AIOUser"
                lang = self.main_app.settings_manager.get("goldberg_language", "english") if self.main_app else "english"
                success, log_msg = patcher.patch_game(game["full_path"], game["id"], "tools", nickname=nick, language=lang)
                QMetaObject.invokeMethod(self, "on_patch_finished", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, log_msg))
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success: QMessageBox.information(self, "Patch Successful", "The Goldberg patch has been applied successfully!\n\n" + log_msg)
        else: QMessageBox.critical(self, "Patch Failed", "Failed to apply patch:\n\n" + log_msg)

    def trigger_revert(self, game):
        msg_box = QMessageBox(self); msg_box.setWindowTitle("Revert Patch"); msg_box.setText(f"Restore original files for {game['name']}?"); msg_box.setInformativeText("This will restore the .bak files and remove Goldberg settings. It only works if a backup exists.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.No); msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app: self.main_app.statusBar().showMessage(f"Reverting {game['name']}...")
            def run():
                success, log_msg = patcher.revert_patch(game["full_path"])
                QMetaObject.invokeMethod(self, "on_revert_finished", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, log_msg))
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_revert_finished(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success: QMessageBox.information(self, "Revert Successful", "Original files have been restored!\n\n" + log_msg)
        else: QMessageBox.warning(self, "Revert Failed", "Could not revert patch:\n\n" + log_msg)

    def load_steam_games_creamapi(self):
        self.clear_layout(self.steam_container_layout_creamapi)
        state_label = QLabel("Scanning Steam libraries..."); state_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;"); state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_container_layout_creamapi.addWidget(state_label)
        def run_scan():
            try:
                self.installed_steam_games_creamapi = steam_utils.get_installed_games()
                QMetaObject.invokeMethod(self, "display_steam_games_creamapi", Qt.ConnectionType.QueuedConnection)
            except Exception as e: print(f"[ERROR] Scan failed: {e}")
        threading.Thread(target=run_scan, daemon=True).start()

    @pyqtSlot()
    def display_steam_games_creamapi(self): self.render_steam_games_creamapi(self.installed_steam_games_creamapi)

    def filter_steam_games_creamapi(self, text):
        filtered = [g for g in self.installed_steam_games_creamapi if text.lower() in g["name"].lower()]; self.render_steam_games_creamapi(filtered)

    def render_steam_games_creamapi(self, games):
        self.clear_layout(self.steam_container_layout_creamapi)
        if not games:
            empty = QLabel("No games found or Steam not detected."); empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; margin-top: 40px;"); empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout_creamapi.addWidget(empty); return
        for game in games:
            card = QFrame(); card.setObjectName("SteamCard"); card.setFixedHeight(85)
            card.setStyleSheet(f"QFrame#SteamCard {{ background-color: {COLORS['bg_card']}; border-radius: 12px; border: 1px solid {COLORS['border']}; }} QFrame#SteamCard:hover {{ border: 1px solid {COLORS['accent_primary']}; background-color: {COLORS['bg_card_hover']}; }}")
            c_layout = QHBoxLayout(card); c_layout.setContentsMargins(25, 0, 25, 0)
            info = QVBoxLayout(); info.setAlignment(Qt.AlignmentFlag.AlignVCenter); info.setSpacing(2)
            name = QLabel(game["name"]); name.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']}; background: transparent;"); info.addWidget(name)
            meta_layout = QHBoxLayout(); meta_layout.setSpacing(15)
            appid = QLabel(f"🆔 {game['id']}"); appid.setStyleSheet(f"font-size: 11px; color: {COLORS['accent_secondary']}; background: transparent; font-weight: 600;"); meta_layout.addWidget(appid)
            dir_name = os.path.basename(str(game["full_path"])); path = QLabel(f"📂 {dir_name}"); path.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: transparent;"); meta_layout.addWidget(path); meta_layout.addStretch()
            info.addLayout(meta_layout); c_layout.addLayout(info, 1)
            btn_layout = QHBoxLayout(); btn_layout.setSpacing(10)
            revert_btn = QPushButton("↩"); revert_btn.setFixedSize(40, 40); revert_btn.setCursor(Qt.CursorShape.PointingHandCursor); revert_btn.setToolTip("Revert patch (restore backups)")
            revert_btn.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']};")
            revert_btn.clicked.connect(lambda checked, g=game: self.trigger_revert_creamapi(g)); btn_layout.addWidget(revert_btn)
            apply_btn = QPushButton("Apply CreamAPI"); apply_btn.setFixedSize(140, 40); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['accent_primary']}; color: white; border-radius: 8px; font-weight: 600; }} QPushButton:hover {{ background-color: {COLORS['accent_secondary']}; }}")
            apply_btn.clicked.connect(lambda checked, g=game: self.trigger_patch_creamapi(g)); btn_layout.addWidget(apply_btn); c_layout.addLayout(btn_layout)
            self.steam_container_layout_creamapi.addWidget(card)

    def trigger_patch_creamapi(self, game):
        dialog = QDialog(self); dialog.setWindowTitle("CreamAPI - DLC Configuration"); dialog.setFixedSize(500, 300); dialog.setStyleSheet(STYLESHEET)
        layout = QVBoxLayout(dialog); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        info_label = QLabel(f"Enter DLC IDs for {game['name']}:"); info_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLORS['text_primary']};"); layout.addWidget(info_label)
        help_label = QLabel("Enter one DLC ID per line (e.g., 123456, 789012)"); help_label.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};"); layout.addWidget(help_label)
        dlc_input = QTextEdit(); dlc_input.setPlaceholderText("123456\n789012\n345678"); dlc_input.setStyleSheet(f"QTextEdit {{ background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 10px; font-size: 13px; }}")
        layout.addWidget(dlc_input); btn_layout = QHBoxLayout(); btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedSize(100, 35); cancel_btn.clicked.connect(dialog.reject); btn_layout.addWidget(cancel_btn)
        apply_btn = QPushButton("Apply"); apply_btn.setFixedSize(100, 35); apply_btn.setStyleSheet(f"QPushButton {{ background-color: {COLORS['accent_primary']}; color: white; border-radius: 8px; font-weight: 600; }} QPushButton:hover {{ background-color: {COLORS['accent_secondary']}; }}")
        apply_btn.clicked.connect(dialog.accept); btn_layout.addWidget(apply_btn); layout.addLayout(btn_layout)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dlc_text = dlc_input.toPlainText().strip()
            dlc_ids = [line.strip() for line in dlc_text.split("\n") if line.strip()] if dlc_text else None
            msg_box = QMessageBox(self); msg_box.setWindowTitle("Apply Patch"); msg_msg = f"Apply CreamAPI to {game['name']}?"
            if dlc_ids: msg_msg += f"\n\nDLC IDs: {', '.join(dlc_ids[:5])}"; 
            if dlc_ids and len(dlc_ids) > 5: msg_msg += f" (+{len(dlc_ids) - 5} more)"
            msg_box.setText(msg_msg); msg_box.setInformativeText("This will replace original Steam DLLs with CreamAPI versions (backups will be created)."); msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.Yes); msg_box.setStyleSheet(STYLESHEET)
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                if self.main_app: self.main_app.statusBar().showMessage(f"Patching {game['name']} with CreamAPI...")
                def run():
                    success, log_msg = patcher.patch_game_creamapi(game["full_path"], game["id"], "tools", dlc_ids=dlc_ids)
                    QMetaObject.invokeMethod(self, "on_patch_finished_creamapi", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, log_msg))
                threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished_creamapi(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success: QMessageBox.information(self, "Patch Successful", "The CreamAPI patch has been applied successfully!\n\n" + log_msg)
        else: QMessageBox.critical(self, "Patch Failed", "Failed to apply patch:\n\n" + log_msg)

    def trigger_revert_creamapi(self, game):
        msg_box = QMessageBox(self); msg_box.setWindowTitle("Revert Patch"); msg_box.setText(f"Restore original files for {game['name']}?"); msg_box.setInformativeText("This will restore the .bak files and remove CreamAPI configuration. It only works if a backup exists.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.No); msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app: self.main_app.statusBar().showMessage(f"Reverting {game['name']}...")
            def run():
                success, log_msg = patcher.revert_creamapi_patch(game["full_path"])
                QMetaObject.invokeMethod(self, "on_revert_finished_creamapi", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, log_msg))
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_revert_finished_creamapi(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success: QMessageBox.information(self, "Revert Successful", "Original files have been restored!\n\n" + log_msg)
        else: QMessageBox.warning(self, "Revert Failed", "Could not revert patch:\n\n" + log_msg)

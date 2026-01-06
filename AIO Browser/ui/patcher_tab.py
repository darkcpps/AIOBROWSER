# patcher_tab.py
import threading
import os
import subprocess
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.styles import COLORS, STYLESHEET
from core import patcher, steam_utils, greenluma_patcher
from core.path_utils import get_tools_dir
from ui.components import LoadingWidget, GamePatcherCard

class PatcherTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("[DEBUG] Initializing PatcherTab...")
        self.main_app = parent # Reference to GameSearchApp for status bar and signals
        self._shared_steam_games = []
        self._is_scanning = False
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.patcher_tabs = QTabWidget()

        # Create the GreenLuma sub-tab
        self.greenluma_tab = QWidget()
        self.setup_greenluma_subtab()

        # Create the Goldberg sub-tab
        self.goldberg_tab = QWidget()
        self.setup_goldberg_subtab()

        self.patcher_tabs.addTab(self.greenluma_tab, "GreenLuma (DO NOT USE)")
        self.patcher_tabs.addTab(self.goldberg_tab, "Goldberg (Emulator)")

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
        self.refresh_steam_btn.clicked.connect(self.request_library_scan)
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
        QTimer.singleShot(500, self.request_library_scan)


    def setup_greenluma_subtab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header + Refresh
        header_layout = QHBoxLayout()
        title_vlayout = QVBoxLayout()

        title = QLabel("🐳  GreenLuma")
        title.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {COLORS['text_primary']};")
        title_vlayout.addWidget(title)

        subtitle = QLabel("The state-of-the-art Steam unlocker. Bypass DLC restrictions without modifying game files.")
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']};")
        title_vlayout.addWidget(subtitle)
        header_layout.addLayout(title_vlayout)

        header_layout.addStretch()

        # Action Buttons
        self.open_gl_folder_btn = QPushButton("📂  Open GL Folder")
        self.open_gl_folder_btn.setFixedSize(140, 40)
        self.open_gl_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_gl_folder_btn.clicked.connect(lambda: os.startfile(os.path.abspath("tools/Greenluma/NormalMode")))
        header_layout.addWidget(self.open_gl_folder_btn)

        self.launch_gl_btn = QPushButton("🚀  Launch Injector")
        self.launch_gl_btn.setFixedSize(140, 40)
        self.launch_gl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_gl_btn.setStyleSheet(f"background-color: {COLORS['accent_primary']}; color: white; border-radius: 8px; font-weight: 600;")
        self.launch_gl_btn.clicked.connect(self.launch_greenluma)
        header_layout.addWidget(self.launch_gl_btn)

        self.refresh_steam_btn_gl = QPushButton("🔄  Scan Library")
        self.refresh_steam_btn_gl.setFixedSize(140, 40)
        self.refresh_steam_btn_gl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_steam_btn_gl.clicked.connect(self.request_library_scan)
        header_layout.addWidget(self.refresh_steam_btn_gl)

        layout.addLayout(header_layout)

        # Steam Status Warning
        self.steam_status_bar = QFrame()
        self.steam_status_bar.setFixedHeight(50)
        self.steam_status_bar.setStyleSheet(f"background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;")
        ss_layout = QHBoxLayout(self.steam_status_bar)
        
        self.ss_label = QLabel("⚠️  Please ensure Steam is CLOSED before using GreenLuma.")
        self.ss_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px; border: none;")
        ss_layout.addWidget(self.ss_label)
        
        refresh_ss_btn = QPushButton("Check Status")
        refresh_ss_btn.setFixedWidth(100)
        refresh_ss_btn.setStyleSheet("background: #ef4444; color: white; border-radius: 4px; font-size: 11px; font-weight: bold;")
        def check_steam():
            import subprocess
            try:
                # Use tasklist to see if steam is running
                res = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq steam.exe'], capture_output=True, text=True)
                if "steam.exe" in res.stdout.lower():
                    self.ss_label.setText("❌ Steam is currently RUNNING. Close it before proceeding!")
                    self.ss_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px; border: none;")
                    self.steam_status_bar.setStyleSheet(f"background-color: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;")
                else:
                    self.ss_label.setText("✅ Steam is CLOSED. You are safe to use the injector.")
                    self.ss_label.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 13px; border: none;")
                    self.steam_status_bar.setStyleSheet(f"background-color: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px;")
            except Exception as e:
                print(f"[ERROR] Steam check failed: {e}")

        refresh_ss_btn.clicked.connect(check_steam)
        ss_layout.addStretch()
        ss_layout.addWidget(refresh_ss_btn)
        layout.addWidget(self.steam_status_bar)
        QTimer.singleShot(500, check_steam) # Initial check

        # Current AppList Viewer
        self.active_applist_label = QLabel("Current AppList: Loading...")
        self.active_applist_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-style: italic; margin-top: 5px;")
        layout.addWidget(self.active_applist_label)

        # GreenLuma Sub-Tabs (My Games / Add New)
        self.gl_mode_tabs = QTabWidget()
        self.gl_mode_tabs.setStyleSheet("QTabWidget::pane { border: none; } QTabBar::tab { background: #222; padding: 10px 20px; border-radius: 5px; margin-right: 5px; } QTabBar::tab:selected { background: #3b82f6; }")
        
        # TAB 1: Installed Games
        self.gl_installed_tab = QWidget()
        gl_installed_layout = QVBoxLayout(self.gl_installed_tab)
        gl_installed_layout.setContentsMargins(0, 15, 0, 0)

        # Search for installed games
        self.steam_search_input_gl = QLineEdit()
        self.steam_search_input_gl.setPlaceholderText("Filter your installed Steam library...")
        self.steam_search_input_gl.setFixedHeight(45)
        self.steam_search_input_gl.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;")
        self.steam_search_input_gl.textChanged.connect(self.filter_steam_games_gl)
        gl_installed_layout.addWidget(self.steam_search_input_gl)

        self.steam_scroll_gl = QScrollArea()
        self.steam_scroll_gl.setWidgetResizable(True)
        self.steam_scroll_gl.setStyleSheet("background: transparent; border: none;")
        self.steam_container_gl = QWidget()
        self.steam_container_layout_gl = QVBoxLayout(self.steam_container_gl)
        self.steam_container_layout_gl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steam_container_layout_gl.setSpacing(12)
        self.steam_scroll_gl.setWidget(self.steam_container_gl)
        gl_installed_layout.addWidget(self.steam_scroll_gl)

        # TAB 2: Add New Games (Global Search)
        self.gl_search_tab = QWidget()
        gl_search_layout = QVBoxLayout(self.gl_search_tab)
        gl_search_layout.setContentsMargins(0, 15, 0, 0)

        search_header = QLabel("Search Steam for games to add to your AppList.")
        search_header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; margin-bottom: 5px;")
        gl_search_layout.addWidget(search_header)

        search_bar_layout = QHBoxLayout()
        self.gl_global_search_input = QLineEdit()
        self.gl_global_search_input.setPlaceholderText("Search Game Name or AppID...")
        self.gl_global_search_input.setFixedHeight(45)
        self.gl_global_search_input.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;")
        self.gl_global_search_input.returnPressed.connect(self.perform_global_gl_search)
        search_bar_layout.addWidget(self.gl_global_search_input)

        self.gl_global_search_btn = QPushButton("🔍 Search")
        self.gl_global_search_btn.setFixedSize(100, 45)
        self.gl_global_search_btn.setStyleSheet(f"background: {COLORS['accent_primary']}; color: white; border-radius: 10px; font-weight: bold;")
        self.gl_global_search_btn.clicked.connect(self.perform_global_gl_search)
        search_bar_layout.addWidget(self.gl_global_search_btn)
        gl_search_layout.addLayout(search_bar_layout)

        self.gl_search_scroll = QScrollArea()
        self.gl_search_scroll.setWidgetResizable(True)
        self.gl_search_scroll.setStyleSheet("background: transparent; border: none;")
        self.gl_search_container = QWidget()
        self.gl_search_layout = QVBoxLayout(self.gl_search_container)
        self.gl_search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gl_search_layout.setSpacing(12)
        self.gl_search_scroll.setWidget(self.gl_search_container)
        gl_search_layout.addWidget(self.gl_search_scroll)

        self.gl_mode_tabs.addTab(self.gl_installed_tab, "📦 DLC Manager (My Games)")
        self.gl_mode_tabs.addTab(self.gl_search_tab, "🚀 Game Manager (Add New)")
        
        # TAB 3: Managed active files
        self.gl_active_tab = QWidget()
        gl_active_layout = QVBoxLayout(self.gl_active_tab)
        gl_active_layout.setContentsMargins(0, 15, 0, 0)
        
        active_header = QLabel("Manage current AppList IDs in your Steam folder.")
        active_header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; margin-bottom: 5px;")
        gl_active_layout.addWidget(active_header)
        
        self.active_list_scroll = QScrollArea()
        self.active_list_scroll.setWidgetResizable(True)
        self.active_list_scroll.setStyleSheet("background: transparent; border: none;")
        self.active_list_container = QWidget()
        self.active_list_layout = QVBoxLayout(self.active_list_container)
        self.active_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_list_scroll.setWidget(self.active_list_container)
        gl_active_layout.addWidget(self.active_list_scroll)
        
        self.gl_mode_tabs.addTab(self.gl_active_tab, "📝 Active AppList")
        
        layout.addWidget(self.gl_mode_tabs)

        self.greenluma_tab.setLayout(layout)


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
        """Unified scan that updates all sub-tabs."""
        print("[ACTION] Requesting library scan...")
        if self._is_scanning: 
            print("[DEBUG] Scan already in progress, ignoring request.")
            return
        self._is_scanning = True
        
        # Clear search inputs to avoid confusion
        self.steam_search_input.setText("")
        self.steam_search_input_gl.setText("")
        
        # Show loaders in both tabs
        self.clear_layout(self.steam_container_layout)
        self.goldberg_loader = LoadingWidget("Scanning Steam Libraries")
        self.steam_container_layout.addWidget(self.goldberg_loader)

        self.clear_layout(self.steam_container_layout_gl)
        self.gl_loader = LoadingWidget("Scanning Steam Libraries")
        self.steam_container_layout_gl.addWidget(self.gl_loader)

        def scan():
            try:
                print("[PROCESS] Searching for Steam libraries and games...")
                self._shared_steam_games = steam_utils.get_installed_games()
                # Sort alphabetically for better UX
                print(f"[PROCESS] Found {len(self._shared_steam_games)} games. Sorting list...")
                self._shared_steam_games.sort(key=lambda x: x["name"])
                QTimer.singleShot(0, self.on_scan_completed)
            except Exception as e:
                print(f"[ERROR] Scan process failed: {e}")
                self._is_scanning = False
        threading.Thread(target=scan, daemon=True).start()

    def on_scan_completed(self):
        print("[UI] Scan completed. Updating displays...")
        self._is_scanning = False
        if hasattr(self, 'goldberg_loader'): self.goldberg_loader.stop(); self.goldberg_loader.setParent(None)
        if hasattr(self, 'gl_loader'): self.gl_loader.stop(); self.gl_loader.setParent(None)
        
        self.display_steam_games()
        self.display_steam_games_gl()
        self.refresh_active_applist_label()

    @pyqtSlot()
    def refresh_active_applist_label(self):
        """Update the label and the management tab showing what's currently in Steam/AppList."""
        try:
            current_ids = greenluma_patcher.get_current_applist()
            
            # Update label
            if current_ids:
                count = len(current_ids)
                text = f"🟢 Current Active AppList: {count} IDs ({', '.join(current_ids[:5])}{'...' if count > 5 else ''})"
            else:
                text = "⚪ Current Active AppList: Empty (Patch a game to start)"
            self.active_applist_label.setText(text)
            
            # Update management tab list
            self.clear_layout(self.active_list_layout)
            if not current_ids:
                self.active_list_layout.addWidget(QLabel("No active AppIDs found in Steam/AppList."))
            else:
                for aid in current_ids:
                    row = QFrame()
                    row.setStyleSheet(f"background: {COLORS['bg_secondary']}; border-radius: 8px; padding: 10px;")
                    row_layout = QHBoxLayout(row)
                    row_layout.addWidget(QLabel(f"🆔 {aid}"))
                    row_layout.addStretch()
                    del_btn = QPushButton("🗑️ Remove")
                    del_btn.setFixedSize(80, 25)
                    del_btn.setStyleSheet("background: #ef4444; color: white; border-radius: 4px; font-size: 11px;")
                    
                    # Logic to delete just one ID
                    def make_delete(app_id_to_del):
                        def delete_id():
                            steam_path = greenluma_patcher.get_steam_path()
                            if steam_path:
                                app_list_dir = steam_path / "AppList"
                                for f in app_list_dir.glob("*.txt"):
                                    try:
                                        with open(f, "r") as rfile:
                                            if rfile.read().strip() == app_id_to_del:
                                                f.unlink()
                                                break
                                    except: pass
                                self.refresh_active_applist_label()
                        return delete_id

                    del_btn.clicked.connect(make_delete(aid))
                    row_layout.addWidget(del_btn)
                    self.active_list_layout.addWidget(row)
        except Exception as e:
            print(f"[ERROR] Failed to refresh active AppList: {e}")

    def display_steam_games(self, filtered_list=None):
        self.clear_layout(self.steam_container_layout)
        games = filtered_list if filtered_list is not None else self._shared_steam_games
        
        if not games:
            empty = QLabel("No games found or Steam not detected.")
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px; margin-top: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout.addWidget(empty)
            return

        for game in games:
            card = GamePatcherCard(game, "Goldberg", self.trigger_patch, self.trigger_revert)
            self.steam_container_layout.addWidget(card)

    def filter_steam_games(self, text):
        if self._is_scanning: return
        filtered = [g for g in self._shared_steam_games if text.lower() in g["name"].lower()]
        self.display_steam_games(filtered)

    def display_steam_games_gl(self, filtered_list=None):
        self.clear_layout(self.steam_container_layout_gl)
        games = filtered_list if filtered_list is not None else self._shared_steam_games
        
        if not games:
            empty = QLabel("No Steam games found."); empty.setStyleSheet(f"color: {COLORS['text_secondary']};"); empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout_gl.addWidget(empty)
            return
            
        for g in games:
            card = GamePatcherCard(g, "GreenLuma", self.trigger_patch_gl, self.trigger_revert_gl)
            self.steam_container_layout_gl.addWidget(card)

    def filter_steam_games_gl(self, text):
        if self._is_scanning: return
        filtered = [g for g in self._shared_steam_games if text.lower() in g["name"].lower()]
        self.display_steam_games_gl(filtered)

    def trigger_patch(self, game):
        msg_box = QMessageBox(self); msg_box.setWindowTitle("Apply Patch"); msg_box.setText(f"Apply Goldberg Emulator to {game['name']}?"); msg_box.setInformativeText("This will replace original Steam DLLs with emulator versions (backups will be created).")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No); msg_box.setDefaultButton(QMessageBox.StandardButton.Yes); msg_box.setStyleSheet(STYLESHEET)
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if self.main_app: self.main_app.statusBar().showMessage(f"Patching {game['name']}...")
            def run():
                nick = self.main_app.settings_manager.get("goldberg_nickname", "AIOUser") if self.main_app else "AIOUser"
                lang = self.main_app.settings_manager.get("goldberg_language", "english") if self.main_app else "english"
                success, log_msg = patcher.patch_game(game["full_path"], game["id"], get_tools_dir(), nickname=nick, language=lang)
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

    # =========================================================================
    # GREENLUMA 2025 LOGIC
    # =========================================================================
    def trigger_patch_gl(self, game):
        print(f"[ACTION] User clicked GreenLuma Patch for: {game['name']} (AppID: {game['id']})")
        dialog = QDialog(self); dialog.setWindowTitle(f"GreenLuma Config - {game['name']}"); dialog.setFixedSize(550, 500); dialog.setStyleSheet(STYLESHEET)
        layout = QVBoxLayout(dialog); layout.setContentsMargins(25, 25, 25, 25); layout.setSpacing(15)
        
        header = QLabel("GreenLuma AppList Manager"); header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(header)
        
        dlc_group = QGroupBox("Target AppIDs"); dlc_group.setStyleSheet("QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #333; margin-top: 10px; padding: 10px; }")
        dlc_layout = QVBoxLayout(dlc_group)
        
        dlc_header_layout = QHBoxLayout()
        dlc_label = QLabel("Enter IDs (Game + DLCs, one per line):"); dlc_label.setStyleSheet("color: #ccc; font-size: 12px;")
        fetch_btn = QPushButton("✨ Fetch IDs From Steam"); fetch_btn.setFixedWidth(160)
        fetch_btn.setStyleSheet(f"QPushButton {{ background: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; font-size: 11px; padding: 5px; }} QPushButton:hover {{ background: #333; }}")
        dlc_header_layout.addWidget(dlc_label); dlc_header_layout.addStretch(); dlc_header_layout.addWidget(fetch_btn)
        dlc_layout.addLayout(dlc_header_layout)
        
        dlc_input = QTextEdit(); dlc_input.setPlaceholderText("GameID\nDLC_ID1\nDLC_ID2"); dlc_input.setStyleSheet(f"background: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 5px; padding: 8px;")
        # Pre-fill with Game ID
        dlc_input.setPlainText(str(game['id']))
        dlc_layout.addWidget(dlc_input)
        layout.addWidget(dlc_group)
        
        def on_fetch():
            fetch_btn.setText("Fetching...")
            fetch_btn.setEnabled(False)
            def run():
                try:
                    appid = game['id']
                    print(f"[UI] Triggering DLC fetch for {appid}...")
                    dlc_list = steam_utils.fetch_dlcs(appid)
                    
                    ids_text = [str(appid)]
                    for d in dlc_list:
                        ids_text.append(f"{d['id']} = {d['name']}")
                    
                    final_text = "\n".join(ids_text)
                    print(f"[UI] Fetch complete. Updating text box with {len(dlc_list)} DLCs.")
                    
                    def update_ui():
                        print(f"[UI] Applying {len(dlc_list)} IDs to text box.")
                        dlc_input.setPlainText(final_text)
                        if self.main_app:
                            self.main_app.statusBar().showMessage(f"Successfully fetched {len(dlc_list)} DLCs for {game['name']}", 4000)
                        fetch_btn.setText("✨ Fetch IDs From Steam")
                        fetch_btn.setEnabled(True)
                    
                    # Use invokeMethod to ensure this runs in the GUI thread
                    QMetaObject.invokeMethod(self, "_safe_ui_callback", Qt.ConnectionType.QueuedConnection, Q_ARG(object, update_ui))
                except Exception as e:
                    print(f"[ERROR] UI Fetch Task Failed: {e}")
                    QMetaObject.invokeMethod(fetch_btn, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "❌ Fetch Failed"))
                    QTimer.singleShot(2000, lambda: fetch_btn.setEnabled(True))
                    QTimer.singleShot(2000, lambda: fetch_btn.setText("✨ Fetch IDs From Steam"))
            
            threading.Thread(target=run, daemon=True).start()
        
        fetch_btn.clicked.connect(on_fetch)
        
        # --- DISABLED AUTO FETCH PER USER REQUEST ---
        # QTimer.singleShot(100, on_fetch)

        # Stealth Mode Toggle
        stealth_cb = QCheckBox("🛡️  Enable Stealth Mode (Legit / NoHook)")
        stealth_cb.setChecked(True) # Recommended by standard managers
        stealth_cb.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(stealth_cb)

        help_text = QLabel("Note: GreenLuma works by adding AppIDs to its internal list.\n"
                           "Stealth Mode (NoHook) is safer but might not work for all games.\n"
                           "You must launch Steam using DLLInjector.exe after patching.")
        help_text.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setFixedSize(100, 35); cancel_btn.clicked.connect(dialog.reject); btn_layout.addWidget(cancel_btn)
        apply_btn = QPushButton("Update AppList"); apply_btn.setFixedSize(150, 35); apply_btn.setStyleSheet(f"background: {COLORS['accent_primary']}; color: white; font-weight: bold; border-radius: 5px;")
        apply_btn.clicked.connect(dialog.accept); btn_layout.addWidget(apply_btn); layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            print("[DEBUG] GreenLuma config dialog accepted.")
            dlc_text = dlc_input.toPlainText().strip()
            dlc_ids = [line.strip() for line in dlc_text.split("\n") if line.strip()]
            use_stealth = stealth_cb.isChecked()
            print(f"[DEBUG] IDs to patch: {dlc_ids}, Stealth Mode: {use_stealth}")
            
            if self.main_app: self.main_app.statusBar().showMessage(f"Updating GreenLuma list for {game['name']}...")
            def run():
                print(f"[PROCESS] Calling patch_with_greenluma for {game['id']}...")
                success, log_msg = patcher.patch_with_greenluma(game["id"], dlc_ids, get_tools_dir(), stealth_mode=use_stealth)
                print(f"[RESULT] Patch succeeded: {success}")
                # Safer thread communication
                QMetaObject.invokeMethod(self, "on_patch_finished_gl", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, success), Q_ARG(str, log_msg))
                QMetaObject.invokeMethod(self, "refresh_active_applist_label", Qt.ConnectionType.QueuedConnection)
            threading.Thread(target=run, daemon=True).start()
        else:
            print("[DEBUG] GreenLuma config dialog cancelled.")

    @pyqtSlot(bool, str)
    def on_patch_finished_gl(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success:
            QMessageBox.information(self, "List Updated", "GreenLuma AppList has been updated!\n\n" + log_msg)
        else:
            QMessageBox.critical(self, "Error", "Failed to update GreenLuma list:\n\n" + log_msg)

    def trigger_revert_gl(self, game):
        print("[ACTION] User clicked Revert/Clear GreenLuma AppList")
        # GreenLuma "reverting" is basically clearing the AppList
        msg = "GreenLuma works globally via the AppList folder. Do you want to clear your entire GreenLuma AppList?"
        if QMessageBox.question(self, "Clear AppList", msg) == QMessageBox.StandardButton.Yes:
            app_list_dir = get_tools_dir() / "Greenluma" / "NormalMode" / "AppList"
            if app_list_dir.exists():
                for f in app_list_dir.glob("*.txt"):
                    try: f.unlink()
                    except: pass
                QMessageBox.information(self, "Cleared", "GreenLuma AppList has been cleared.")

    def launch_greenluma(self):
        """Execute DLLInjector.exe from Steam root directory."""
        print("[ACTION] User clicked Launch Injector")
        steam_path = greenluma_patcher.get_steam_path()
        if not steam_path:
            QMessageBox.critical(self, "Error", "Could not locate Steam installation folder.")
            return

        exe_path = steam_path / "DLLInjector.exe"
        working_dir = steam_path
        
        if not exe_path.exists():
            QMessageBox.critical(self, "Error", f"GreenLuma is not installed in your Steam folder yet.\n\nPlease 'Patch' a game first to set it up automatically.")
            return
            
        try:
            print(f"[PROCESS] Launching GreenLuma from Steam folder: {exe_path}")
            # Use Popen so the browser doesn't freeze or wait for Steam to close
            subprocess.Popen([str(exe_path)], cwd=str(working_dir), shell=True)
            if self.main_app:
                self.main_app.statusBar().showMessage("GreenLuma Injector launched from Steam folder.", 5000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch injector:\n{e}")

    @pyqtSlot(object)
    def _safe_ui_callback(self, callback):
        """Internal helper to execute callbacks on the GUI thread."""
        if callable(callback):
            callback()

    def perform_global_gl_search(self):
        query = self.gl_global_search_input.text().strip()
        if not query: return
        
        print(f"[ACTION] Global Steam Search for GreenLuma: {query}")
        self.clear_layout(self.gl_search_layout)
        loader = LoadingWidget(f"Searching Steam for '{query}'...")
        self.gl_search_layout.addWidget(loader)
        
        def run():
            try:
                # We use steam_utils to search Steam storefront
                results = steam_utils.search_steam_games(query)
                
                def update():
                    self.clear_layout(self.gl_search_layout)
                    if not results:
                        self.gl_search_layout.addWidget(QLabel("No results found."))
                    else:
                        for game in results:
                            # Use GamePatcherCard but with GreenLuma mode
                            card = GamePatcherCard(game, "GreenLuma", self.trigger_patch_gl, self.trigger_revert_gl)
                            self.gl_search_layout.addWidget(card)
                
                QMetaObject.invokeMethod(self, "_safe_ui_callback", Qt.ConnectionType.QueuedConnection, Q_ARG(object, update))
            except Exception as e:
                print(f"[ERROR] Global Search failed: {e}")
        
        threading.Thread(target=run, daemon=True).start()

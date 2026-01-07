# ui/patcher/greenluma_tab.py
import threading
import os
import subprocess
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from ui.core.styles import COLORS, STYLESHEET
from core import patcher, steam_utils, greenluma_patcher
from core.path_utils import get_tools_dir
from ui.core.components import LoadingWidget, GamePatcherCard

class GreenLumaTab(QWidget):
    patch_finished = pyqtSignal(bool, str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self._shared_steam_games = []
        self._is_scanning = False
        
        self.patch_finished.connect(self.on_patch_finished)
        
        self.initUI()

    def initUI(self):
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
            try:
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
        self.steam_search_input = QLineEdit()
        self.steam_search_input.setPlaceholderText("Filter your installed Steam library...")
        self.steam_search_input.setFixedHeight(45)
        self.steam_search_input.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-radius: 12px; padding: 0 15px;")
        self.steam_search_input.textChanged.connect(self.filter_steam_games)
        gl_installed_layout.addWidget(self.steam_search_input)
        self.steam_scroll = QScrollArea()
        self.steam_scroll.setWidgetResizable(True)
        self.steam_scroll.setStyleSheet("background: transparent; border: none;")
        self.steam_container = QWidget()
        self.steam_container_layout = QVBoxLayout(self.steam_container)
        self.steam_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steam_container_layout.setSpacing(12)
        self.steam_scroll.setWidget(self.steam_container)
        gl_installed_layout.addWidget(self.steam_scroll)

        # TAB 2: Add New Games (Global Search)
        self.gl_search_tab = QWidget()
        gl_search_layout = QVBoxLayout(self.gl_search_tab)
        gl_search_layout.setContentsMargins(0, 15, 0, 0)
        search_header = QLabel("Search Steam for games to add to your AppList.")
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

        # TAB 3: Managed active files
        self.gl_active_tab = QWidget()
        gl_active_layout = QVBoxLayout(self.gl_active_tab)
        gl_active_layout.setContentsMargins(0, 15, 0, 0)
        active_header = QLabel("Manage current AppList IDs in your Steam folder.")
        gl_active_layout.addWidget(active_header)
        self.active_list_scroll = QScrollArea()
        self.active_list_scroll.setWidgetResizable(True)
        self.active_list_scroll.setStyleSheet("background: transparent; border: none;")
        self.active_list_container = QWidget()
        self.active_list_layout = QVBoxLayout(self.active_list_container)
        self.active_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_list_scroll.setWidget(self.active_list_container)
        gl_active_layout.addWidget(self.active_list_scroll)
        
        self.gl_mode_tabs.addTab(self.gl_installed_tab, "📦 DLC Manager (My Games)")
        self.gl_mode_tabs.addTab(self.gl_search_tab, "🚀 Game Manager (Add New)")
        self.gl_mode_tabs.addTab(self.gl_active_tab, "📝 Active AppList")
        
        layout.addWidget(self.gl_mode_tabs)
        self.setLayout(layout)
        QTimer.singleShot(500, self.request_library_scan)
        self.refresh_active_applist_label()

    def manual_folder_patch(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Game Folder (used to get AppID)")
        if not folder: return
        
        # We need an AppID for GreenLuma.
        appid, ok = QInputDialog.getInt(self, "AppID Required", "Enter Steam AppID for this game:", 0, 0, 9999999)
        if not ok: return
        
        game = {
            "name": os.path.basename(folder),
            "id": appid,
            "full_path": folder
        }
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
        if self._is_scanning: return
        self._is_scanning = True
        self.steam_search_input.setText("")
        self.clear_layout(self.steam_container_layout)
        self.loader = LoadingWidget("Scanning Steam Libraries")
        self.steam_container_layout.addWidget(self.loader)

        def scan():
            try:
                games = steam_utils.get_installed_games()
                games.sort(key=lambda x: x["name"])
                QMetaObject.invokeMethod(self, "on_scan_completed", Qt.ConnectionType.QueuedConnection, Q_ARG(list, games))
            except Exception as e:
                print(f"[ERROR] GreenLuma scan failed: {e}")
                QMetaObject.invokeMethod(self, "on_scan_failed", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))
            finally:
                self._is_scanning = False

        threading.Thread(target=scan, daemon=True).start()

    @pyqtSlot(list)
    def on_scan_completed(self, games):
        if hasattr(self, 'loader'): 
            self.loader.stop()
            self.loader.setParent(None)
            # No del self.loader here to be safe and consistent
        self._shared_steam_games = games
        self.display_steam_games()

    @pyqtSlot(str)
    def on_scan_failed(self, error_msg):
        if hasattr(self, 'loader'):
            self.loader.stop()
            self.loader.setParent(None)
        
        self.clear_layout(self.steam_container_layout)
        err_label = QLabel(f"❌ Scan Failed: {error_msg}")
        err_label.setStyleSheet(f"color: {COLORS['accent_red']}; font-weight: bold;")
        err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_container_layout.addWidget(err_label)

    def display_steam_games(self, filtered_list=None):
        self.clear_layout(self.steam_container_layout)
        games = filtered_list if filtered_list is not None else self._shared_steam_games
        if not games:
            empty = QLabel("No games found."); empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steam_container_layout.addWidget(empty)
            return
        for g in games:
            card = GamePatcherCard(g, "GreenLuma", self.trigger_patch, self.trigger_revert)
            self.steam_container_layout.addWidget(card)

    def filter_steam_games(self, text):
        if self._is_scanning: return
        filtered = [g for g in self._shared_steam_games if text.lower() in g["name"].lower()]
        self.display_steam_games(filtered)

    @pyqtSlot()
    def refresh_active_applist_label(self):
        try:
            current_ids = greenluma_patcher.get_current_applist()
            if current_ids:
                count = len(current_ids)
                text = f"🟢 Current Active AppList: {count} IDs ({', '.join(current_ids[:5])}{'...' if count > 5 else ''})"
            else:
                text = "⚪ Current Active AppList: Empty (Patch a game to start)"
            self.active_applist_label.setText(text)
            
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
                    
                    def make_delete(app_id_to_del):
                        def delete_id():
                            steam_path = greenluma_patcher.get_steam_path()
                            if steam_path:
                                app_list_dir = steam_path / "AppList"
                                for f in app_list_dir.glob("*.txt"):
                                    try:
                                        with open(f, "r") as rfile:
                                            if rfile.read().strip() == app_id_to_del:
                                                f.unlink(); break
                                    except: pass
                                self.refresh_active_applist_label()
                        return delete_id

                    del_btn.clicked.connect(make_delete(aid))
                    row_layout.addWidget(del_btn)
                    self.active_list_layout.addWidget(row)
        except Exception as e:
            print(f"[ERROR] Failed to refresh active AppList: {e}")

    def trigger_patch(self, game):
        dialog = QDialog(self); dialog.setWindowTitle(f"GreenLuma Config - {game['name']}"); dialog.setFixedSize(550, 500); dialog.setStyleSheet(STYLESHEET)
        layout = QVBoxLayout(dialog); layout.setContentsMargins(25, 25, 25, 25); layout.setSpacing(15)
        header = QLabel("GreenLuma AppList Manager"); header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(header)
        dlc_group = QGroupBox("Target AppIDs"); dlc_group.setStyleSheet("QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #333; margin-top: 10px; padding: 10px; }")
        dlc_layout = QVBoxLayout(dlc_group)
        dlc_header_layout = QHBoxLayout()
        dlc_label = QLabel("Enter IDs:"); fetch_btn = QPushButton("✨ Fetch IDs From Steam"); fetch_btn.setFixedWidth(160)
        dlc_header_layout.addWidget(dlc_label); dlc_header_layout.addStretch(); dlc_header_layout.addWidget(fetch_btn)
        dlc_layout.addLayout(dlc_header_layout)
        dlc_input = QTextEdit(); dlc_input.setPlainText(str(game['id']))
        dlc_layout.addWidget(dlc_input); layout.addWidget(dlc_group)
        
        def on_fetch():
            fetch_btn.setText("Fetching..."); fetch_btn.setEnabled(False)
            def run():
                try:
                    dlc_list = steam_utils.fetch_dlcs(game['id'])
                    ids_text = [str(game['id'])]
                    for d in dlc_list: ids_text.append(f"{d['id']} = {d['name']}")
                    final_text = "\n".join(ids_text)
                    def update_ui():
                        dlc_input.setPlainText(final_text)
                        fetch_btn.setText("✨ Fetch IDs From Steam"); fetch_btn.setEnabled(True)
                    QMetaObject.invokeMethod(self, "_safe_ui_callback", Qt.ConnectionType.QueuedConnection, Q_ARG(object, update_ui))
                except: fetch_btn.setText("❌ Fetch Failed"); QTimer.singleShot(2000, lambda: fetch_btn.setEnabled(True))
            threading.Thread(target=run, daemon=True).start()
        fetch_btn.clicked.connect(on_fetch)

        stealth_cb = QCheckBox("🛡️  Enable Stealth Mode")
        stealth_cb.setChecked(True); layout.addWidget(stealth_cb)
        btn_layout = QHBoxLayout(); btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(dialog.reject); btn_layout.addWidget(cancel_btn)
        apply_btn = QPushButton("Update AppList"); apply_btn.setStyleSheet(f"background: {COLORS['accent_primary']}; color: white; font-weight: bold;"); apply_btn.clicked.connect(dialog.accept); btn_layout.addWidget(apply_btn); layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dlc_text = dlc_input.toPlainText().strip()
            dlc_ids = [line.strip() for line in dlc_text.split("\n") if line.strip()]
            def run():
                success, log_msg = patcher.patch_with_greenluma(game["id"], dlc_ids, get_tools_dir(), stealth_mode=stealth_cb.isChecked())
                self.patch_finished.emit(success, log_msg)
                QMetaObject.invokeMethod(self, "refresh_active_applist_label", Qt.ConnectionType.QueuedConnection)
            threading.Thread(target=run, daemon=True).start()

    @pyqtSlot(bool, str)
    def on_patch_finished(self, success, log_msg):
        if self.main_app: self.main_app.statusBar().showMessage("Ready", 3000)
        if success: QMessageBox.information(self, "List Updated", "GreenLuma AppList updated!\n\n" + log_msg)
        else: QMessageBox.critical(self, "Error", "Failed: " + log_msg)

    def trigger_revert(self, game):
        msg = "Clear entire GreenLuma AppList?"
        if QMessageBox.question(self, "Clear", msg) == QMessageBox.StandardButton.Yes:
            app_list_dir = get_tools_dir() / "Greenluma" / "NormalMode" / "AppList"
            if app_list_dir.exists():
                for f in app_list_dir.glob("*.txt"):
                    try: f.unlink()
                    except: pass
                QMessageBox.information(self, "Cleared", "Cleared.")
                self.refresh_active_applist_label()

    def launch_greenluma(self):
        steam_path = greenluma_patcher.get_steam_path()
        if not steam_path: QMessageBox.critical(self, "Error", "No Steam path."); return
        exe_path = steam_path / "DLLInjector.exe"
        if not exe_path.exists(): QMessageBox.critical(self, "Error", "GreenLuma not installed."); return
        try:
            subprocess.Popen([str(exe_path)], cwd=str(steam_path), shell=True)
            if self.main_app: self.main_app.statusBar().showMessage("Launched.", 5000)
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed: {e}")

    @pyqtSlot(object)
    def _safe_ui_callback(self, callback):
        if callable(callback): callback()

    def perform_global_gl_search(self):
        query = self.gl_global_search_input.text().strip()
        if not query: return
        self.clear_layout(self.gl_search_layout)
        loader = LoadingWidget(f"Searching Steam for '{query}'...")
        self.gl_search_layout.addWidget(loader)
        def run():
            try:
                results = steam_utils.search_steam_games(query)
                def update():
                    self.clear_layout(self.gl_search_layout)
                    if not results: self.gl_search_layout.addWidget(QLabel("No results found."))
                    else:
                        for game in results: self.gl_search_layout.addWidget(GamePatcherCard(game, "GreenLuma", self.trigger_patch, self.trigger_revert))
                QMetaObject.invokeMethod(self, "_safe_ui_callback", Qt.ConnectionType.QueuedConnection, Q_ARG(object, update))
            except Exception as e: print(e)
        threading.Thread(target=run, daemon=True).start()

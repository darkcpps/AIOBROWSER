# Tidal tab removed — use Monochrome tab instead.
from PyQt6.QtWidgets import QWidget

# File intentionally removed. Tidal support has been removed and replaced by Monochrome downloader.
# Keeping a minimal module avoids import errors in environments that expect this module to exist.

class TidalTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Intentionally empty - functionality removed.
        pass


    def create_track_list(self) -> QGroupBox:
        """Create track list display"""
        group = QGroupBox("Tracks")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        # Select buttons
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        self.select_all_btn.clicked.connect(self.select_all_tracks)
        select_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setStyleSheet(self.select_all_btn.styleSheet())
        self.deselect_all_btn.clicked.connect(self.deselect_all_tracks)
        select_layout.addWidget(self.deselect_all_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Track list
        self.track_list = QListWidget()
        self.track_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 5px;
                color: {COLORS['text_primary']};
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_primary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        self.track_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.track_list)

        group.setLayout(layout)
        return group

    def create_search_results(self) -> QGroupBox:
        """Create search results display"""
        group = QGroupBox("Search Results")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        # Results list
        self.search_results_list = QListWidget()
        self.search_results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 5px;
                color: {COLORS['text_primary']};
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['accent_primary']};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        self.search_results_list.itemDoubleClicked.connect(self.on_search_result_selected)
        layout.addWidget(self.search_results_list)

        # Select button
        select_result_btn = QPushButton("Select Result")
        select_result_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
        """)
        select_result_btn.clicked.connect(self.select_search_result)
        layout.addWidget(select_result_btn)

        group.setLayout(layout)
        return group

    def set_quality(self, quality: AudioQuality):
        """Set download quality"""
        self.download_quality = quality

        # Update info label
        info_texts = {
            "LOW": "💡 Small file size, good for mobile devices",
            "HIGH": "💡 High quality AAC, good balance of size and quality",
            "LOSSLESS": "💡 CD quality FLAC, recommended for most users",
            "HI_RES": "💡 Studio quality FLAC, largest file size"
        }
        self.quality_info_label.setText(info_texts.get(quality, ""))

    def search_or_fetch(self):
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def search_tidal(self, query: str):
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def _search_thread(self, query: str, search_type: str):
        # Removed - functionality no longer available
        return
            import traceback
            traceback.print_exc()
            self.download_error.emit("", f"Search error: {str(e)}")

    def on_search_results_loaded(self, data: Dict):
        # Removed: Tidal search results are no longer supported
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")


    def select_search_result(self):
        """Select a search result and fetch its tracks"""
        selected_items = self.search_results_list.selectedItems()
        if not selected_items:
            self.status_label.setText("❌ Please select a result")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        self.on_search_result_selected(selected_items[0])

    def on_search_result_selected(self, item: QListWidgetItem):
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def fetch_metadata(self, url: str):
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def _fetch_metadata_thread(self, url: str):
        # Removed - functionality no longer available
        return

    def on_metadata_loaded(self, data: Dict):
        # Removed - functionality no longer available
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def _fetch_metadata_thread(self, url: str):
        # Removed - functionality no longer available
        self.download_error.emit("", "Tidal support removed. Use Monochrome tab.")

    def on_metadata_loaded(self, data: Dict):
        """Handle loaded metadata"""
        tracks = data["tracks"]
        self.current_tracks = tracks

        # Hide search results, show track list
        self.search_results_widget.setVisible(False)
        self.track_list_widget.setVisible(True)
        self.download_btn.setVisible(True)

        # Clear and populate track list
        self.track_list.clear()
        for track in tracks:
            artists = ", ".join([a["name"] for a in track.get("artists", [])])
            track_name = track.get("title", "Unknown")
            duration = MetadataHelper.format_duration(track.get("duration", 0))
            item_text = f"{track_name} - {artists} [{duration}]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, track["id"])
            self.track_list.addItem(item)

        self.status_label.setText(f"✅ Loaded {len(tracks)} track(s)")
        self.status_label.setStyleSheet(f"color: {COLORS.get('accent_green', '#00ff00')}; font-size: 12px;")
        self.download_btn.setEnabled(True)

    def select_all_tracks(self):
        """Select all tracks in list"""
        for i in range(self.track_list.count()):
            self.track_list.item(i).setSelected(True)

    def deselect_all_tracks(self):
        """Deselect all tracks"""
        self.track_list.clearSelection()

    def start_downloads(self):
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")

    def _download_track_thread(self, track_data: Dict, output_dir: Path):
        # Removed - functionality no longer available
        return

    def on_download_progress(self, track_id: str, progress: float):
        # Removed - functionality no longer available
        pass

    def on_download_complete(self, track_id: str, filepath: str):
        # Removed - functionality no longer available
        pass

    def on_download_error(self, track_id: str, error_msg: str):
        # Removed - functionality no longer available
        self.status_label.setText("Tidal support removed. Use Monochrome tab.")


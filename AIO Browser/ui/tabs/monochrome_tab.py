"""
Monochrome Downloader Tab
UI for downloading high-quality music from Monochrome (FLAC up to 24-bit/192kHz)
Powered by Monochrome API - monochrome-api.samidy.com
"""
import threading
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from core.monochrome_downloader import MonochromeAPI, MonochromeDownloader, MetadataHelper, AudioQuality
from ui.core.styles import COLORS


class MonochromeTab(QWidget):
    # Signals
    metadata_loaded = pyqtSignal(dict)
    search_results_loaded = pyqtSignal(dict)
    download_progress = pyqtSignal(str, float)
    download_complete = pyqtSignal(str, str)
    download_error = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.monochrome_api = MonochromeAPI()
        self.downloader: Optional[MonochromeDownloader] = None
        self.current_tracks: List[Dict] = []
        self.search_results: List[Dict] = []
        self.download_quality: AudioQuality = "LOSSLESS"

        # Connect signals
        self.metadata_loaded.connect(self.on_metadata_loaded)
        self.search_results_loaded.connect(self.on_search_results_loaded)
        self.download_progress.connect(self.on_download_progress)
        self.download_complete.connect(self.on_download_complete)
        self.download_error.connect(self.on_download_error)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("🎧 Monochrome Downloader")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Info banner
        info_banner = QLabel("✨ Download lossless music via Monochrome • FLAC up to 24-bit/192kHz • No account required\n💡 Powered by monochrome-api.samidy.com - A privacy-focused music streaming API")
        info_banner.setStyleSheet(f"""
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid {COLORS['accent_primary']};
            font-size: 11px;
        """)
        info_banner.setWordWrap(True)
        layout.addWidget(info_banner)

        # Search Section
        search_group = self.create_search_section()
        layout.addWidget(search_group)

        # Quality Selection
        quality_group = self.create_quality_section()
        layout.addWidget(quality_group)

        # Search Results List
        self.search_results_widget = self.create_search_results()
        layout.addWidget(self.search_results_widget)
        self.search_results_widget.setVisible(False)

        # Track List
        self.track_list_widget = self.create_track_list()
        layout.addWidget(self.track_list_widget)

        # Download Button
        self.download_btn = QPushButton("Download Selected Tracks")
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['border']};
                color: {COLORS['text_secondary']};
            }}
        """)
        self.download_btn.clicked.connect(self.start_downloads)
        layout.addWidget(self.download_btn)

        # Status Label
        self.status_label = QLabel("Search for music to begin")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

    def create_search_section(self) -> QGroupBox:
        """Create search input section"""
        group = QGroupBox("Search Music")
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

        # Search type selection
        search_type_layout = QHBoxLayout()
        search_type_label = QLabel("Search for:")
        search_type_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
        search_type_layout.addWidget(search_type_label)

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["Tracks", "Albums", "Playlists", "Artists"])
        self.search_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                color: {COLORS['text_primary']};
                font-size: 12px;
            }}
            QComboBox:hover {{
                border: 1px solid {COLORS['accent_primary']};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        search_type_layout.addWidget(self.search_type_combo)
        search_type_layout.addStretch()
        layout.addLayout(search_type_layout)

        # Input and button
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by artist, album, or track name...")
        self.search_input.returnPressed.connect(self.search_monochrome)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['accent_primary']};
            }}
        """)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
        """)
        search_btn.clicked.connect(self.search_monochrome)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)
        group.setLayout(layout)

        return group

    def create_quality_section(self) -> QGroupBox:
        """Create quality selection section"""
        group = QGroupBox("Download Quality")
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

        # Quality radio buttons
        quality_layout = QHBoxLayout()

        self.low_radio = QRadioButton("AAC 96kbps (LOW)")
        self.low_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.low_radio.toggled.connect(lambda: self.set_quality("LOW"))
        quality_layout.addWidget(self.low_radio)

        self.high_radio = QRadioButton("AAC 320kbps (HIGH)")
        self.high_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.high_radio.toggled.connect(lambda: self.set_quality("HIGH"))
        quality_layout.addWidget(self.high_radio)

        self.lossless_radio = QRadioButton("FLAC 16-bit/44.1kHz (LOSSLESS)")
        self.lossless_radio.setChecked(True)
        self.lossless_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.lossless_radio.toggled.connect(lambda: self.set_quality("LOSSLESS"))
        quality_layout.addWidget(self.lossless_radio)

        self.hires_radio = QRadioButton("FLAC 24-bit/96kHz+ (HI_RES)")
        self.hires_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.hires_radio.toggled.connect(lambda: self.set_quality("HI_RES"))
        quality_layout.addWidget(self.hires_radio)

        quality_layout.addStretch()
        layout.addLayout(quality_layout)

        # Quality info label
        self.quality_info_label = QLabel("💡 LOSSLESS quality recommended for best audio quality")
        self.quality_info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.quality_info_label)

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

    def search_monochrome(self):
        """Search Monochrome catalog"""
        query = self.search_input.text().strip()
        if not query:
            self.status_label.setText("❌ Please enter a search term")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        self.status_label.setText("🔍 Searching Monochrome...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        # Get search type
        search_type_map = {
            "Tracks": "s",
            "Albums": "al",
            "Playlists": "p",
            "Artists": "a"
        }
        search_type = search_type_map.get(self.search_type_combo.currentText(), "al")

        # Run in background thread
        thread = threading.Thread(target=self._search_thread, args=(query, search_type))
        thread.daemon = True
        thread.start()

    def _search_thread(self, query: str, search_type: str):
        """Background thread for searching"""
        try:
            print(f"[MONOCHROME UI] Searching for '{query}' (type: {search_type})")
            results = self.monochrome_api.search(query, search_type)
            print(f"[MONOCHROME UI] Search complete")

            self.search_results_loaded.emit({"query": query, "type": search_type, "results": results})

        except Exception as e:
            print(f"[MONOCHROME UI] Search ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.download_error.emit("", f"Search error: {str(e)}")

    def on_search_results_loaded(self, data: Dict):
        """Handle loaded search results"""
        results = data["results"]
        search_type = data["type"]

        # Clear and populate search results list
        self.search_results_list.clear()
        self.search_results = []

        # Parse results based on type
        if search_type == "s":  # Tracks
            if "items" in results:
                items = results.get("items", [])
            else:
                items = results.get("tracks", {}).get("items", [])

            for item in items:
                artists = ", ".join([a["name"] for a in item.get("artists", [])])
                album = item.get("album", {}).get("title", "Unknown Album")
                text = f"🎵 {item.get('title', 'Unknown')} - {artists} (from: {album})"
                list_item = QListWidgetItem(text)
                list_item.setData(Qt.ItemDataRole.UserRole, {"type": "track", "id": item["id"], "data": item})
                self.search_results_list.addItem(list_item)
                self.search_results.append(item)

        elif search_type == "al":  # Albums
            items = results.get("albums", {}).get("items", [])
            for item in items:
                artists = ", ".join([a["name"] for a in item.get("artists", [])])
                year = item.get("releaseDate", "")[:4] if item.get("releaseDate") else ""
                num_tracks = item.get("numberOfTracks", "?")
                text = f"💿 {item.get('title', 'Unknown')} - {artists} ({year}) • {num_tracks} tracks"
                list_item = QListWidgetItem(text)
                list_item.setData(Qt.ItemDataRole.UserRole, {"type": "album", "id": item["id"], "data": item})
                self.search_results_list.addItem(list_item)
                self.search_results.append(item)

        elif search_type == "p":  # Playlists
            items = results.get("playlists", {}).get("items", [])
            for item in items:
                creator = item.get("creator", {}).get("name", "Unknown")
                num_tracks = item.get("numberOfTracks", 0)
                text = f"📝 {item.get('title', 'Unknown')} by {creator} ({num_tracks} tracks)"
                list_item = QListWidgetItem(text)
                list_item.setData(Qt.ItemDataRole.UserRole, {"type": "playlist", "id": item.get("uuid", item.get("id")), "data": item})
                self.search_results_list.addItem(list_item)
                self.search_results.append(item)

        elif search_type == "a":  # Artists
            items = results.get("artists", {}).get("items", [])
            for item in items:
                text = f"👤 {item.get('name', 'Unknown')}"
                list_item = QListWidgetItem(text)
                list_item.setData(Qt.ItemDataRole.UserRole, {"type": "artist", "id": item["id"], "data": item})
                self.search_results_list.addItem(list_item)
                self.search_results.append(item)

        # Show search results, hide track list
        self.search_results_widget.setVisible(True)
        self.track_list_widget.setVisible(False)
        self.download_btn.setVisible(False)

        self.status_label.setText(f"✅ Found {len(items)} result(s)")
        self.status_label.setStyleSheet(f"color: {COLORS.get('accent_green', '#00ff00')}; font-size: 12px;")

    def select_search_result(self):
        """Select a search result and fetch its tracks"""
        selected_items = self.search_results_list.selectedItems()
        if not selected_items:
            self.status_label.setText("❌ Please select a result")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        self.on_search_result_selected(selected_items[0])

    def on_search_result_selected(self, item: QListWidgetItem):
        """Handle selection of a search result"""
        item_data = item.data(Qt.ItemDataRole.UserRole)
        result_type = item_data["type"]
        result_id = item_data["id"]

        print(f"[MONOCHROME UI] Selected {result_type}: {result_id}")

        self.status_label.setText("🔄 Fetching tracks...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        # Run in background thread
        thread = threading.Thread(target=self._fetch_metadata_thread, args=(result_type, result_id))
        thread.daemon = True
        thread.start()

    def _fetch_metadata_thread(self, content_type: str, content_id: str):
        """Background thread for fetching metadata"""
        try:
            print(f"[MONOCHROME UI] Fetching {content_type} {content_id}")

            if content_type == "track":
                track = self.monochrome_api.get_track(content_id)
                tracks = [track]
            elif content_type == "album":
                album = self.monochrome_api.get_album(content_id)
                tracks = album.get("tracks", [])
                # Add album info to each track
                for track in tracks:
                    if "album" not in track or not track["album"]:
                        track["album"] = {
                            "id": album["id"],
                            "title": album["title"],
                            "cover": album.get("cover"),
                            "artists": album.get("artists", []),
                            "releaseDate": album.get("releaseDate"),
                            "numberOfTracks": album.get("numberOfTracks")
                        }
            elif content_type == "playlist":
                playlist = self.monochrome_api.get_playlist(content_id)
                tracks = playlist.get("tracks", [])
            elif content_type == "artist":
                # For artists, we could get top tracks or albums
                # For now, let's get artist info and show a message
                artist = self.monochrome_api.get_artist(content_id)
                self.download_error.emit("", f"Artist selected: {artist.get('name', 'Unknown')}. Please select an album or track to download.")
                return
            else:
                raise ValueError(f"Unsupported content type: {content_type}")

            print(f"[MONOCHROME UI] Emitting metadata for {len(tracks)} tracks")
            self.metadata_loaded.emit({"type": content_type, "tracks": tracks})

        except Exception as e:
            print(f"[MONOCHROME UI] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.download_error.emit("", f"Error fetching metadata: {str(e)}")

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
        """Start downloading selected tracks"""
        selected_items = self.track_list.selectedItems()
        if not selected_items:
            self.status_label.setText("❌ Please select at least one track")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        # Initialize downloader if not already
        if not self.downloader:
            self.downloader = MonochromeDownloader(self.monochrome_api)

        # Get download path from settings
        download_path = self.parent.settings_manager.get("download_path", str(Path.home() / "Downloads"))
        monochrome_path = Path(download_path) / "Monochrome"
        monochrome_path.mkdir(parents=True, exist_ok=True)

        # Get selected track IDs
        selected_track_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        self.status_label.setText(f"⬇️ Downloading {len(selected_track_ids)} track(s)...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.download_btn.setEnabled(False)

        # Start download threads
        for track_id in selected_track_ids:
            track_data = next((t for t in self.current_tracks if t["id"] == track_id), None)
            if track_data:
                thread = threading.Thread(
                    target=self._download_track_thread,
                    args=(track_data, monochrome_path)
                )
                thread.daemon = True
                thread.start()

    def _download_track_thread(self, track_data: Dict, output_dir: Path):
        """Background thread for downloading a track"""
        try:
            track_id = str(track_data["id"])
            track_title = track_data.get("title", "Unknown")
            print(f"[MONOCHROME UI] Download thread started for: {track_title} (ID: {track_id})")

            def progress_callback(progress, downloaded, total):
                self.download_progress.emit(track_id, progress)

            result = self.downloader.download_track(
                track_data,
                output_dir,
                self.download_quality,
                progress_callback
            )

            print(f"[MONOCHROME UI] Download complete, result: {result}")
            self.download_complete.emit(track_id, result)

        except Exception as e:
            print(f"[MONOCHROME UI] Download error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.download_error.emit(track_id, str(e))

    def on_download_progress(self, track_id: str, progress: float):
        """Handle download progress update"""
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if str(item.data(Qt.ItemDataRole.UserRole)) == track_id:
                original_text = item.text().split(" [")[0]
                duration = item.text().split("[")[-1].split("]")[0]
                item.setText(f"{original_text} [{duration}] - {progress:.1f}%")
                break

    def on_download_complete(self, track_id: str, filepath: str):
        """Handle download completion"""
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if str(item.data(Qt.ItemDataRole.UserRole)) == track_id:
                original_text = item.text().split(" [")[0]
                if filepath.startswith("EXISTS:"):
                    item.setText(f"{original_text} [Already exists]")
                    item.setBackground(QColor("#ffaa00").lighter(160))
                else:
                    item.setText(f"{original_text} [✅ Complete]")
                    item.setBackground(QColor("#00ff00").lighter(160))
                break

        # Check if all downloads are complete
        completed = sum(1 for i in range(self.track_list.count())
                       if "[✅ Complete]" in self.track_list.item(i).text() or
                          "[Already exists]" in self.track_list.item(i).text())
        selected = len(self.track_list.selectedItems())

        if completed >= selected:
            self.status_label.setText("✅ All downloads complete!")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_green', '#00ff00')}; font-size: 12px;")
            self.download_btn.setEnabled(True)

    def on_download_error(self, track_id: str, error_msg: str):
        """Handle download error"""
        if track_id:
            for i in range(self.track_list.count()):
                item = self.track_list.item(i)
                if str(item.data(Qt.ItemDataRole.UserRole)) == track_id:
                    original_text = item.text().split(" [")[0]
                    item.setText(f"{original_text} [❌ Error]")
                    item.setBackground(QColor(COLORS.get('accent_red', '#ff0000')).lighter(160))
                    break

        self.status_label.setText(f"❌ Error: {error_msg}")
        self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
        self.download_btn.setEnabled(True)

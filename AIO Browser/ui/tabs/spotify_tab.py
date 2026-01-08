# Spotify tab removed — use Monochrome tab instead.
from PyQt6.QtWidgets import QWidget

# File intentionally removed. Spotify support has been removed and replaced by Monochrome downloader.
# Keeping a minimal module avoids import errors in environments that expect this module to exist.

class SpotifyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Intentionally empty - functionality removed.
        pass

    def create_token_section(self) -> QGroupBox:
        """Create session token input section"""
        group = QGroupBox("Session Token")
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

        # Info with help button
        info_layout = QHBoxLayout()
        info_label = QLabel("⚠️ Required: Get your session token from spotidownloader.com (requires Chrome)")
        info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)

        help_btn = QPushButton("❓ How to get token")
        help_btn.setFixedWidth(140)
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        help_btn.clicked.connect(self.show_token_help)
        info_layout.addWidget(help_btn)
        info_layout.addStretch()

        layout.addLayout(info_layout)

        token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Paste your session token here...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px;
                color: {COLORS['text_primary']};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['accent_primary']};
            }}
        """)
        token_layout.addWidget(self.token_input)

        show_token_btn = QPushButton("👁")
        show_token_btn.setFixedWidth(40)
        show_token_btn.setCheckable(True)
        show_token_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent_primary']};
            }}
        """)
        show_token_btn.toggled.connect(
            lambda checked: self.token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        token_layout.addWidget(show_token_btn)

        save_token_btn = QPushButton("Save Token")
        save_token_btn.setStyleSheet(f"""
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
        save_token_btn.clicked.connect(self.save_token)
        token_layout.addWidget(save_token_btn)

        layout.addLayout(token_layout)
        group.setLayout(layout)

        return group

    def create_url_section(self) -> QGroupBox:
        """Create Spotify URL input section"""
        group = QGroupBox("Spotify URL")
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

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Spotify track/album/playlist/artist URL...")
        self.url_input.setStyleSheet(f"""
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
        url_layout.addWidget(self.url_input)

        fetch_btn = QPushButton("Fetch Metadata")
        fetch_btn.setStyleSheet(f"""
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
        fetch_btn.clicked.connect(self.fetch_metadata)
        url_layout.addWidget(fetch_btn)

        layout.addLayout(url_layout)
        group.setLayout(layout)

        return group

    def create_format_section(self) -> QGroupBox:
        """Create format selection section"""
        group = QGroupBox("Download Format")
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

        layout = QHBoxLayout()

        self.mp3_radio = QRadioButton("MP3 (320kbps)")
        self.mp3_radio.setChecked(True)
        self.mp3_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.mp3_radio.toggled.connect(lambda: self.set_format("mp3"))
        layout.addWidget(self.mp3_radio)

        self.flac_radio = QRadioButton("FLAC (Lossless)")
        self.flac_radio.setStyleSheet(f"color: {COLORS['text_primary']};")
        self.flac_radio.toggled.connect(lambda: self.set_format("flac"))
        layout.addWidget(self.flac_radio)

        layout.addStretch()
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

        # Select All button
        select_all_layout = QHBoxLayout()
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
        select_all_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setStyleSheet(self.select_all_btn.styleSheet())
        self.deselect_all_btn.clicked.connect(self.deselect_all_tracks)
        select_all_layout.addWidget(self.deselect_all_btn)

        select_all_layout.addStretch()
        layout.addLayout(select_all_layout)

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

    def save_token(self):
        """Save and validate session token"""
        token = self.token_input.text().strip()
        if not token:
            self.status_label.setText("❌ Please enter a session token")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        self.session_token = token
        self.downloader_api = SpotiDownloaderAPI(token)
        self.status_label.setText("✅ Session token saved! You can now fetch tracks")
        self.status_label.setStyleSheet(f"color: {COLORS.get('accent_green', '#00ff00')}; font-size: 12px;")

    def set_format(self, format_type: str):
        """Set download format"""
        self.download_format = format_type

    def fetch_metadata(self):
        """Fetch metadata from Spotify URL"""
        if not self.session_token:
            self.status_label.setText("❌ Please enter and save a session token first")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("❌ Please enter a Spotify URL")
            self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
            return

        self.status_label.setText("🔄 Fetching metadata...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")

        # Run in background thread
        thread = threading.Thread(target=self._fetch_metadata_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def _fetch_metadata_thread(self, url: str):
        """Background thread for fetching metadata"""
        try:
            spotify_type, spotify_id = self.spotify_api.parse_spotify_url(url)

            if spotify_type == "track":
                track = self.spotify_api.get_track(spotify_id)
                tracks = [track]
            elif spotify_type == "album":
                album = self.spotify_api.get_album(spotify_id)
                tracks = [item for item in album["tracks"]["items"]]
                # Add album info to each track
                for track in tracks:
                    track["album"] = {
                        "name": album["name"],
                        "artists": album["artists"],
                        "release_date": album.get("release_date", ""),
                        "total_tracks": album["total_tracks"],
                        "images": album.get("images", [])
                    }
            elif spotify_type == "playlist":
                playlist = self.spotify_api.get_playlist(spotify_id)
                tracks = [item["track"] for item in playlist["tracks"]["items"] if item["track"]]
            elif spotify_type == "artist":
                artist = self.spotify_api.get_artist(spotify_id)
                albums = self.spotify_api.get_artist_albums(spotify_id)
                # Get all tracks from all albums
                tracks = []
                for album_item in albums[:10]:  # Limit to first 10 albums
                    album = self.spotify_api.get_album(album_item["id"])
                    for track in album["tracks"]["items"]:
                        track["album"] = {
                            "name": album["name"],
                            "artists": album["artists"],
                            "release_date": album.get("release_date", ""),
                            "total_tracks": album["total_tracks"],
                            "images": album.get("images", [])
                        }
                        tracks.append(track)
            else:
                raise ValueError(f"Unsupported Spotify type: {spotify_type}")

            self.metadata_loaded.emit({"type": spotify_type, "tracks": tracks})

        except Exception as e:
            self.download_error.emit("", f"Error fetching metadata: {str(e)}")

    def on_metadata_loaded(self, data: Dict):
        """Handle loaded metadata"""
        tracks = data["tracks"]
        self.current_tracks = tracks

        # Clear and populate track list
        self.track_list.clear()
        for track in tracks:
            artists = ", ".join([a["name"] for a in track.get("artists", [])])
            track_name = track.get("name", "Unknown")
            item_text = f"{track_name} - {artists}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, track["id"])
            self.track_list.addItem(item)

        self.status_label.setText(f"✅ Loaded {len(tracks)} track(s)")
        self.status_label.setStyleSheet(f"color: #00ff00; font-size: 12px;")
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

        # Get download path from settings
        download_path = self.parent.settings_manager.get("download_path", str(Path.home() / "Downloads"))
        spotify_path = Path(download_path) / "Spotify"
        spotify_path.mkdir(parents=True, exist_ok=True)

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
                    args=(track_data, spotify_path)
                )
                thread.daemon = True
                thread.start()

    def _download_track_thread(self, track_data: Dict, output_dir: Path):
        """Background thread for downloading a track"""
        try:
            track_id = track_data["id"]

            # Get download links
            links = self.downloader_api.get_download_link(track_id)

            # Select appropriate link based on format
            if self.download_format == "flac" and links.get("linkFlac"):
                download_url = links["linkFlac"]
                file_ext = ".flac"
            else:
                download_url = links["link"]
                file_ext = ".mp3"

            if not download_url:
                self.download_error.emit(track_id, "No download link available")
                return

            # Build filename
            filename = MetadataEmbedder.build_filename(
                track_data,
                "{track}. {title} - {artist}",
                include_track_number=True
            )
            output_path = output_dir / f"{filename}{file_ext}"

            # Download file
            def progress_callback(progress, downloaded, total):
                self.download_progress.emit(track_id, progress)

            self.downloader_api.download_file(download_url, output_path, progress_callback)

            # Download cover art
            cover_data = None
            album = track_data.get("album", {})
            if album and album.get("images"):
                cover_url = album["images"][0]["url"]  # Highest quality
                try:
                    import requests
                    response = requests.get(cover_url)
                    response.raise_for_status()
                    cover_data = response.content
                except:
                    pass

            # Embed metadata
            if file_ext == ".mp3":
                MetadataEmbedder.embed_metadata_mp3(output_path, track_data, cover_data)
            else:
                MetadataEmbedder.embed_metadata_flac(output_path, track_data, cover_data)

            self.download_complete.emit(track_id, str(output_path))

        except Exception as e:
            self.download_error.emit(track_id, str(e))

    def on_download_progress(self, track_id: str, progress: float):
        """Handle download progress update"""
        # Find track in list and update
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == track_id:
                original_text = item.text().split(" [")[0]
                item.setText(f"{original_text} [{progress:.1f}%]")
                break

    def on_download_complete(self, track_id: str, filepath: str):
        """Handle download completion"""
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == track_id:
                original_text = item.text().split(" [")[0]
                item.setText(f"{original_text} [✅ Complete]")
                item.setBackground(QColor("#00ff00").lighter(160))
                break

        # Check if all downloads are complete
        if all("[✅ Complete]" in self.track_list.item(i).text()
               for i in range(self.track_list.count())
               if self.track_list.item(i).isSelected()):
            self.status_label.setText("✅ All downloads complete!")
            self.status_label.setStyleSheet(f"color: #00ff00; font-size: 12px;")
            self.download_btn.setEnabled(True)

    def on_download_error(self, track_id: str, error_msg: str):
        """Handle download error"""
        if track_id:
            for i in range(self.track_list.count()):
                item = self.track_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == track_id:
                    original_text = item.text().split(" [")[0]
                    item.setText(f"{original_text} [❌ Error]")
                    item.setBackground(QColor(COLORS.get('error', '#ff0000')).lighter(160))
                    break

        self.status_label.setText(f"❌ Error: {error_msg}")
        self.status_label.setStyleSheet(f"color: {COLORS.get('accent_red', '#ff0000')}; font-size: 12px;")
        self.download_btn.setEnabled(True)

    def show_token_help(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Spotify support removed")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Spotify support has been removed. Please use the Monochrome tab for music downloads.")
        msg.exec()

import sys
import re
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QTextEdit, 
                             QCheckBox, QComboBox, QListWidget, QListWidgetItem)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QPixmap, QImage

# Check for search library
try:
    from ddgs import DDGS
    HAS_SEARCH = True
except ImportError:
    HAS_SEARCH = False

class VidFastPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamerV6 - Smart Search")
        self.resize(1100, 850)
        self.episode_data = {} 
        self.thumb_cache = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setStyleSheet(
            "QWidget { background: #0f1217; color: #e6e9ef; }"
            "QLineEdit { background: #151a21; border: 1px solid #273042; padding: 8px; border-radius: 8px; }"
            "QPushButton { background: #1f2937; border: 1px solid #2f3b52; padding: 8px 14px; border-radius: 8px; }"
            "QPushButton:hover { background: #263246; }"
            "QComboBox { background: #151a21; border: 1px solid #273042; padding: 6px; border-radius: 8px; }"
            "QCheckBox { padding: 4px 6px; }"
            "QListWidget { background: #12171f; border: 1px solid #243047; border-radius: 10px; }"
            "QListWidget::item { padding: 6px; }"
        )

        title = QLabel("StreamerV6")
        title.setStyleSheet("font-size: 20px; font-weight: bold; letter-spacing: 1px;")
        subtitle = QLabel("Smart search and instant playback")
        subtitle.setStyleSheet("color: #9aa4b2;")
        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)
        
        # --- 1. SEARCH BAR ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Movie/Show Name (e.g. Breaking Bad)...")
        self.search_input.returnPressed.connect(self.search_media)
        
        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.search_media)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        main_layout.addLayout(search_layout)

        # --- 2. RESULTS LIST (NEW) ---
        self.results_list = QListWidget()
        self.results_list.setFixedHeight(200)
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.hide() # Hide until we have results
        main_layout.addWidget(self.results_list)

        # --- 3. CONTROLS BAR ---
        controls_layout = QHBoxLayout()
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("tt1234567")
        self.id_input.setFixedWidth(120)
        
        self.is_tv_checkbox = QCheckBox("TV Show?")
        self.is_tv_checkbox.setChecked(True)
        self.is_tv_checkbox.toggled.connect(self.toggle_tv_controls)
        
        self.combo_season = QComboBox()
        self.combo_season.setPlaceholderText("Season")
        self.combo_season.setFixedWidth(120)
        self.combo_season.currentIndexChanged.connect(self.update_episodes_list)
        
        self.combo_episode = QComboBox()
        self.combo_episode.setPlaceholderText("Episode")
        self.combo_episode.setFixedWidth(250)
        
        self.btn_play = QPushButton("WATCH NOW")
        self.btn_play.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_play.clicked.connect(self.load_video)

        controls_layout.addWidget(QLabel("ID:"))
        controls_layout.addWidget(self.id_input)
        controls_layout.addWidget(self.is_tv_checkbox)
        controls_layout.addWidget(self.combo_season)
        controls_layout.addWidget(self.combo_episode)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)

        # --- 4. WEB VIEW ---
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.web_view)
        
        # --- 5. DEBUG LOG ---
        self.debug_box = QTextEdit()
        self.debug_box.setFixedHeight(60)
        self.debug_box.setReadOnly(True)
        self.debug_box.setStyleSheet("background-color: #222; color: #0f0;")
        main_layout.addWidget(self.debug_box)
        
        self.setLayout(main_layout)
        self.toggle_tv_controls(True)

    def log(self, msg):
        print(msg)
        self.debug_box.append(msg)

    def toggle_tv_controls(self, is_tv):
        self.combo_season.setVisible(is_tv)
        self.combo_episode.setVisible(is_tv)

    def search_media(self):
        """Searches for multiple results and shows the list"""
        if not HAS_SEARCH:
            self.log("Error: 'ddgs' library missing.")
            return

        query = self.search_input.text().strip()
        if not query: return
        
        self.btn_search.setText("Searching...")
        self.results_list.clear()
        self.thumb_cache = {}
        self.results_list.hide()
        QApplication.processEvents()
        
        try:
            # Search for top 5 results on IMDb
            results = DDGS().text(f"{query} site:imdb.com/title/", max_results=5)
            
            if results:
                self.results_list.show()
                for r in results:
                    title = r['title'].replace(" - IMDb", "")
                    url = r['href']
                    
                    # Extract ID
                    match = re.search(r'(tt\d+)', url)
                    if match:
                        imdb_id = match.group(1)
                        thumb_url = self.fetch_thumbnail_url(imdb_id)
                        item = QListWidgetItem()
                        item.setData(Qt.ItemDataRole.UserRole, imdb_id)
                        item.setData(Qt.ItemDataRole.UserRole + 1, thumb_url)
                        widget = self.build_result_widget(title, imdb_id, thumb_url)
                        item.setSizeHint(widget.sizeHint())
                        self.results_list.addItem(item)
                        self.results_list.setItemWidget(item, widget)

                self.log(f"Found {self.results_list.count()} results.")
            else:
                self.log("No results found.")
        except Exception as e:
            self.log(f"Error: {e}")
            
        self.btn_search.setText("Search")

    def on_result_clicked(self, item):
        """Handles clicking a search result"""
        imdb_id = item.data(Qt.ItemDataRole.UserRole)
        self.id_input.setText(imdb_id)
        self.log(f"Selected: {imdb_id}")
        
        if self.is_tv_checkbox.isChecked():
            self.fetch_tv_metadata(imdb_id)

    def build_result_widget(self, title, imdb_id, thumb_url):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        thumb = QLabel()
        thumb.setFixedSize(60, 90)
        thumb.setStyleSheet("background: #1b2331; border: 1px solid #2a364f; border-radius: 6px;")
        if thumb_url:
            pixmap = self.fetch_pixmap(thumb_url)
            if pixmap:
                thumb.setPixmap(pixmap.scaled(60, 90, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(thumb)

        text = QLabel(f"{title}\n{imdb_id}")
        text.setStyleSheet("font-size: 13px; color: #e6e9ef;")
        layout.addWidget(text)
        layout.addStretch()

        return container

    def fetch_thumbnail_url(self, imdb_id):
        try:
            resp = requests.get(f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}", timeout=5)
            if resp.status_code != 200:
                return None
            data = resp.json()
            image = data.get("image") or {}
            return image.get("medium") or image.get("original")
        except Exception:
            return None

    def fetch_pixmap(self, url):
        if url in self.thumb_cache:
            return self.thumb_cache[url]
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return None
            image = QImage.fromData(resp.content)
            if image.isNull():
                return None
            pixmap = QPixmap.fromImage(image)
            self.thumb_cache[url] = pixmap
            return pixmap
        except Exception:
            return None

    def fetch_tv_metadata(self, imdb_id):
        self.log(f"Fetching episodes for {imdb_id}...")
        self.combo_season.clear()
        self.combo_episode.clear()
        self.episode_data = {}

        try:
            lookup = requests.get(f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}", timeout=5)
            if lookup.status_code != 200:
                self.log("Show not found on TVMaze.")
                return

            tvmaze_id = lookup.json()['id']
            eps_resp = requests.get(f"https://api.tvmaze.com/shows/{tvmaze_id}/episodes", timeout=5)
            episodes = eps_resp.json()

            for ep in episodes:
                s = ep['season']
                e = ep['number']
                name = ep.get('name', f"Episode {e}")
                
                if s not in self.episode_data:
                    self.episode_data[s] = []
                self.episode_data[s].append({'num': e, 'name': name})

            for s in sorted(self.episode_data.keys()):
                self.combo_season.addItem(f"Season {s}", userData=s)
            
            self.log(f"Loaded {len(self.episode_data)} seasons!")

        except Exception as e:
            self.log(f"API Error: {e}")

    def update_episodes_list(self):
        self.combo_episode.clear()
        season_num = self.combo_season.currentData()
        
        if season_num in self.episode_data:
            for ep in self.episode_data[season_num]:
                label = f"{ep['num']}. {ep['name']}"
                self.combo_episode.addItem(label, userData=ep['num'])

    def load_video(self):
        video_id = self.id_input.text().strip()
        if not video_id:
            self.log("Error: Missing ID")
            return

        base_url = "https://vidfast.pro"
        params = "?autoPlay=true&theme=27ae60"

        if self.is_tv_checkbox.isChecked():
            s = self.combo_season.currentData()
            e = self.combo_episode.currentData()
            if s is None or e is None:
                self.log("Error: Select Season/Episode")
                return
            url = f"{base_url}/tv/{video_id}/{s}/{e}{params}"
        else:
            url = f"{base_url}/movie/{video_id}{params}"

        self.web_view.setUrl(QUrl(url))
        self.log(f"Loading {url}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VidFastPlayer()
    player.show()
    sys.exit(app.exec())

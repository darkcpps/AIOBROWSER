import logging
import re
import threading
from urllib.parse import quote

import requests
from PyQt6.QtCore import (
    Q_ARG,
    QEvent,
    QMetaObject,
    QTimer,
    Qt,
    QUrl,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ui.core.components import InfoBanner, LoadingWidget
from ui.core.styles import COLORS, get_colors

class VideoStreamTab(QWidget):
    results_ready = pyqtSignal(list)

    def __init__(self, main_app=None):
        super().__init__(main_app)
        self.main_app = main_app
        self.results = []
        self.thumb_cache = {}
        self.results_ready.connect(self.display_results)
        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)

        header = QLabel("Video Streaming")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['text_primary']};")
        subheader = QLabel("Search series or movies and watch instantly.")
        subheader.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(header)
        layout.addWidget(subheader)

        info_banner = InfoBanner(
            title="Player tips",
            body_lines=[
                "Press <b>F</b> for fullscreen • Press <b>Esc</b> to exit fullscreen",
                "If the video is buffering or not loading, change servers using the cloud icon in the player.",
            ],
            icon="🎬",
            object_name="VideoStreamingInfoBanner",
        )
        layout.addWidget(info_banner)

        self.search_bar = QFrame()
        self.search_bar.setFixedHeight(60)
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;"
        )
        sb_layout = QHBoxLayout(self.search_bar)
        sb_layout.setContentsMargins(10, 5, 10, 5)
        sb_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a series or movie...")
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet(
            "border: none; background: transparent; padding: 0 15px; font-size: 16px;"
        )
        self.search_input.returnPressed.connect(self.start_search)
        sb_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedSize(100, 40)
        self.search_btn.clicked.connect(self.start_search)
        sb_layout.addWidget(self.search_btn)
        layout.addWidget(self.search_bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(15)
        self.scroll.setWidget(self.results_widget)
        layout.addWidget(self.scroll)

    def setup_animations(self):
        self.glow_timer = QTimer()
        self.glow_timer.setInterval(50)
        self.glow_value = 0
        self.glow_direction = 1
        self.glow_timer.timeout.connect(self.animate_glow)
        self.glow_effect = QGraphicsDropShadowEffect()

    def animate_glow(self):
        self.glow_value += self.glow_direction * 5
        if self.glow_value >= 100:
            self.glow_value = 100
            self.glow_direction = -1
        elif self.glow_value <= 0:
            self.glow_value = 0
            self.glow_direction = 1
        glow_intensity = self.glow_value / 100.0

        c = QColor(COLORS["accent_primary"])
        border_color = (
            f"rgba({c.red()}, {c.green()}, {c.blue()}, {0.3 + glow_intensity * 0.7})"
        )

        shadow_blur = 10 + int(glow_intensity * 20)
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 2px solid {border_color}; border-radius: 12px;"
        )
        if self.glow_effect:
            try:
                self.glow_effect.setBlurRadius(shadow_blur)
                self.glow_effect.setColor(
                    QColor(
                        c.red(), c.green(), c.blue(), int(100 + glow_intensity * 155)
                    )
                )
                self.glow_effect.setOffset(0, 0)
            except:
                self.glow_effect = QGraphicsDropShadowEffect()
                self.search_bar.setGraphicsEffect(self.glow_effect)

    def start_glow(self):
        self.glow_value = 0
        self.glow_direction = 1
        self.glow_effect = QGraphicsDropShadowEffect()
        self.search_bar.setGraphicsEffect(self.glow_effect)
        self.glow_timer.start()

    def stop_glow(self):
        self.glow_timer.stop()
        self.search_bar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 12px;"
        )
        try:
            self.search_bar.setGraphicsEffect(None)
            self.glow_effect = None
        except:
            pass

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def log(self, msg):
        logging.getLogger(__name__).debug("[VideoStream] %s", msg)

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.log("Search skipped: empty query.")
            return
        self.log(f"Search started: {query}")
        self.clear_layout(self.results_layout)
        self.loading_widget = LoadingWidget("Searching")
        self.results_layout.addWidget(
            self.loading_widget, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.start_glow()
        threading.Thread(target=self.perform_search, args=(query,), daemon=True).start()

    def perform_search(self, query):
        self.log(f"Querying IMDb suggestions: {query}")
        results = []
        try:
            seen_ids = set()
            imdb_results = self.imdb_suggest(query, max_results=12)
            self.log(f"Raw results returned: {len(imdb_results)}")

            for result in imdb_results:
                imdb_id = result["imdb_id"]
                raw_title = result.get("raw_title", "")
                year = result.get("year")
                if imdb_id in seen_ids:
                    self.log(f"Skipped duplicate IMDb ID: {imdb_id}")
                    continue
                seen_ids.add(imdb_id)
                is_tv = bool(result.get("is_tv"))
                if year is None:
                    self.log(f"Skipped unknown-year result: {imdb_id} ({raw_title})")
                    continue
                info = {"premiered": None, "status": None}
                if not self.is_released_result(is_tv, year, info, raw_title):
                    self.log(f"Skipped unreleased result: {imdb_id} ({raw_title})")
                    continue
                title = (
                    result.get("title")
                    or imdb_id
                )
                self.log(f"Fetching details for {imdb_id} ({title})")
                results.append(
                    {
                        "title": title,
                        "imdb_id": imdb_id,
                        "thumb_url": result.get("thumb_url"),
                        "is_tv": is_tv,
                    }
                )
        except Exception as exc:
            self.log(f"Search error: {exc}")
            results = []
        self.results_ready.emit(results)

    def imdb_suggest(self, query, max_results=12):
        normalized = re.sub(r"\s+", " ", (query or "")).strip().lower()
        if not normalized:
            return []
        slug = quote(normalized.replace(" ", "_"), safe="").lower()
        first = slug[0] if slug else "a"
        url = f"https://v2.sg.media-imdb.com/suggestion/{first}/{slug}.json"
        self.log(f"IMDb suggest URL: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            self.log(f"IMDb suggest failed: {resp.status_code}")
            return []

        payload = resp.json() or {}
        items = payload.get("d") or []
        results = []
        for item in items:
            imdb_id = item.get("id") or ""
            if not imdb_id.startswith("tt"):
                continue

            kind_raw = (item.get("q") or "").strip()
            kind_key = re.sub(r"[^a-z]", "", kind_raw.lower())
            if kind_key in {"tvepisode"}:
                continue
            if kind_key not in {"feature", "tvseries", "tvminiseries", "tvmovie"}:
                continue

            title = (item.get("l") or "").strip()
            year = item.get("y", None)
            try:
                year = int(year) if year is not None else None
            except Exception:
                year = None
            if year is None:
                yr = (item.get("yr") or "").strip()
                match = re.search(r"(\d{4})", yr)
                if match:
                    try:
                        year = int(match.group(1))
                    except Exception:
                        year = None

            thumb_url = None
            image = item.get("i") or {}
            if isinstance(image, dict):
                thumb_url = image.get("imageUrl")

            is_tv = kind_key in {"tvseries", "tvminiseries"}
            raw_title = f"{title} ({kind_raw})" if kind_raw else title
            results.append(
                {
                    "imdb_id": imdb_id,
                    "title": title,
                    "raw_title": raw_title,
                    "year": year,
                    "thumb_url": thumb_url,
                    "is_tv": is_tv,
                }
            )

            if len(results) >= max_results:
                break

        return results

    def extract_year(self, text):
        s = text or ""
        match = re.search(r"\((\d{4})(?:–\d{4})?\)", s)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                return None
        match = re.search(r"\b(\d{4})\b", s)
        if match:
            try:
                return int(match.group(1))
            except Exception:
                return None
        return None

    def is_released_result(self, is_tv, year, tvmaze_info, raw_title):
        from datetime import date

        now = date.today()
        raw = (raw_title or "").lower()
        if any(term in raw for term in ("upcoming", "in production", "announced")):
            return False
        if is_tv:
            if year and year > now.year:
                return False
            status = (tvmaze_info or {}).get("status") or ""
            if status.lower() in {"in development", "to be determined"}:
                return False
            premiered = (tvmaze_info or {}).get("premiered")
            if premiered:
                try:
                    y, m, d = premiered.split("-", 2)
                    if date(int(y), int(m), int(d)) > now:
                        return False
                except Exception:
                    pass
            return True

        if year and year > now.year:
            return False
        if tvmaze_info and tvmaze_info.get("premiered"):
            # Non-TV items shouldn't have TVMaze premiered; ignore.
            pass
        return True

    def clean_ddg_title(self, raw_title):
        title = (raw_title or "").replace(" - IMDb", "").strip()
        extracted = self._extract_title_from_noisy_string(title)
        if extracted:
            title = extracted
        if re.search(r"https?://", title, flags=re.I) or "imdb.com/title/" in title:
            return None
        title = re.sub(
            r"www\.\s*imdb\s*\.\s*com\s*›\s*title\s*›\s*tt\d+\s*",
            "",
            title,
            flags=re.I,
        )
        extracted = self._extract_title_from_noisy_string(title)
        if extracted:
            title = extracted
        if "⭐" in title:
            title = title.split("⭐", 1)[0].strip()
        title = re.sub(r"\s*\|\s.*$", "", title).strip()
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _extract_title_from_noisy_string(self, title):
        cleaned = re.sub(r"\s+", " ", (title or "")).strip()
        if not cleaned:
            return None

        # Prefer patterns like: Name (TV Series 2008–2013) / Name (TV Mini Series 2020)
        match = re.search(
            r"\b([A-Za-z0-9][^()]{1,80}?)\s*\((?:TV Series|TV Mini Series|TV Movie|TV Special|Movie|Short|Video)\b",
            cleaned,
            flags=re.I,
        )
        if match:
            return match.group(1).strip(' "\'')

        # Or: Name (2010) / Name (2008–2013)
        match = re.search(
            r"\b([A-Za-z0-9][^()]{1,80}?)\s*\((?:\d{4}(?:–\d{4})?)\)",
            cleaned,
        )
        if match:
            return match.group(1).strip(' "\'')

        # If DDG gives a long repeated breadcrumb string, keep only the first chunk.
        if len(cleaned) > 120:
            cleaned = cleaned.split(" www.", 1)[0].strip()
            cleaned = cleaned.split(" - ", 1)[0].strip()
            cleaned = cleaned.split(" | ", 1)[0].strip()
            cleaned = cleaned.split("⭐", 1)[0].strip()
            if 0 < len(cleaned) <= 90:
                return cleaned.strip(' "\'')

        return None

    @pyqtSlot(list)
    def display_results(self, results):
        if hasattr(self, "loading_widget") and self.loading_widget:
            self.loading_widget.stop()
            self.loading_widget.deleteLater()
            self.loading_widget = None
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")
        self.stop_glow()
        self.results = results
        self.clear_layout(self.results_layout)
        self.log(f"Display results: {len(results)} items.")

        if not results:
            empty = QLabel("No results found.")
            empty.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 16px; margin-top: 50px;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_layout.addWidget(empty)
            return

        for i, item in enumerate(results):
            card = StreamResultCard(item, self, delay=i * 100)
            self.results_layout.addWidget(card)

    def fetch_show_info(self, imdb_id):
        try:
            resp = requests.get(
                f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}", timeout=5
            )
            if resp.status_code != 200:
                self.log(f"TVMaze lookup failed for {imdb_id}: {resp.status_code}")
                return {
                    "is_tv": False,
                    "thumb_url": None,
                    "title": None,
                    "premiered": None,
                    "status": None,
                }
            data = resp.json()
            image = data.get("image") or {}
            return {
                "is_tv": True,
                "thumb_url": image.get("medium") or image.get("original"),
                "title": data.get("name"),
                "premiered": data.get("premiered"),
                "status": data.get("status"),
            }
        except Exception as exc:
            self.log(f"TVMaze lookup error for {imdb_id}: {exc}")
            return {
                "is_tv": False,
                "thumb_url": None,
                "title": None,
                "premiered": None,
                "status": None,
            }

    def open_watch_dialog(self, item):
        self.log(f"Watch clicked: {item.get('imdb_id')} ({item.get('title')})")
        dialog = StreamWatchDialog(self, item)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.log("Watch canceled.")
            return
        url = dialog.get_stream_url()
        if not url:
            self.log("Watch aborted: no stream URL.")
            return
        self.log(f"Launching fullscreen player: {url}")
        self.open_fullscreen_player(url, item.get("title", "Video"))

    def open_fullscreen_player(self, url, title):
        self._player_dialog = FullscreenPlayerDialog(self, url, title)
        self._player_dialog.showFullScreen()


class StreamResultCard(QFrame):
    def __init__(self, item, parent=None, delay=0):
        super().__init__(parent)
        self.item = item
        self.parent = parent
        self.delay = delay
        self.thumb_cache = {}
        self.init_ui()
        QTimer.singleShot(delay, self.start_image_load)

    def init_ui(self):
        self.setObjectName("Card")
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 20, 12)
        layout.setSpacing(20)

        self.image_label = QLabel()
        self.image_label.setFixedSize(90, 125)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; border-radius: 10px;"
        )
        self.image_label.setText("No\nImage")
        layout.addWidget(self.image_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        kind = "Series" if self.item.get("is_tv") else "Movie"
        kind_color = (
            COLORS["accent_primary"] if self.item.get("is_tv") else COLORS["accent_green"]
        )
        kind_badge = QLabel(kind)
        kind_badge.setStyleSheet(
            f"background-color: {kind_color}; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 700;"
        )
        kind_row = QHBoxLayout()
        kind_row.addWidget(kind_badge)
        kind_row.addStretch()
        info_layout.addLayout(kind_row)

        title_label = QLabel(self.item.get("title", "Unknown"))
        title_label.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']};"
        )
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        meta_label = QLabel(self.item.get("imdb_id", ""))
        meta_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        info_layout.addWidget(meta_label)
        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

        watch_btn = QPushButton("Watch")
        watch_btn.setFixedSize(120, 45)
        watch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        watch_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: white;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
            """
        )
        watch_btn.clicked.connect(lambda: self.parent.open_watch_dialog(self.item))
        layout.addWidget(watch_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def start_image_load(self):
        threading.Thread(target=self.load_image, daemon=True).start()

    def load_image(self):
        url = self.item.get("thumb_url")
        if not url:
            if hasattr(self.parent, "log"):
                self.parent.log(f"No thumbnail for {self.item.get('imdb_id')}")
            return
        try:
            response = requests.get(url, timeout=5)
            image = QImage.fromData(response.content)
            if image.isNull():
                return
            pixmap = QPixmap.fromImage(image)
            QMetaObject.invokeMethod(
                self,
                "set_pixmap",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(QPixmap, pixmap),
            )
        except Exception as exc:
            if hasattr(self.parent, "log"):
                self.parent.log(f"Thumbnail error: {exc}")
            pass

    @pyqtSlot(QPixmap)
    def set_pixmap(self, pixmap):
        self.image_label.setPixmap(
            pixmap.scaled(
                90,
                125,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.image_label.setText("")


class StreamWatchDialog(QDialog):
    def __init__(self, parent, item):
        super().__init__(parent)
        self.main_app = getattr(parent, "main_app", parent)
        self.item = item
        self.episode_data = {}
        self.selected_url = None
        self.setWindowTitle("Choose Episode")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        colors = get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(self.item.get("title", ""))
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        self.type_label = QLabel("Pick season and episode to watch.")
        self.type_label.setStyleSheet(f"color: {colors['text_secondary']};")
        layout.addWidget(self.type_label)

        self.combo_season = QComboBox()
        self.combo_season.setPlaceholderText("Season")
        self.combo_season.currentIndexChanged.connect(self.update_episodes_list)

        self.combo_episode = QComboBox()
        self.combo_episode.setPlaceholderText("Episode")

        layout.addWidget(self.combo_season)
        layout.addWidget(self.combo_episode)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.play_btn = QPushButton("Play Fullscreen")
        self.play_btn.setStyleSheet(
            f"QPushButton {{ background-color: {colors['accent_primary']}; }}"
        )
        self.play_btn.clicked.connect(self.on_play_clicked)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.play_btn)
        layout.addLayout(btn_row)

        if self.item.get("is_tv"):
            self.fetch_tv_metadata(self.item.get("imdb_id"))
        else:
            self.type_label.setText("This looks like a movie.")
            self.combo_season.hide()
            self.combo_episode.hide()

    def fetch_tv_metadata(self, imdb_id):
        self.combo_season.clear()
        self.combo_episode.clear()
        self.episode_data = {}
        try:
            if hasattr(self.main_app, "log"):
                self.main_app.log(f"Loading episodes for {imdb_id}")
            lookup = requests.get(
                f"https://api.tvmaze.com/lookup/shows?imdb={imdb_id}", timeout=5
            )
            if lookup.status_code != 200:
                if hasattr(self.main_app, "log"):
                    self.main_app.log(
                        f"Episode lookup failed: {imdb_id} ({lookup.status_code})"
                    )
                self.type_label.setText("Show not found on TVMaze.")
                return
            tvmaze_id = lookup.json()["id"]
            eps_resp = requests.get(
                f"https://api.tvmaze.com/shows/{tvmaze_id}/episodes", timeout=5
            )
            episodes = eps_resp.json()
            for ep in episodes:
                season = ep["season"]
                number = ep["number"]
                name = ep.get("name", f"Episode {number}")
                self.episode_data.setdefault(season, []).append(
                    {"num": number, "name": name}
                )
            for season in sorted(self.episode_data.keys()):
                self.combo_season.addItem(f"Season {season}", userData=season)
            if not self.episode_data:
                self.type_label.setText("No episode data found.")
        except Exception:
            self.type_label.setText("Error loading episodes.")

    def update_episodes_list(self):
        self.combo_episode.clear()
        season_num = self.combo_season.currentData()
        if season_num in self.episode_data:
            for ep in self.episode_data[season_num]:
                label = f"{ep['num']}. {ep['name']}"
                self.combo_episode.addItem(label, userData=ep["num"])

    def on_play_clicked(self):
        url = self.build_stream_url()
        if not url:
            if hasattr(self.main_app, "log"):
                self.main_app.log("Play blocked: missing season/episode.")
            return
        if hasattr(self.main_app, "log"):
            self.main_app.log(f"Play confirmed: {url}")
        self.selected_url = url
        self.accept()

    def build_stream_url(self):
        imdb_id = self.item.get("imdb_id")
        if not imdb_id:
            return None
        base_url = "https://vidfast.pro"
        params = "?autoPlay=true"
        if self.item.get("is_tv"):
            season = self.combo_season.currentData()
            episode = self.combo_episode.currentData()
            if season is None or episode is None:
                QMessageBox.warning(
                    self, "Missing Selection", "Pick a season and episode first."
                )
                return None
            return f"{base_url}/tv/{imdb_id}/{season}/{episode}{params}"
        return f"{base_url}/movie/{imdb_id}{params}"

    def get_stream_url(self):
        return self.selected_url


class FullscreenPlayerDialog(QDialog):
    def __init__(self, parent, url, title):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._base_flags = self.windowFlags()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(url))
        layout.addWidget(self.web_view)

        self._f_shortcut = QShortcut(QKeySequence("F"), self)
        self._f_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._f_shortcut.activated.connect(self.toggle_fullscreen)

        self._esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._esc_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._esc_shortcut.activated.connect(self.exit_fullscreen)
        self.web_view.installEventFilter(self)

        try:
            self.web_view.page().fullScreenRequested.connect(
                self._handle_fullscreen_request
            )
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj is self.web_view and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                if self.isFullScreen():
                    self.exit_fullscreen()
                    return True
            if event.key() == Qt.Key.Key_F:
                self.toggle_fullscreen()
                return True
        return super().eventFilter(obj, event)

    def _handle_fullscreen_request(self, request):
        try:
            request.accept()
            if request.toggleOn():
                self.enter_fullscreen()
            else:
                self.exit_fullscreen()
        except Exception:
            pass

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        if self.isFullScreen():
            return
        try:
            self.setWindowFlags(
                self._base_flags
                | Qt.WindowType.FramelessWindowHint
            )
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen:
                self.setGeometry(screen.geometry())
            self.showFullScreen()
            self.raise_()
            self.activateWindow()
        except Exception:
            self.showFullScreen()

    def exit_fullscreen(self):
        if not self.isFullScreen():
            return
        try:
            self.web_view.page().runJavaScript(
                "if (document.fullscreenElement) { document.exitFullscreen(); }"
            )
        except Exception:
            pass
        try:
            self.setWindowFlags(self._base_flags)
            self.showNormal()
        except Exception:
            self.showNormal()
        try:
            self.resize(1280, 720)
        except Exception:
            pass
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.center() - self.rect().center())
        except Exception:
            pass

import webbrowser

from core import emulators
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from ui.core.components import InfoBanner
from ui.core.styles import COLORS, get_current_theme


def _build_emulator_platform_index():
    index = {}
    for platform_key, emulator_ids in emulators.PLATFORM_TO_EMULATORS.items():
        for emu_id in emulator_ids:
            index.setdefault(emu_id, set()).add(platform_key)
    return index


_EMU_PLATFORMS = _build_emulator_platform_index()


class EmulatorCard(QFrame):
    def __init__(self, option, main_app):
        super().__init__()
        self.option = option
        self.main_app = main_app
        self.setObjectName("EmulatorCard")
        self.status_label = None
        self.initUI()

    def initUI(self):
        self.setStyleSheet(
            f"""
            QFrame#EmulatorCard {{
                background-color: {COLORS["bg_card"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 14px;
            }}
            QFrame#EmulatorCard:hover {{
                border: 1px solid {COLORS["accent_primary"]};
            }}
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(6)

        title = QLabel(self.option.name)
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {COLORS['text_primary']};"
        )
        left.addWidget(title)

        platforms = sorted(_EMU_PLATFORMS.get(self.option.id, set()))
        platform_names = ", ".join(emulators.get_platform_display_name(p) for p in platforms) or "—"
        subtitle = QLabel(f"Supports: {platform_names}")
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']};"
        )
        subtitle.setWordWrap(True)
        left.addWidget(subtitle)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 12px;")
        left.addWidget(self.status_label)

        layout.addLayout(left, 1)

        btns = QHBoxLayout()
        btns.setSpacing(10)

        locate_btn = QPushButton("Locate")
        locate_btn.setFixedHeight(34)
        locate_btn.clicked.connect(self.locate_exe)
        btns.addWidget(locate_btn)

        page_btn = QPushButton("Open Page")
        page_btn.setFixedHeight(34)
        page_btn.clicked.connect(lambda: webbrowser.open(self.option.download_page_url))
        btns.addWidget(page_btn)

        download_btn = QPushButton("Download")
        download_btn.setFixedHeight(34)
        hover_text = "#000000" if get_current_theme() == "black_gold" else "white"
        download_btn.setStyleSheet(
            f"QPushButton {{ background: {COLORS['accent_primary']}; color: white; font-weight: 800; border-radius: 8px; padding: 0 14px; }}"
            f"QPushButton:hover {{ background: {COLORS['accent_secondary']}; color: {hover_text}; }}"
        )
        download_btn.clicked.connect(self.download)
        btns.addWidget(download_btn)

        layout.addLayout(btns)
        self.update_status()

    def is_installed(self):
        try:
            emulator_paths = self.main_app.settings_manager.get("emulator_paths", {}) or {}
        except Exception:
            emulator_paths = {}
        return emulators.find_emulator_executable(self.option, emulator_paths) is not None

    def locate_exe(self):
        start_dir = self.main_app.settings_manager.get("default_download_path", "")
        if not start_dir:
            start_dir = ""
        exe_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Locate {self.option.name} executable",
            start_dir,
            "Executable (*.exe)",
        )
        if not exe_path:
            return
        emulator_paths = self.main_app.settings_manager.get("emulator_paths", {}) or {}
        emulator_paths = dict(emulator_paths)
        emulator_paths[self.option.id] = exe_path
        self.main_app.settings_manager.update_setting("emulator_paths", emulator_paths)
        self.update_status()

    def update_status(self):
        installed = self.is_installed()
        if self.status_label:
            self.status_label.setText("Detected on this PC" if installed else "Not detected")
            self.status_label.setStyleSheet(
                f"font-size: 12px; color: {COLORS['accent_secondary'] if installed else COLORS['text_muted']};"
            )

    def download(self):
        if hasattr(self.main_app, "_start_emulator_download"):
            self.main_app._start_emulator_download(self.option)
        else:
            webbrowser.open(self.option.download_page_url)


class EmulatorsTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.cards = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        layout.addWidget(
            InfoBanner(
                title="Emulators",
                body_lines=[
                    "Download and manage emulators used for ROMs.",
                    "Use Locate if you already have an emulator installed (portable or custom path).",
                ],
                icon="🎮",
                object_name="EmulatorsInfoBanner",
                compact=True,
            )
        )

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_row.addWidget(self.search_input, 2)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("All Platforms", "all")
        for key in sorted(emulators.PLATFORM_TO_EMULATORS.keys()):
            self.platform_combo.addItem(emulators.get_platform_display_name(key), key)
        self.platform_combo.currentIndexChanged.connect(self.apply_filters)
        filter_row.addWidget(self.platform_combo, 1)

        layout.addLayout(filter_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(12)
        self.container_layout.setContentsMargins(0, 0, 10, 0)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.build_cards()
        self.apply_filters()

    def build_cards(self):
        for c in self.cards:
            c.deleteLater()
        self.cards = []

        options = list(emulators.EMULATORS.values())
        options.sort(key=lambda o: o.name.lower())

        for opt in options:
            card = EmulatorCard(opt, self.main_app)
            self.cards.append(card)
            self.container_layout.addWidget(card)

        self.container_layout.addStretch()

    def apply_filters(self):
        q = (self.search_input.text() or "").strip().lower()
        platform_key = self.platform_combo.currentData()

        for card in self.cards:
            name_ok = (not q) or (q in card.option.name.lower())
            plat_ok = True
            if platform_key and platform_key != "all":
                plat_ok = platform_key in _EMU_PLATFORMS.get(card.option.id, set())
            card.setVisible(name_ok and plat_ok)

    def refresh(self):
        for card in self.cards:
            card.update_status()

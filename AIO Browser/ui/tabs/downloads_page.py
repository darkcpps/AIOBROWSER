# ui/downloads.py
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.core.components import InfoBanner
from ui.core.styles import COLORS


class DownloadItemWidget(QFrame):
    removed = pyqtSignal(object)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.control_flags = {"paused": False, "stopped": False}
        self.setObjectName("DownloadItem")
        self.initUI()

    def initUI(self):
        self.setMinimumHeight(120)
        self.setStyleSheet(f"""
            QFrame#DownloadItem {{
                background-color: {COLORS["bg_card"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 15px;
            }}
            QFrame#DownloadItem:hover {{
                border: 1px solid {COLORS["accent_primary"]};
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)

        # Header: Title and Status
        header_layout = QHBoxLayout()

        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet(
            f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};"
        )
        header_layout.addWidget(self.title_label, 1)

        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']};"
        )
        header_layout.addWidget(self.status_label)

        main_layout.addLayout(header_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS["bg_secondary"]};
                border-radius: 4px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS["accent_primary"]},
                    stop:1 {COLORS["accent_secondary"]});
                border-radius: 4px;
            }}
        """)
        main_layout.addWidget(self.progress_bar)

        # Bottom section: Speed, ETA, and Controls
        bottom_layout = QHBoxLayout()

        self.info_label = QLabel("Waiting for link resolution...")
        self.info_label.setStyleSheet(
            f"font-size: 11px; color: {COLORS['text_muted']};"
        )
        bottom_layout.addWidget(self.info_label, 1)

        self.btn_frame = QWidget()
        self.btn_layout = QHBoxLayout(self.btn_frame)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.setSpacing(10)

        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setFixedSize(35, 35)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setStyleSheet(self.get_button_style(COLORS["bg_secondary"]))
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("✕")
        self.stop_btn.setFixedSize(35, 35)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet(self.get_button_style(COLORS["accent_red"]))
        self.stop_btn.clicked.connect(self.handle_stop_or_remove)
        self.btn_layout.addWidget(self.stop_btn)

        self.btn_frame.hide()  # Hide until download starts
        bottom_layout.addWidget(self.btn_frame)

        main_layout.addLayout(bottom_layout)

    def get_button_style(self, bg):
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_primary"] if bg != COLORS["accent_red"] else COLORS["accent_red_hover"]};
            }}
        """

    def toggle_pause(self):
        self.control_flags["paused"] = not self.control_flags["paused"]
        if self.control_flags["paused"]:
            self.pause_btn.setText("▶")
            self.status_label.setText("Paused")
            self.pause_btn.setStyleSheet(self.get_button_style(COLORS["accent_green"]))
        else:
            self.pause_btn.setText("⏸")
            self.status_label.setText("Downloading")
            self.pause_btn.setStyleSheet(self.get_button_style(COLORS["bg_secondary"]))

    def stop_download(self):
        self.control_flags["stopped"] = True
        self.status_label.setText("Stopped")
        self.setEnabled(False)
        self.info_label.setText("Download cancelled by user.")

    def handle_stop_or_remove(self):
        # If already stopped or finished (indicated by disabled or special status), remove it
        if (
            self.control_flags["stopped"]
            or self.status_label.text() == "Finished"
            or self.status_label.text() == "Stopped"
            or self.status_label.text() == "Error"
        ):
            self.removed.emit(self)
        else:
            # First click stops it
            self.stop_download()
            # Change icon to a "bin" or just keep X for second click
            self.stop_btn.setText("🗑")
            self.setEnabled(True)  # Re-enable so they can click the trash icon
            self.pause_btn.hide()

    @pyqtSlot(str, float)
    def update_progress(self, status_msg, progress):
        self.info_label.setText(status_msg)
        self.progress_bar.setValue(int(progress * 100))

        # Check msg for status indicators
        if "Complete" in status_msg or "✅" in status_msg:
            self.status_label.setText("Finished")
            self.pause_btn.hide()
            self.stop_btn.setText("🗑")
        elif "Error" in status_msg or "❌" in status_msg:
            self.status_label.setText("Error")
            self.control_flags["stopped"] = True
            self.stop_btn.setText("🗑")
            self.pause_btn.hide()
        elif "Stopped" in status_msg or "⏹" in status_msg:
            self.status_label.setText("Stopped")
            self.control_flags["stopped"] = True
            self.stop_btn.setText("🗑")
            self.pause_btn.hide()
        elif self.control_flags["paused"]:
            self.status_label.setText("Paused")
        else:
            self.status_label.setText("Downloading")

        if not self.btn_frame.isVisible():
            self.btn_frame.show()


class DownloadsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.items = {}

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Header
        header = QLabel("Active Downloads")
        header.setStyleSheet(
            f"font-size: 24px; font-weight: 800; color: {COLORS['text_primary']};"
        )
        layout.addWidget(header)

        layout.addWidget(
            InfoBanner(
                title="Downloads",
                body_lines=[
                    "Downloads started in other tabs show up here. Use the controls on each card to pause/stop/remove.",
                ],
                icon="⬇️",
                object_name="DownloadsInfoBanner",
                compact=True,
            )
        )

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(15)
        self.container_layout.setContentsMargins(0, 0, 10, 0)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # Empty state message
        self.empty_label = QLabel("No active downloads. Go find some games!")
        self.empty_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14px;"
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.empty_label)

    def add_download(self, download_id, title):
        if self.empty_label.isVisible():
            self.empty_label.hide()

        item = DownloadItemWidget(title)
        item.removed.connect(lambda i: self.remove_download_by_widget(i, download_id))
        self.items[download_id] = item
        self.container_layout.insertWidget(0, item)
        return item

    def remove_download_by_widget(self, widget, download_id):
        if download_id in self.items:
            del self.items[download_id]
        widget.deleteLater()

        # Check if empty
        QTimer.singleShot(100, self.check_empty)

    def check_empty(self):
        if not self.items:
            self.empty_label.show()

    def remove_download(self, download_id):
        if download_id in self.items:
            item = self.items.pop(download_id)
            item.deleteLater()

        if not self.items:
            self.empty_label.show()

    def has_active_downloads(self):
        """Check if there are any downloads currently running (not finished/stopped)"""
        for item in self.items.values():
            status = item.status_label.text()
            if (
                status == "Downloading"
                or status == "Paused"
                or status == "Initializing..."
            ):
                return True
        return False

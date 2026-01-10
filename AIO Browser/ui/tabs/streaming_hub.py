from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from ui.tabs.video_stream_tab import VideoStreamTab


class StreamingHub(QWidget):
    """Top-level Streaming hub containing streaming-related subtabs."""

    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabBar::tab { padding: 12px 25px; margin: 0px; }
            QTabBar { margin: 0px; padding: 0px; }
            QTabWidget::pane { border: none; margin: 0px; padding: 0px; background: transparent; }
            """
        )

        self.video_streaming_tab = VideoStreamTab(self.main_app)
        self.tab_widget.addTab(self.video_streaming_tab, "Video Streaming")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

class VidFastPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StreamerV1")
        self.resize(1000, 600)
        self.init_ui()

    def init_ui(self):
        # 1. Main Layout
        layout = QVBoxLayout()
        
        # 2. Input Controls (Top Bar)
        input_layout = QHBoxLayout()
        
        # ID Input
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID (e.g. tt4574334)")
        self.id_input.setFixedWidth(150)
        
        # Season Input
        self.season_input = QLineEdit()
        self.season_input.setPlaceholderText("S")
        self.season_input.setFixedWidth(40)
        
        # Episode Input
        self.episode_input = QLineEdit()
        self.episode_input.setPlaceholderText("E")
        self.episode_input.setFixedWidth(40)
        
        # Watch Button
        self.btn_play = QPushButton("Watch")
        self.btn_play.clicked.connect(self.load_video)
        
        # Add widgets to row
        input_layout.addWidget(QLabel("ID:"))
        input_layout.addWidget(self.id_input)
        input_layout.addWidget(QLabel("Season:"))
        input_layout.addWidget(self.season_input)
        input_layout.addWidget(QLabel("Ep:"))
        input_layout.addWidget(self.episode_input)
        input_layout.addWidget(self.btn_play)
        input_layout.addStretch() # Pushes everything to the left
        
        # 3. Web View
        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: black;") 

        # 4. Add to main layout
        layout.addLayout(input_layout)
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)

    def load_video(self):
        video_id = self.id_input.text().strip()
        season = self.season_input.text().strip()
        episode = self.episode_input.text().strip()
        
        if not video_id:
            return

        base_url = "https://vidfast.pro"
        params = "?autoPlay=true&theme=16A085"
        
        # LOGIC: If Season AND Episode are filled, it's a TV Show
        if season and episode:
            # URL Structure: /tv/{id}/{season}/{episode}
            full_url = f"{base_url}/tv/{video_id}/{season}/{episode}{params}"
            print(f"Streaming TV Show: S{season} E{episode}")
        else:
            # URL Structure: /movie/{id}
            full_url = f"{base_url}/movie/{video_id}{params}"
            print("Streaming Movie")

        self.web_view.setUrl(QUrl(full_url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VidFastPlayer()
    player.show()
    sys.exit(app.exec())

import sys
import time
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QProgressBar, QLabel, QFileDialog, 
                             QInputDialog, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# Try to import libtorrent
try:
    import libtorrent as lt
    HAS_LIBTORRENT = True
except ImportError:
    HAS_LIBTORRENT = False

class DownloadWorker(QThread):
    progress_update = pyqtSignal(int, str, str)
    finished = pyqtSignal()

    def __init__(self, source, save_path):
        super().__init__()
        self.source = source  # Can be a file path or a magnet link
        self.save_path = save_path
        self.is_running = True

    def run(self):
        if not HAS_LIBTORRENT:
            self.progress_update.emit(0, "Error: libtorrent not installed!", "0 kB/s")
            return

        # 1. Create Session
        ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})

        # 2. Add Torrent (Magnet or File)
        params = {'save_path': self.save_path}
        
        if self.source.startswith("magnet:?"):
            # It's a magnet link
            handle = lt.add_magnet_uri(ses, self.source, params)
            self.progress_update.emit(0, "Fetching Magnet Metadata...", "0.0 kB/s")
        else:
            # It's a file
            info = lt.torrent_info(self.source)
            params['ti'] = info
            handle = ses.add_torrent(params)

        # 3. Download Loop
        while self.is_running:
            s = handle.status()
            
            # Check if we have metadata (crucial for magnets)
            if not handle.has_metadata():
                time.sleep(1)
                continue

            progress = int(s.progress * 100)
            download_rate = s.download_rate / 1000  # kB/s
            
            # Get specific state (checking files, downloading, seeding)
            state_str = s.state.name if hasattr(s.state, 'name') else str(s.state)
            
            status_msg = f"{state_str} | Peers: {s.num_peers}"
            speed_msg = f"{download_rate:.1f} kB/s"
            
            self.progress_update.emit(progress, status_msg, speed_msg)

            if handle.is_seed():
                self.progress_update.emit(100, "Download Complete! Seeding...", "0.0 kB/s")
                break
                
            time.sleep(1)
            
        self.finished.emit()

    def stop(self):
        self.is_running = False

class TorrentClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Magnet Client")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # UI Elements
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        self.lbl_speed = QLabel("Speed: 0 kB/s")
        self.lbl_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_speed)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Buttons
        self.btn_file = QPushButton("Load .torrent File")
        self.btn_file.clicked.connect(self.load_file)
        layout.addWidget(self.btn_file)

        self.btn_magnet = QPushButton("Paste Magnet Link")
        self.btn_magnet.clicked.connect(self.load_magnet)
        layout.addWidget(self.btn_magnet)

        self.worker = None

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Torrent", "", "Torrent Files (*.torrent)")
        if file_name:
            self.start_download(file_name)

    def load_magnet(self):
        # Open a simple dialog box to paste the link
        link, ok = QInputDialog.getText(self, "Add Magnet", "Paste Magnet Link:")
        if ok and link:
            self.start_download(link)

    def start_download(self, source):
        if self.worker is not None:
            self.worker.stop()
            
        # Save to current folder
        save_path = os.getcwd()
        
        self.worker = DownloadWorker(source, save_path)
        self.worker.progress_update.connect(self.update_ui)
        self.worker.start()
        
        self.disable_buttons(True)

    def disable_buttons(self, disable):
        self.btn_file.setEnabled(not disable)
        self.btn_magnet.setEnabled(not disable)

    def update_ui(self, progress, status, speed):
        self.progress_bar.setValue(progress)
        self.lbl_status.setText(status)
        self.lbl_speed.setText(speed)
        
        if progress == 100:
            self.disable_buttons(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TorrentClient()
    window.show()
    sys.exit(app.exec())

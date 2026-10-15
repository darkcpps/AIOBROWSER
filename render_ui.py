"""Render the AIO Browser UI to PNGs for visual review.

Usage:  python3 render_ui.py [theme] [tab1 tab2 ...]
Defaults to the "default" theme and all tabs.
"""
import os
import sys
import tempfile

sys.path.insert(0, "/workspace/AIO Browser")
os.chdir(tempfile.mkdtemp(prefix="aiobrowser_shots_"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from ui.dialogs.settings_dialog import SettingsManager  # noqa: E402
from ui.core.main_window import GameSearchApp  # noqa: E402

theme = sys.argv[1] if len(sys.argv) > 1 else "default"
tabs = sys.argv[2:] or [
    "games",
    "search",
    "software",
    "patcher",
    "downloader",
    "emulators",
    "downloads",
    "info",
    "settings",
]

OUT = "/workspace/shots"
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv[:1])
sm = SettingsManager()
sm.update_setting("disable_splash", True)
sm.update_setting("theme", theme)

window = GameSearchApp()
window.resize(1300, 840)
window.show()
app.processEvents()

for tab in tabs:
    try:
        window.sidebar.set_active(tab)
    except Exception as exc:  # noqa: BLE001
        print("nav fail", tab, exc)
        continue
    for _ in range(6):
        app.processEvents()
    try:
        from PyQt6.QtTest import QTest

        QTest.qWait(500)
    except Exception:  # noqa: BLE001
        pass
    for _ in range(4):
        app.processEvents()
    path = os.path.join(OUT, f"{theme}__{tab}.png")
    window.grab().save(path)
    print("shot", path)

print("DONE", theme)

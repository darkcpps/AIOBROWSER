"""Render the AIO Browser UI to PNG files.

Useful for documentation and for reviewing UI changes without a desktop.

Usage
-----
    cd "AIO Browser"
    python tools/render_ui.py                      # all tabs, default theme
    python tools/render_ui.py --theme black_gold    # all tabs, one theme
    python tools/render_ui.py games settings        # specific tabs
    python tools/render_ui.py --out ../docs/screenshots

The script runs Qt on the ``offscreen`` platform, so it works head-less (CI,
containers). On Linux the Qt system libraries must be installed, e.g.:

    sudo apt install libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 fontconfig
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ALL_TABS = [
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


def main():
    parser = argparse.ArgumentParser(description="Render the AIO Browser UI to PNGs.")
    parser.add_argument("tabs", nargs="*", default=None, help="tabs to render")
    parser.add_argument("--theme", default="default", help="theme name")
    parser.add_argument(
        "--out",
        default=str(PROJECT_ROOT.parent / "docs" / "screenshots"),
        help="output directory",
    )
    parser.add_argument("--width", type=int, default=1300)
    parser.add_argument("--height", type=int, default=840)
    args = parser.parse_args()

    # Keep the user's real settings file untouched.
    os.chdir(tempfile.mkdtemp(prefix="aiobrowser_render_"))

    from PyQt6.QtWidgets import QApplication

    from ui.core.main_window import GameSearchApp
    from ui.dialogs.settings_dialog import SettingsManager

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv[:1])
    settings = SettingsManager()
    settings.update_setting("disable_splash", True)
    settings.update_setting("theme", args.theme)

    window = GameSearchApp()
    window.resize(args.width, args.height)
    window.show()
    app.processEvents()

    tabs = args.tabs or ALL_TABS
    for tab in tabs:
        try:
            window.sidebar.set_active(tab)
        except Exception as exc:  # noqa: BLE001
            print(f"skip {tab}: {exc}")
            continue
        for _ in range(6):
            app.processEvents()
        try:
            from PyQt6.QtTest import QTest

            QTest.qWait(400)
        except Exception:  # noqa: BLE001
            pass
        for _ in range(4):
            app.processEvents()

        path = out_dir / f"{args.theme}__{tab}.png"
        window.grab().save(str(path))
        print("wrote", path)

    print("done")


if __name__ == "__main__":
    main()

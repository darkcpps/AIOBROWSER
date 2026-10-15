# AIO Browser - A software designed to make life easier

**Status:** 🚧 Work in Progress (Expect bugs + instability)

An all-in-one software solution designed to handle the complicated stuff, making it easier for first-time users.

## Features
- **Game Finder:** Search for games using both **Direct Download** links and **Torrents**.
- **Built-in Patching:** Easily apply the **Goldberg** emulator directly through the app (beginner-friendly).
- **Modern GUI:** A clean, easy-to-navigate interface.
- **Cross-platform:** Runs on **Windows** and **Linux** (macOS mostly, untested). Steam detection, emulator discovery, FFmpeg and the Goldberg patcher all adapt to the current OS.
- **Crisp UI everywhere:** Navigation and banners use built-in vector icons instead of emoji, so the interface looks identical on Linux systems without an emoji font.
- **Visuals:** Includes a custom splash screen on launch.
- **Youtube Downloading** Download Youtube videos or audios
- **Tidal FLACS** Download Tidal FLACS (Experimental)
- **ROMS & Emulators:** Browse and download ROMs and emulators
- **Built-in BitTorrent:** Easier torrenting for beginners.
- **Software downloads:** Install apps.
- **Torrent Search Engine**
  
## Getting started

### Requirements
- Python 3.10 or newer.
- **Linux:** a few system libraries are required for the Qt GUI. On Debian/Ubuntu:
  ```bash
  sudo apt install libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 fontconfig
  ```

Install the runtime dependencies:

```bash
pip install -r "AIO Browser/requirements.txt"
```

Optional features (YouTube downloads, the built-in BitTorrent client and Steam
detection) ship as separate extras and can be installed with:

```bash
pip install -r "AIO Browser/requirements-optional.txt"
```

Every optional import is guarded, so a missing extra only disables the matching
feature instead of crashing the application.

### Run from source
```bash
cd "AIO Browser"
python main_pyqt.py
```

### Running the tests
The suite covers the platform-independent core logic (plus the GUI styling and
icon generation when PyQt6 is available) and runs without a display:

```bash
cd "AIO Browser"
pip install pytest requests beautifulsoup4
python -m pytest
```

## Cross-platform notes
- **Steam:** detected via the Windows registry, the running process (requires
  `psutil`), or the standard install locations for Windows, Linux (native,
  Flatpak and Snap) and macOS.
- **Emulators:** both Windows `.exe` and Linux binary names are searched on
  `PATH` and in the usual install folders.
- **FFmpeg:** the YouTube downloader auto-downloads a portable build for the
  current platform (Windows `.zip`, Linux `.tar.xz`, macOS `.zip`).
- **Goldberg patcher:** swaps `steam_api.dll`, `steam_api64.dll` or
  `libsteam_api.so`, keeping a `.bak` backup for a one-click revert.

## Known issues
- This project is in early access and will be unstable (crashes, failed downloads, broken UI, etc.).
- Bugs are expected. If you find one, please report it in GitHub Issues.

## Planned features
- **Greenluma and Onlinefix Patcher** - Add games on steam and unlock DLC and Online.
- **More download servers:** More sources for faster downloads and more game results.
- **Optional Installations** Make most features optional for user experience and the user gets to choose what they want to install.

## Legal disclaimer
- AIO Browser does not include any game files, and it is not affiliated with any game publishers or platforms.
- You use this software at your own risk. I’m not responsible for any damage, data loss, or issues caused to your computer from using it.

---

*Note: This project is in early development and currently barebones. Updates and new features are coming soon.*



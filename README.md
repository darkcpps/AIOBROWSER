# AIO Browser - A software designed to make life easier

**Status:** 🚧 Work in Progress (Expect bugs + instability)

An all-in-one software solution designed to handle the complicated stuff, making it easier for first-time users.

## Features
- **Game Finder:** Search for games using both **Direct Download** links and **Torrents**.
- **Built-in Patching:** Easily apply the **Goldberg** emulator directly through the app (beginner-friendly).
- **Modern GUI:** A clean, easy-to-navigate interface.
- **Visuals:** Includes a custom splash screen on launch.
- **Youtube Downloading** Download Youtube videos or audios
- **Tidal FLACS** Download Tidal FLACS (Experimental)
- **Video Streaming:** Stream videos directly in-app
- **ROMS & Emulators:** Browse and download ROMs and emulators
- **Built-in BitTorrent:** Easier torrenting for beginners.
- **Software downloads:** Install apps.
- **Torrent Search Engine**
  
## Getting started

### Requirements
- Python 3.10 or newer.

Install the runtime dependencies:

```bash
pip install -r "AIO Browser/requirements.txt"
```

Optional features (YouTube downloads, the built-in BitTorrent client and Steam
detection) ship as separate extras and can be installed with:

```bash
pip install -r "AIO Browser/requirements-optional.txt"
```

### Run from source
```bash
cd "AIO Browser"
python main_pyqt.py
```

### Running the tests
The test-suite covers the platform-independent core logic and runs without a
display or a Qt installation:

```bash
cd "AIO Browser"
pip install pytest requests beautifulsoup4
python -m pytest
```

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



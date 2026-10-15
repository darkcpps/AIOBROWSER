# core/goldberg_patcher.py
# Goldberg Emulator patching functions (cross-platform).
import io
import os
import shutil
import zipfile
from pathlib import Path

import requests

GOLDBERG_ZIP_URL = (
    "https://gitlab.com/Mr_Goldberg/goldberg_emulator/"
    "-/jobs/artifacts/master/download?job=deploy_all"
)

# Library name used by Steam on each platform -> replacement file in the
# Goldberg emulator bundle.
STEAM_API_FILES = (
    "steam_api.dll",
    "steam_api64.dll",
    "libsteam_api.so",
)


def _backup_path(target: Path) -> Path:
    """Backup path for a replaced library (works for any extension)."""
    return target.with_name(target.name + ".bak")


def ensure_goldberg_files(tools_dir):
    """Ensure Goldberg Emulator files are downloaded and ready."""
    tools_path = Path(tools_dir)
    extract_path = tools_path / "goldberg_emu"

    # Check if already exists
    if extract_path.exists() and any(
        (extract_path / name).exists() for name in STEAM_API_FILES
    ):
        return extract_path

    extract_path.mkdir(parents=True, exist_ok=True)

    try:
        # Suppress insecure request warnings for this specific bypass
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        response = requests.get(GOLDBERG_ZIP_URL, timeout=30, verify=False, headers=headers)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_path)
        return extract_path
    except Exception as e:
        print("[ERROR] Failed to download Goldberg: %s" % e)
        return None


def patch_game(game_dir, app_id, tools_dir, nickname="AIOUser", language="english"):
    """Apply the Goldberg patch to a game directory."""
    emu_path = ensure_goldberg_files(tools_dir)
    if not emu_path:
        return False, "Could not download Goldberg Emulator files."

    game_path = Path(game_dir)
    if not game_path.exists():
        return False, "Game directory does not exist: %s" % game_dir

    found_any = False
    log = []

    # Find every Steam API library (recursively) and swap in the emulator.
    for root, dirs, files in os.walk(game_path):
        for filename in files:
            if filename not in STEAM_API_FILES:
                continue

            target_file = Path(root) / filename
            emu_src = emu_path / filename

            if not emu_src.exists():
                # The bundle may nest platform folders; search for it.
                matches = list(emu_path.rglob(filename))
                emu_src = matches[0] if matches else None

            if not emu_src or not Path(emu_src).exists():
                log.append("Skipped %s (no emulator build for this platform)" % filename)
                continue

            # Backup original (never overwrite an existing backup).
            bak_file = _backup_path(target_file)
            if not bak_file.exists():
                shutil.copy2(target_file, bak_file)
                log.append("Backed up %s" % filename)

            # Copy emulator
            shutil.copy2(emu_src, target_file)
            log.append("Replaced %s with Goldberg version" % filename)

            # Create steam_appid.txt in the same folder
            appid_file = Path(root) / "steam_appid.txt"
            with open(appid_file, "w") as f:
                f.write(str(app_id))
            log.append("Created steam_appid.txt (%s)" % app_id)

            # Create Goldberg settings folder
            settings_dir = Path(root) / "settings"
            settings_dir.mkdir(exist_ok=True)

            with open(settings_dir / "account_name.txt", "w") as f:
                f.write(nickname)
            with open(settings_dir / "language.txt", "w") as f:
                f.write(language)

            log.append("Configured identity: %s (%s)" % (nickname, language))
            found_any = True

    if not found_any:
        return (
            False,
            "No Steam API library found in the game directory "
            "(looked for %s)." % ", ".join(STEAM_API_FILES),
        )

    return True, "\n".join(log)


def revert_patch(game_dir):
    """Restore original Steam libraries and remove Goldberg files."""
    game_path = Path(game_dir)
    if not game_path.exists():
        return False, "Game directory does not exist: %s" % game_dir

    found_bak = False
    log = []

    for root, dirs, files in os.walk(game_path):
        # 1. Restore libraries from .bak (handles legacy *.dll.bak too).
        for filename in files:
            if not filename.endswith(".bak"):
                continue

            bak_file = Path(root) / filename
            original_file = bak_file.with_name(filename[: -len(".bak")])

            try:
                if original_file.exists():
                    os.remove(original_file)
                os.rename(bak_file, original_file)
                log.append("Restored %s" % original_file.name)
                found_bak = True
            except Exception as e:
                log.append("Failed to restore %s: %s" % (original_file.name, e))

        # 2. Remove steam_appid.txt if it exists alongside a DLL
        appid_file = Path(root) / "steam_appid.txt"
        if appid_file.exists():
            try:
                os.remove(appid_file)
                log.append("Removed steam_appid.txt")
            except OSError:
                pass

        # 3. Remove Goldberg settings folder
        settings_dir = Path(root) / "settings"
        if settings_dir.exists() and (settings_dir / "account_name.txt").exists():
            try:
                shutil.rmtree(settings_dir)
                log.append("Removed Goldberg settings folder")
            except OSError:
                pass

    if not found_bak:
        return False, "No backup (.bak) files found. Revert may not be possible."

    return True, "\n".join(log)

# core/goldberg_patcher.py
# Goldberg Emulator patching functions
import shutil
import os
import requests
import zipfile
import io
from pathlib import Path

GOLDBERG_ZIP_URL = "https://gitlab.com/Mr_Goldberg/goldberg_emulator/-/jobs/artifacts/master/download?job=deploy_all"

def ensure_goldberg_files(tools_dir):
    """Ensure Goldberg Emulator files are downloaded and ready."""
    tools_path = Path(tools_dir)
    extract_path = tools_path / "goldberg_emu"
    
    # Check if already exists
    if extract_path.exists() and (extract_path / "steam_api64.dll").exists():
        return extract_path
    
    extract_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Suppress insecure request warnings for this specific bypass
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(GOLDBERG_ZIP_URL, timeout=30, verify=False, headers=headers)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(extract_path)
        return extract_path
    except Exception as e:
        print(f"[ERROR] Failed to download Goldberg: {e}")
        return None

def patch_game(game_dir, app_id, tools_dir, nickname="AIOUser", language="english"):
    """Apply Goldberg patch to a game directory."""
    emu_path = ensure_goldberg_files(tools_dir)
    if not emu_path:
        return False, "Could not download Goldberg Emulator files."
    
    game_path = Path(game_dir)
    if not game_path.exists():
        return False, f"Game directory does not exist: {game_dir}"
    
    found_any = False
    log = []
    
    # Files to replace
    mapping = {
        "steam_api.dll": "steam_api.dll",
        "steam_api64.dll": "steam_api64.dll"
    }
    
    # Also for linux if we ever support it: libsteam_api.so
    
    # Find all occurrences of steam_api(64).dll recursively
    for root, dirs, files in os.walk(game_path):
        for filename in files:
            if filename in mapping:
                target_file = Path(root) / filename
                emu_src = emu_path / mapping[filename]
                
                if emu_src.exists():
                    # Backup original
                    bak_file = target_file.with_suffix(".dll.bak")
                    if not bak_file.exists():
                        shutil.copy2(target_file, bak_file)
                        log.append(f"Backed up {filename} to .bak")
                    
                    # Copy emulator
                    shutil.copy2(emu_src, target_file)
                    log.append(f"Replaced {filename} with Goldberg version")
                    
                    # Create steam_appid.txt in the same folder
                    appid_file = Path(root) / "steam_appid.txt"
                    with open(appid_file, "w") as f:
                        f.write(str(app_id))
                    log.append(f"Created steam_appid.txt ({app_id})")
                    
                    # Create Goldberg settings folder
                    settings_dir = Path(root) / "settings"
                    settings_dir.mkdir(exist_ok=True)
                    
                    # Nickname
                    with open(settings_dir / "account_name.txt", "w") as f:
                        f.write(nickname)
                    
                    # Language
                    with open(settings_dir / "language.txt", "w") as f:
                        f.write(language)
                        
                    log.append(f"Configured identity: {nickname} ({language})")
                    
                    found_any = True
    
    if not found_any:
        return False, "No Steam API DLLs found in game directory."
    
    return True, "\n".join(log)

def revert_patch(game_dir):
    """Restore original Steam DLLs and remove Goldberg files."""
    game_path = Path(game_dir)
    if not game_path.exists():
        return False, f"Game directory does not exist: {game_dir}"
    
    found_bak = False
    log = []
    
    for root, dirs, files in os.walk(game_path):
        # 1. Restore DLLs from .bak
        for filename in files:
            if filename.endswith(".dll.bak"):
                bak_file = Path(root) / filename
                original_file = bak_file.with_suffix("") # Removes .bak
                
                try:
                    # Move backup back to original
                    if original_file.exists():
                        os.remove(original_file)
                    os.rename(bak_file, original_file)
                    log.append(f"Restored {original_file.name}")
                    found_bak = True
                except Exception as e:
                    log.append(f"Failed to restore {original_file.name}: {e}")
                    
        # 2. Remove steam_appid.txt if it exists alongside a DLL
        appid_file = Path(root) / "steam_appid.txt"
        if appid_file.exists():
            try:
                os.remove(appid_file)
                log.append("Removed steam_appid.txt")
            except: pass
            
        # 3. Remove Goldberg settings folder
        settings_dir = Path(root) / "settings"
        if settings_dir.exists() and (settings_dir / "account_name.txt").exists():
            try:
                shutil.rmtree(settings_dir)
                log.append("Removed Goldberg settings folder")
            except: pass
            
    if not found_bak:
        return False, "No backup (.bak) files found. Revert may not be possible."
        
    return True, "\n".join(log)

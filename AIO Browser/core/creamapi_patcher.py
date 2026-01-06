# core/creamapi_patcher.py
# CreamAPI patching functions
import shutil
import os
import requests
import zipfile
import io
from pathlib import Path

CREAMAPI_REPO_URL = "https://api.github.com/repos/Warwolfer/auto-creamapi-2/releases/latest"

def ensure_creamapi_files(tools_dir):
    """Ensure CreamAPI files are downloaded and ready."""
    tools_path = Path(tools_dir)
    extract_path = tools_path / "creamapi"
    
    # Check if files already exist
    if extract_path.exists():
        # Check if DLLs are in the root
        if (extract_path / "steam_api64.dll").exists() or (extract_path / "steam_api.dll").exists():
            return extract_path
        
        # Check if DLLs are in subdirectories
        for root, dirs, files in os.walk(extract_path):
            if "steam_api64.dll" in files or "steam_api.dll" in files:
                # Found DLLs in a subdirectory, copy them to root for easier access
                for dll_name in ["steam_api.dll", "steam_api64.dll"]:
                    dll_path = Path(root) / dll_name
                    if dll_path.exists() and dll_path.parent != extract_path:
                        target = extract_path / dll_name
                        if not target.exists():
                            shutil.copy2(dll_path, target)
                return extract_path
    
    # Try to download from auto-creamapi-2 repository
    extract_path.mkdir(parents=True, exist_ok=True)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Get latest release info
        response = requests.get(CREAMAPI_REPO_URL, timeout=30, headers=headers)
        response.raise_for_status()
        release_data = response.json()
        
        # Look for DLL files in release assets
        dll_assets = {}
        for asset in release_data.get('assets', []):
            asset_name = asset['name'].lower()
            if 'steam_api.dll' in asset_name and not '64' in asset_name:
                dll_assets['steam_api.dll'] = asset['browser_download_url']
            elif 'steam_api64.dll' in asset_name:
                dll_assets['steam_api64.dll'] = asset['browser_download_url']
            elif asset_name.endswith('.zip'):
                # Try downloading zip and extracting DLLs
                zip_url = asset['browser_download_url']
                zip_response = requests.get(zip_url, timeout=60, headers=headers)
                zip_response.raise_for_status()
                
                with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
                    z.extractall(extract_path)
                
                # Look for DLLs in extracted files
                for root, dirs, files in os.walk(extract_path):
                    for dll_name in ["steam_api.dll", "steam_api64.dll"]:
                        dll_path = Path(root) / dll_name
                        if dll_path.exists() and dll_path.parent != extract_path:
                            target = extract_path / dll_name
                            if not target.exists():
                                shutil.copy2(dll_path, target)
                
                # Check if we found DLLs
                if (extract_path / "steam_api64.dll").exists() or (extract_path / "steam_api.dll").exists():
                    return extract_path
        
        # Download individual DLL files if found
        for dll_name, dll_url in dll_assets.items():
            dll_response = requests.get(dll_url, timeout=60, headers=headers)
            dll_response.raise_for_status()
            
            dll_path = extract_path / dll_name
            with open(dll_path, 'wb') as f:
                f.write(dll_response.content)
        
        # Check if we got any DLLs
        if (extract_path / "steam_api64.dll").exists() or (extract_path / "steam_api.dll").exists():
            return extract_path
        
        return None
    except Exception as e:
        print(f"[ERROR] Failed to download CreamAPI: {e}")
        return None

def patch_game_creamapi(game_dir, app_id, tools_dir, dlc_ids=None):
    """Apply CreamAPI patch to a game directory."""
    creamapi_path = ensure_creamapi_files(tools_dir)
    if not creamapi_path:
        return False, ("CreamAPI files not found. The automatic download failed.\n\n"
                      f"Please manually place the DLLs in: {Path(tools_dir) / 'creamapi'}\n\n"
                      "Required files: steam_api.dll and/or steam_api64.dll\n\n"
                      "You can find CreamAPI from:\n"
                      "- auto-creamapi-2 repository: https://github.com/Warwolfer/auto-creamapi-2\n"
                      "- Community forums or creamapi.org")
    
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
    
    # Find all occurrences of steam_api(64).dll recursively
    for root, dirs, files in os.walk(game_path):
        for filename in files:
            if filename in mapping:
                target_file = Path(root) / filename
                creamapi_src = creamapi_path / mapping[filename]
                
                if creamapi_src.exists():
                    # Backup original
                    bak_file = target_file.with_suffix(".dll.bak")
                    if not bak_file.exists():
                        shutil.copy2(target_file, bak_file)
                        log.append(f"Backed up {filename} to .bak")
                    
                    # Copy CreamAPI DLL
                    shutil.copy2(creamapi_src, target_file)
                    log.append(f"Replaced {filename} with CreamAPI version")
                    
                    # Create cream_api.ini in the same folder
                    ini_file = Path(root) / "cream_api.ini"
                    with open(ini_file, "w", encoding="utf-8") as f:
                        f.write("[steam]\n")
                        f.write(f"appid = {app_id}\n\n")
                        f.write("[dlc]\n")
                        if dlc_ids:
                            for dlc_id in dlc_ids:
                                if dlc_id.strip():
                                    f.write(f"{dlc_id.strip()} = true\n")
                        else:
                            f.write("; Add DLC IDs here, one per line\n")
                            f.write("; Example: 123456 = true\n")
                    log.append(f"Created cream_api.ini ({app_id})")
                    if dlc_ids:
                        log.append(f"Configured {len([d for d in dlc_ids if d.strip()])} DLC(s)")
                    
                    found_any = True
    
    if not found_any:
        return False, "No Steam API DLLs found in game directory."
    
    return True, "\n".join(log)

def revert_creamapi_patch(game_dir):
    """Restore original Steam DLLs and remove CreamAPI files."""
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
                    
        # 2. Remove cream_api.ini if it exists
        ini_file = Path(root) / "cream_api.ini"
        if ini_file.exists():
            try:
                os.remove(ini_file)
                log.append("Removed cream_api.ini")
            except: pass
            
    if not found_bak:
        return False, "No backup (.bak) files found. Revert may not be possible."
        
    return True, "\n".join(log)

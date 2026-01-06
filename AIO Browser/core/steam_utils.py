# core/steam_utils.py
import winreg
import os
import re
from pathlib import Path

def get_steam_path():
    """Locate Steam installation path from Registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        path, _ = winreg.QueryValueEx(key, "InstallPath")
        return Path(path)
    except:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            return Path(path)
        except:
            return None

def parse_vdf(content):
    """Extremely basic VDF parser for ACF/Library files."""
    items = re.findall(r'"(.*?)"\s*"(.*?)"', content)
    return dict(items)

def get_steam_libraries():
    """Find all Steam library folders."""
    steam_path = get_steam_path()
    if not steam_path:
        return []
    
    libraries = [steam_path]
    lib_vdf = steam_path / "steamapps" / "libraryfolders.vdf"
    
    if lib_vdf.exists():
        with open(lib_vdf, "r", encoding="utf-8") as f:
            content = f.read()
            # Find all "path" values
            paths = re.findall(r'"path"\s*"(.*?)"', content)
            for p in paths:
                p_path = Path(p.replace("\\\\", "\\"))
                if p_path not in libraries:
                    libraries.append(p_path)
    
    return libraries

def get_installed_games():
    """Scan libraries for installed games."""
    libraries = get_steam_libraries()
    games = []
    
    for lib in libraries:
        apps_path = lib / "steamapps"
        if not apps_path.exists():
            continue
            
        for acf in apps_path.glob("appmanifest_*.acf"):
            try:
                with open(acf, "r", encoding="utf-8") as f:
                    content = f.read()
                    data = parse_vdf(content)
                    
                    if "name" in data and "installdir" in data:
                        games.append({
                            "id": data.get("appid", acf.stem.split("_")[1]),
                            "name": data["name"],
                            "install_dir": data["installdir"],
                            "full_path": apps_path / "common" / data["installdir"],
                            "source": "Steam"
                        })
            except:
                continue
                
    return sorted(games, key=lambda x: x["name"])

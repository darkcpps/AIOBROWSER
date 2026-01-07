# core/steam_utils.py
import winreg
import os
import re
from pathlib import Path

def get_steam_path():
    """Locate Steam installation path from Registry, process list, or default locations."""
    # 1. Registry Lookup (Thorough)
    for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
        for subkey in [r"SOFTWARE\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"]:
            try:
                key = winreg.OpenKey(root, subkey)
                path, _ = winreg.QueryValueEx(key, "InstallPath")
                winreg.CloseKey(key)
                if path and Path(path).exists():
                    return Path(path)
            except:
                continue

    # 2. Process Lookup (If Steam is running)
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'exe']):
            if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
                p = Path(proc.info['exe']).parent
                if p.exists():
                    return p
    except:
        pass

    # 3. Common Default Paths
    defaults = [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        Path.home() / "AppData" / "Local" / "Steam"
    ]
    for d in defaults:
        p = Path(d)
        if p.exists() and (p / "steam.exe").exists():
            return p

    return None

def parse_vdf(content):
    """Extremely basic VDF parser for ACF/Library files. Returns lowercase keys."""
    # Handle both tabs and spaces
    items = re.findall(r'"(.*?)"\s+"(.*?)"', content)
    if not items:
        # Fallback for some VDF variants
        items = re.findall(r'"(.*?)"\s*"(.*?)"', content)
    
    return {k.lower(): v for k, v in items}

def get_steam_libraries():
    """Find all Steam library folders."""
    steam_path = get_steam_path()
    if not steam_path:
        return []
    
    libraries = [steam_path]
    lib_vdf = steam_path / "steamapps" / "libraryfolders.vdf"
    
    if lib_vdf.exists():
        try:
            with open(lib_vdf, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Find all "path" values (case insensitive search)
                paths = re.findall(r'"path"\s+"(.*?)"', content, re.IGNORECASE)
                if not paths:
                    paths = re.findall(r'"path"\s*"(.*?)"', content, re.IGNORECASE)
                
                for p in paths:
                    p_path = Path(p.replace("\\\\", "\\"))
                    if p_path.exists() and p_path not in libraries:
                        libraries.append(p_path)
        except Exception as e:
            print(f"[ERROR] Failed to parse libraryfolders.vdf: {e}")
    
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
                # Use errors="ignore" to handle potential encoding issues in user names or dirs
                with open(acf, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    data = parse_vdf(content)
                    
                    if "name" in data and "installdir" in data:
                        full_path = apps_path / "common" / data["installdir"]
                        
                        # Only include if the game folder actually exists
                        if full_path.exists():
                            games.append({
                                "id": data.get("appid", acf.stem.split("_")[1]),
                                "name": data["name"],
                                "install_dir": data["installdir"],
                                "full_path": full_path,
                                "source": "Steam"
                            })
            except Exception as e:
                print(f"[DEBUG] Failed to parse ACF {acf.name}: {e}")
                continue
                
    return sorted(games, key=lambda x: x["name"])

def search_steam_games(query):
    """Search Steam storefront for games."""
    import requests
    from bs4 import BeautifulSoup
    
    params = {"term": query, "count": 25, "start": 0, "category1": 998} # category1=998 is games
    try:
        url = "https://store.steampowered.com/search/results"
        response = requests.get(url, params=params, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        for row in soup.select("a.search_result_row"):
            appid = row.get("data-ds-appid")
            name = row.select_one("span.title").get_text()
            img = row.select_one("div.search_capsule img").get("src")
            
            # Use small capsules
            img = img.replace("capsule_617x353", "capsule_sm_120")
            
            if appid:
                results.append({
                    "id": appid,
                    "name": name,
                    "image": img,
                    "type": "Game"
                })
        return results
    except Exception as e:
        print(f"[ERROR] Global Steam Search failed: {e}")
        return []

def fetch_dlcs(app_id):
    """
    Fetch DLC list for a given AppID with Steam Storefront and SteamDB fallback.
    """
    import requests
    import json
    import re
    
    print(f"[FETCH] Fetching DLCs for AppID: {app_id}...")
    dlcs = []
    
    # 1. Try Steam Storefront API (Official)
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if str(app_id) in data and data[str(app_id)].get("success"):
            app_data = data[str(app_id)]["data"]
            dlc_ids = app_data.get("dlc", [])
            
            if dlc_ids:
                print(f"[FETCH] Storefront found {len(dlc_ids)} DLC IDs. Resolving names...")
                # Bulk resolve names for IDs
                # Steam allows up to ~100 IDs in one request
                chunk_size = 50
                for i in range(0, len(dlc_ids), chunk_size):
                    chunk = dlc_ids[i:i + chunk_size]
                    resolve_url = f"https://store.steampowered.com/api/appdetails?appids={','.join(map(str, chunk))}&filters=basic"
                    r_resp = requests.get(resolve_url, timeout=10).json()
                    
                    for d_id in chunk:
                        sid = str(d_id)
                        if sid in r_resp and r_resp[sid].get("success"):
                            d_name = r_resp[sid]["data"].get("name", f"DLC {sid}")
                            dlcs.append({"id": sid, "name": d_name})
                        else:
                            dlcs.append({"id": sid, "name": f"DLC {sid}"})
    except Exception as e:
        print(f"[ERROR] Storefront API failed: {e}")

    # 2. Try SteamDB via Wayback Machine for hidden/delisted DLCs
    if not dlcs or len(dlcs) < 5: 
        try:
            steam_db_url = f"https://steamdb.info/app/{app_id}/dlc/"
            wayback_api = f"https://archive.org/wayback/available?url={steam_db_url}"
            wb_resp = requests.get(wayback_api, timeout=10).json()
            
            if "archived_snapshots" in wb_resp and "closest" in wb_resp["archived_snapshots"]:
                raw_url = wb_resp["archived_snapshots"]["closest"]["url"].replace("/http", "id_/http")
                print(f"[FETCH] Downloading SteamDB snapshot: {raw_url}")
                content = requests.get(raw_url, timeout=15).text
                
                # More robust regex for SteamDB AppID rows
                # Looking for: <tr class="app" data-appid="XXXX"> ... <td>Name</td>
                matches = re.finditer(r'<tr\s+class="app"\s+data-appid="(\d+)".*?<td>(.*?)</td>', content, re.DOTALL)
                found_count = 0
                for m in matches:
                    d_id = m.group(1)
                    d_name = re.sub('<[^<]+?>', '', m.group(2)).strip()
                    if d_name.isdigit(): continue # Skip cases where name is just the ID
                    
                    if not any(d['id'] == d_id for d in dlcs):
                        dlcs.append({"id": d_id, "name": d_name})
                        found_count += 1
                print(f"[FETCH] SteamDB Fallback added {found_count} new DLCs.")
        except Exception as e:
            print(f"[ERROR] SteamDB Fallback failed: {e}")

    # Sort and clean
    seen = set()
    final_dlcs = []
    for d in dlcs:
        if d["id"] not in seen:
            # Fallback if name is just the ID or empty
            if not d["name"] or d["name"].strip() == d["id"] or d["name"].isdigit():
                d["name"] = f"Unresolved DLC ({d['id']})"
            
            # Clean up names like "The Binding of Isaac: Rebirth - Repentance" -> "Repentance" 
            # if the parent name is present (optional, but nice)
            
            final_dlcs.append(d)
            seen.add(d["id"])

    # Sort numerically by ID or alphabetically by name? Alphabetical is usually better for users.
    return sorted(final_dlcs, key=lambda x: x["name"])

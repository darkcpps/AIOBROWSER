# greenluma_patcher.py
import os
import shutil
import subprocess
from pathlib import Path
import winreg

def get_steam_path():
    """Locate the Steam installation path via Registry."""
    print("[DEBUG] Searching for Steam path in Registry...")
    try:
        # Check both HKCU and HKLM for InstallPath
        for hkey in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
            for subkey in [r"Software\Valve\Steam", r"Software\WOW6432Node\Valve\Steam"]:
                try:
                    key = winreg.OpenKey(hkey, subkey)
                    steam_path, _ = winreg.QueryValueEx(key, "InstallPath" if "Steam" in subkey else "InstallPath")
                    print(f"[DEBUG] Found Steam path: {steam_path}")
                    return Path(steam_path)
                except: continue
        
        # Fallback for common locations if registry fails
        common_paths = [Path("C:/Program Files (x86)/Steam"), Path("C:/Program Files/Steam")]
        for p in common_paths:
            if p.exists():
                print(f"[DEBUG] Registry failed, but found Steam at fallback: {p}")
                return p
                
        return None
    except Exception as e:
        print(f"[ERROR] Could not find Steam path: {e}")
        return None

def auto_setup_greenluma(tools_dir):
    """
    Automate everything: 
    Copies GL files to Steam directory if they aren't there yet.
    """
    steam_path = get_steam_path()
    if not steam_path:
        return False, "Steam not found. Please install Steam first."

    src_gl = Path(tools_dir) / "Greenluma" / "NormalMode"
    if not src_gl.exists():
        return False, f"GreenLuma source files missing from {src_gl}"

    # Required files for GreenLuma to work
    files_to_copy = ["DLLInjector.exe", "GreenLuma_2024_x64.dll", "GreenLuma_2024_x86.dll"]
    
    # Actually, GreenLuma 2025 might have different names, let's copy everything in NormalMode
    print(f"[PROCESS] Syncing GreenLuma files to Steam folder: {steam_path}")
    for item in src_gl.iterdir():
        if item.name == "AppList": continue # We manage this separately
        
        dest = steam_path / item.name
        try:
            if item.is_file():
                # Only copy if different or doesn't exist
                if not dest.exists() or os.path.getmtime(item) > os.path.getmtime(dest):
                    shutil.copy2(item, dest)
            elif item.is_dir():
                # Copy directory if it doesn't exist or is outdated
                if dest.exists():
                    # Instead of full copytree, just copy missing files inside
                    for subitem in item.rglob("*"):
                        if subitem.is_file():
                            rel_path = subitem.relative_to(item)
                            sub_dest = dest / rel_path
                            sub_dest.parent.mkdir(parents=True, exist_ok=True)
                            if not sub_dest.exists() or os.path.getmtime(subitem) > os.path.getmtime(sub_dest):
                                shutil.copy2(subitem, sub_dest)
                else:
                    shutil.copytree(item, dest)
        except Exception as e:
            print(f"[ERROR] Could not sync {item.name}: {e}")

    # Ensure AppList exists in Steam folder
    app_list_dir = steam_path / "AppList"
    app_list_dir.mkdir(parents=True, exist_ok=True)
    
    return True, steam_path

def patch_with_greenluma(app_id, dlc_ids, tools_dir, stealth_mode=True):
    """
    Setup GreenLuma directly in the Steam folder.
    """
    success, result = auto_setup_greenluma(tools_dir)
    if not success:
        return False, result
    
    steam_path = result
    
    # Update the INI file based on manager logic
    update_injector_ini(steam_path, stealth_mode)
    
    app_list_dir = steam_path / "AppList"
    
    print(f"[PROCESS] Managing AppList at: {app_list_dir}")

    # Collect all IDs
    all_ids = []
    
    # Handle the input list (which might contain 'ID = Name')
    if dlc_ids:
        for d in dlc_ids:
            clean_id = str(d).split('=')[0].strip()
            if clean_id and clean_id.isdigit():
                all_ids.append(clean_id)
    
    # If app_id wasn't in the list, add it
    str_app_id = str(app_id)
    if str_app_id not in all_ids:
        all_ids.insert(0, str_app_id)

    # Clear existing .txt files
    print("[PROCESS] Clearing old AppList profiles...")
    for f in app_list_dir.glob("*.txt"):
        try: f.unlink()
        except: pass

    # Write new IDs: 0.txt, 1.txt, ...
    print(f"[PROCESS] Writing {len(all_ids)} AppIDs to Steam/AppList...")
    for i, aid in enumerate(all_ids):
        with open(app_list_dir / f"{i}.txt", "w") as f:
            f.write(aid)

    log = [
        f"✅ SUCCESS: GreenLuma is now integrated with Steam.",
        f"📂 AppList Location: {app_list_dir}",
        f"🎮 Total IDs Active: {len(all_ids)}",
        f"🛡️ Mode: {'Stealth (NoHook)' if stealth_mode else 'Standard (Hook)'}",
        "",
        "🚀 NEXT STEPS:",
        "1. Close Steam completely.",
        f"2. Run 'DLLInjector.exe' located in your Steam folder.",
        "   (You can use the 'Launch Injector' button in the browser!)"
    ]

    return True, "\n".join(log)

def update_injector_ini(steam_path, stealth_mode=True):
    """
    Logic borrowed and improved from GreenLuma 2024 Manager.
    Configures DLLInjector.ini for the specific Steam installation.
    """
    ini_path = steam_path / "DLLInjector.ini"
    
    # 1. Detect the DLL (usually x86 for Steam)
    gl_dll = "GreenLuma_2025_x86.dll"
    for f in steam_path.glob("GreenLuma_*_x86.dll"):
        gl_dll = f.name
        break
    
    # 2. Prepare the INI content matching the 2025 format
    # The injector is VERY picky about section headers [DllInjector] and key names.
    config_lines = [
        "[DllInjector]",
        f"AllowMultipleInstancesOfDLLInjector = 0",
        f"UseFullPathsFromIni = 0",
        "",
        "# Exe to start",
        f"Exe = Steam.exe",
        f"CommandLine ={' ' if stealth_mode else ' -inhibitbootstrap'}",
        "",
        "# Dll to inject",
        f"Dll = {gl_dll}",
        "",
        "# Wait for started exe to close before exiting the DllInjector process.",
        f"WaitForProcessTermination = {'0' if stealth_mode else '1'}",
        "",
        "# Set a fake parent process",
        f"EnableFakeParentProcess = {'1' if stealth_mode else '0'}",
        f"FakeParentProcess = explorer.exe",
        "",
        "# Enable security mitigations on child process.",
        f"EnableMitigationsOnChildProcess = 0",
        "",
        "DEP = 1",
        "SEHOP = 1",
        "HeapTerminate = 1",
        "ForceRelocateImages = 1",
        "BottomUpASLR = 1",
        "HighEntropyASLR = 1",
        "RelocationsRequired = 1",
        "StrictHandleChecks = 0",
        "Win32kSystemCallDisable = 0",
        "ExtensionPointDisable = 1",
        "CFG = 1",
        "CFGExportSuppression = 1",
        "StrictCFG = 1",
        "DynamicCodeDisable = 0",
        "DynamicCodeAllowOptOut = 0",
        "BlockNonMicrosoftBinaries = 0",
        "FontDisable = 1",
        "NoRemoteImages = 1",
        "NoLowLabelImages = 1",
        "PreferSystem32 = 0",
        "RestrictIndirectBranchPrediction = 1",
        "SpeculativeStoreBypassDisable = 0",
        "ShadowStack = 0",
        "ContextIPValidation = 0",
        "BlockNonCETEHCONT = 0",
        "BlockFSCTL = 0",
        "",
        "# Number of files to create",
        f"CreateFiles = {'2' if stealth_mode else '0'}",
        "",
        "# Name of the file(s) to create",
        f"FileToCreate_1 = {'NoQuestion.bin' if stealth_mode else ''}",
        f"FileToCreate_2 = {'StealthMode.bin' if stealth_mode else ''}",
        "",
        "Use4GBPatch = 0",
        "FileToPatch_1 = ",
        f"BootImage = GreenLuma2025_Files\\BootImage.bmp",
        "BootImageWidth = 500",
        "BootImageHeight = 500",
        "BootImageXOffest = 240",
        "BootImageYOffest = 280"
    ]
    
    try:
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write("\n".join(config_lines))
        print(f"[DEBUG] DLLInjector.ini updated (Stealth={stealth_mode})")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update INI: {e}")
        return False

def get_current_applist(tools_dir=None):
    """Return list of AppIDs currently in Steam's AppList."""
    steam_path = get_steam_path()
    if not steam_path: return []
    
    app_list_dir = steam_path / "AppList"
    if not app_list_dir.exists(): return []

    ids = []
    # Grab all txt files, sort them numerically
    files = list(app_list_dir.glob("*.txt"))
    files.sort(key=lambda x: int(x.stem) if x.stem.isdigit() else 999)
    
    for f in files:
        try:
            with open(f, "r") as file:
                aid = file.read().strip()
                if aid: ids.append(aid)
        except: pass
    return ids

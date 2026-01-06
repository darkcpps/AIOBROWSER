# core/path_utils.py
import os
import sys
from pathlib import Path

def get_root_dir():
    """Get the root directory of the application, handling PyInstaller packaging."""
    if getattr(sys, "frozen", False):
        # When running as a PyInstaller bundle, use the executable's directory
        # PyInstaller 6+ puts internal files in _internal, but the exe is in the parent.
        return Path(sys.executable).parent
    # When running as a script, use the current project root
    return Path(__file__).parent.parent.absolute()

def get_tools_dir():
    """Get the path to the tools directory."""
    if hasattr(sys, '_MEIPASS'):
        # One-file bundle
        return Path(sys._MEIPASS) / "tools"
        
    root = get_root_dir()
    
    # Check if tools is in root (development or simple bundle)
    tools_in_root = root / "tools"
    if tools_in_root.exists():
        return tools_in_root
        
    # Check if tools is in _internal (PyInstaller bundle)
    tools_in_internal = root / "_internal" / "tools"
    if tools_in_internal.exists():
        return tools_in_internal
        
    return tools_in_root

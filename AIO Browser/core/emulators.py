from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class EmulatorOption:
    id: str
    name: str
    exe_names: tuple[str, ...]
    download_page_url: str
    direct_download_url: Optional[str] = None
    github_repo: Optional[str] = None
    github_asset_patterns: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    common_dir_names: tuple[str, ...] = ()


def _clean_text(value: str) -> str:
    s = (value or "").strip().lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_platform(raw_platform: str) -> Optional[str]:
    s = _clean_text(raw_platform)
    if not s:
        return None

    if "playstation 5" in s or s == "ps5" or " ps5" in f" {s} ":
        return None

    if "wii u" in s or "wiiu" in s:
        return "wiiu"
    if "gamecube" in s or s in {"gc", "ngc"}:
        return "gamecube"
    if "wii" in s:
        return "wii"

    if "nintendo 3ds" in s or s == "3ds":
        return "3ds"
    if "switch" in s or s == "ns" or "nintendo switch" in s:
        return "switch"

    if s in {"nintendo ds", "nds", "ds"} or "nintendo ds" in s:
        return "ds"

    if s in {"nes", "nintendo entertainment system"} or "nes" in s:
        return "nes"
    if s in {"snes", "super nintendo"} or "snes" in s:
        return "snes"

    if s in {"gb", "game boy"} or "game boy" in s:
        return "gb"
    if s in {"gbc", "game boy color"} or "game boy color" in s:
        return "gbc"
    if s in {"gba", "game boy advance"} or "game boy advance" in s:
        return "gba"

    if s in {"ps1", "psx"} or "playstation 1" in s:
        return "ps1"
    if s in {"playstation", "ps"}:
        return "ps1"
    if s in {"ps2"} or "playstation 2" in s:
        return "ps2"
    if s in {"ps3"} or "playstation 3" in s:
        return "ps3"
    if s in {"ps4"} or "playstation 4" in s:
        return "ps4"
    if s in {"psp"} or "playstation portable" in s:
        return "psp"
    if s in {"vita", "ps vita", "playstation vita"} or "vita" in s:
        return "vita"

    if s in {"xbox", "original xbox"}:
        return "xbox"
    if s in {"xbox 360", "x360"} or "xbox 360" in s:
        return "xbox360"

    if "sega saturn" in s or s == "saturn":
        return "saturn"
    if "dreamcast" in s:
        return "dreamcast"
    if "sega cd" in s or "mega cd" in s or s in {"segacd", "megacd"}:
        return "segacd"

    return None


def pick_platform(raw_platforms: Iterable[str] | None, preferred_raw: str | None = None) -> Optional[str]:
    preferred = normalize_platform(preferred_raw or "")
    normalized = [normalize_platform(p) for p in (raw_platforms or [])]
    normalized = [p for p in normalized if p]

    if preferred and preferred in set(normalized):
        return preferred
    if len(normalized) == 1:
        return normalized[0]
    if normalized:
        return normalized[0]
    return preferred


PLATFORM_DISPLAY_NAMES: dict[str, str] = {
    "3ds": "Nintendo 3DS",
    "switch": "Nintendo Switch",
    "wii": "Nintendo Wii",
    "wiiu": "Nintendo Wii U",
    "ds": "Nintendo DS",
    "gamecube": "Nintendo GameCube",
    "nes": "NES",
    "snes": "SNES",
    "gb": "Game Boy",
    "gbc": "Game Boy Color",
    "gba": "Game Boy Advance",
    "ps1": "PlayStation 1",
    "ps2": "PlayStation 2",
    "ps3": "PlayStation 3",
    "ps4": "PlayStation 4",
    "psp": "PSP",
    "vita": "PS Vita",
    "xbox": "Xbox (Original)",
    "xbox360": "Xbox 360",
    "saturn": "Sega Saturn",
    "dreamcast": "Sega Dreamcast",
    "segacd": "Sega CD",
}


EMULATORS: dict[str, EmulatorOption] = {
    "lime3ds": EmulatorOption(
        id="lime3ds",
        name="Lime3DS",
        exe_names=("lime3ds.exe", "lime3ds-qt.exe"),
        download_page_url="https://archive.org/download/lime3ds-emulator/lime3ds-2118.2-windows-msvc.zip",
        direct_download_url="https://archive.org/download/lime3ds-emulator/lime3ds-2118.2-windows-msvc.zip",
        notes=("Recommended newer Citra fork (archived build).",),
        common_dir_names=("Lime3DS",),
    ),
    "citra": EmulatorOption(
        id="citra",
        name="Citra",
        exe_names=("citra-qt.exe", "citra.exe"),
        download_page_url="https://archive.org/download/citra-nightly-2104_20240304/citra-windows-msvc-20240304-0ff3440.zip",
        direct_download_url="https://archive.org/download/citra-nightly-2104_20240304/citra-windows-msvc-20240304-0ff3440.zip",
        notes=("Legacy (archived build). Many users prefer Lime3DS now.",),
        common_dir_names=("Citra",),
    ),
    "ryujinx": EmulatorOption(
        id="ryujinx",
        name="Ryujinx",
        exe_names=("Ryujinx.exe",),
        download_page_url="https://git.ryujinx.app/api/v4/projects/1/packages/generic/Ryubing/1.3.3/ryujinx-1.3.3-win_x64.zip",
        direct_download_url="https://git.ryujinx.app/api/v4/projects/1/packages/generic/Ryubing/1.3.3/ryujinx-1.3.3-win_x64.zip",
        common_dir_names=("Ryujinx",),
    ),
    "dolphin": EmulatorOption(
        id="dolphin",
        name="Dolphin",
        exe_names=("Dolphin.exe",),
        download_page_url="https://dl.dolphin-emu.org/builds/64/56/dolphin-master-2512-120-x64.7z",
        direct_download_url="https://dl.dolphin-emu.org/builds/64/56/dolphin-master-2512-120-x64.7z",
        common_dir_names=("Dolphin Emulator", "Dolphin"),
    ),
    "cemu": EmulatorOption(
        id="cemu",
        name="Cemu",
        exe_names=("Cemu.exe",),
        download_page_url="https://github.com/cemu-project/Cemu/releases/download/v2.6/cemu-2.6-windows-x64.zip",
        direct_download_url="https://github.com/cemu-project/Cemu/releases/download/v2.6/cemu-2.6-windows-x64.zip",
        common_dir_names=("Cemu",),
    ),
    "melonds": EmulatorOption(
        id="melonds",
        name="melonDS",
        exe_names=("melonDS.exe",),
        download_page_url="https://melonds.kuribo64.net/downloads/melonDS-1.1-windows-x86_64.zip",
        direct_download_url="https://melonds.kuribo64.net/downloads/melonDS-1.1-windows-x86_64.zip",
        common_dir_names=("melonDS",),
    ),
    "retroarch": EmulatorOption(
        id="retroarch",
        name="RetroArch",
        exe_names=("retroarch.exe",),
        download_page_url="https://buildbot.libretro.com/nightly/windows/x86_64/RetroArch.7z",
        direct_download_url="https://buildbot.libretro.com/nightly/windows/x86_64/RetroArch.7z",
        common_dir_names=("RetroArch",),
    ),
    "mgba": EmulatorOption(
        id="mgba",
        name="mGBA",
        exe_names=("mgba.exe", "mGBA.exe"),
        download_page_url="https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-win64.7z",
        direct_download_url="https://github.com/mgba-emu/mgba/releases/download/0.10.5/mGBA-0.10.5-win64.7z",
        common_dir_names=("mGBA", "mgba"),
    ),
    "duckstation": EmulatorOption(
        id="duckstation",
        name="DuckStation",
        exe_names=("duckstation-qt-x64-ReleaseLTO.exe", "duckstation-qt-x64-Release.exe", "duckstation-qt.exe"),
        download_page_url="https://github.com/stenzek/duckstation/releases/download/latest/duckstation-windows-x64-release.zip",
        direct_download_url="https://github.com/stenzek/duckstation/releases/download/latest/duckstation-windows-x64-release.zip",
        common_dir_names=("DuckStation",),
    ),
    "pcsx2": EmulatorOption(
        id="pcsx2",
        name="PCSX2",
        exe_names=("pcsx2-qt.exe", "pcsx2-qtx64.exe", "pcsx2.exe"),
        download_page_url="https://github.com/PCSX2/pcsx2/releases/download/v2.7.10/pcsx2-v2.7.10-windows-x64-Qt.7z",
        direct_download_url="https://github.com/PCSX2/pcsx2/releases/download/v2.7.10/pcsx2-v2.7.10-windows-x64-Qt.7z",
        common_dir_names=("PCSX2",),
    ),
    "rpcs3": EmulatorOption(
        id="rpcs3",
        name="RPCS3",
        exe_names=("rpcs3.exe", "RPCS3.exe"),
        download_page_url="https://rpcs3.net/latest-build?download=win",
        direct_download_url="https://rpcs3.net/latest-build?download=win",
        common_dir_names=("RPCS3",),
    ),
    "shadps4": EmulatorOption(
        id="shadps4",
        name="ShadPS4",
        exe_names=("shadps4.exe", "ShadPS4.exe"),
        download_page_url="https://sourceforge.net/projects/shadps4.mirror/files/v.0.12.0/shadps4-win64-qt-0.12.0.zip/download",
        direct_download_url="https://sourceforge.net/projects/shadps4.mirror/files/v.0.12.0/shadps4-win64-qt-0.12.0.zip/download",
        notes=("Windows build is via mirror; official site notes Windows releases are unavailable.",),
        common_dir_names=("shadPS4", "ShadPS4"),
    ),
    "ppsspp": EmulatorOption(
        id="ppsspp",
        name="PPSSPP",
        exe_names=("PPSSPPWindows64.exe", "ppssppwindows64.exe", "PPSSPPWindows.exe", "ppsspp.exe"),
        download_page_url="https://github.com/hrydgard/ppsspp/releases/download/v1.19.1/ppsspp_win.zip",
        direct_download_url="https://github.com/hrydgard/ppsspp/releases/download/v1.19.1/ppsspp_win.zip",
        common_dir_names=("PPSSPP",),
    ),
    "vita3k": EmulatorOption(
        id="vita3k",
        name="Vita3K",
        exe_names=("Vita3K.exe", "vita3k.exe"),
        download_page_url="https://sourceforge.net/projects/vita3k.mirror/files/continuous/windows-latest.zip/download",
        direct_download_url="https://sourceforge.net/projects/vita3k.mirror/files/continuous/windows-latest.zip/download",
        common_dir_names=("Vita3K",),
    ),
    "xemu": EmulatorOption(
        id="xemu",
        name="Xemu",
        exe_names=("xemu.exe",),
        download_page_url="https://github.com/xemu-project/xemu/releases/latest/download/xemu-win-x86_64-release.zip",
        direct_download_url="https://github.com/xemu-project/xemu/releases/latest/download/xemu-win-x86_64-release.zip",
        common_dir_names=("xemu", "Xemu"),
    ),
    "xenia": EmulatorOption(
        id="xenia",
        name="Xenia",
        exe_names=("xenia.exe",),
        download_page_url="https://github.com/xenia-project/release-builds-windows/releases/latest/download/xenia_master.zip",
        direct_download_url="https://github.com/xenia-project/release-builds-windows/releases/latest/download/xenia_master.zip",
        common_dir_names=("Xenia",),
    ),
    "xenia_canary": EmulatorOption(
        id="xenia_canary",
        name="Xenia (Canary)",
        exe_names=("xenia_canary.exe",),
        download_page_url="https://github.com/xenia-canary/xenia-canary/releases/latest/download/xenia_canary.zip",
        direct_download_url="https://github.com/xenia-canary/xenia-canary/releases/latest/download/xenia_canary.zip",
        common_dir_names=("Xenia", "Xenia Canary"),
    ),
    "flycast": EmulatorOption(
        id="flycast",
        name="Flycast",
        exe_names=("flycast.exe", "Flycast.exe"),
        download_page_url="https://github.com/flyinghead/flycast/releases/download/v2.5/flycast-win64-2.5.zip",
        direct_download_url="https://github.com/flyinghead/flycast/releases/download/v2.5/flycast-win64-2.5.zip",
        common_dir_names=("Flycast",),
    ),
    "mednafen": EmulatorOption(
        id="mednafen",
        name="Mednafen (Saturn)",
        exe_names=("mednafen.exe",),
        download_page_url="https://mednafen.github.io/releases/files/mednafen-1.32.1-win64.zip",
        direct_download_url="https://mednafen.github.io/releases/files/mednafen-1.32.1-win64.zip",
        common_dir_names=("Mednafen",),
    ),
}


PLATFORM_TO_EMULATORS: dict[str, tuple[str, ...]] = {
    "3ds": ("lime3ds", "citra"),
    "switch": ("ryujinx",),
    "wii": ("dolphin",),
    "wiiu": ("cemu",),
    "ds": ("melonds",),
    "gamecube": ("dolphin",),
    "nes": ("retroarch",),
    "snes": ("retroarch",),
    "gb": ("mgba",),
    "gbc": ("mgba",),
    "gba": ("mgba",),
    "ps1": ("duckstation",),
    "ps2": ("pcsx2",),
    "ps3": ("rpcs3",),
    "ps4": ("shadps4",),
    "psp": ("ppsspp",),
    "vita": ("vita3k",),
    "xbox": ("xemu",),
    "xbox360": ("xenia", "xenia_canary"),
    "saturn": ("retroarch", "mednafen"),
    "dreamcast": ("flycast",),
    "segacd": ("retroarch",),
}


PLATFORM_NOTES: dict[str, tuple[str, ...]] = {
    "nes": ("Recommended cores: Mesen (NES).",),
    "snes": ("Recommended cores: bsnes or Snes9x (SNES).",),
    "saturn": ("Recommended core: Beetle Saturn (RetroArch) or use Mednafen Saturn.",),
    "segacd": ("Recommended core: Genesis Plus GX (RetroArch).",),
}


def get_emulator_options_for_platform(platform_key: str) -> list[EmulatorOption]:
    ids = PLATFORM_TO_EMULATORS.get(platform_key) or ()
    return [EMULATORS[i] for i in ids if i in EMULATORS]


def get_platform_display_name(platform_key: str) -> str:
    return PLATFORM_DISPLAY_NAMES.get(platform_key, platform_key.upper())


def get_platform_notes(platform_key: str) -> tuple[str, ...]:
    return PLATFORM_NOTES.get(platform_key, ())


def find_emulator_executable(option: EmulatorOption, emulator_paths: dict | None = None) -> Optional[Path]:
    emulator_paths = emulator_paths or {}
    configured = emulator_paths.get(option.id)
    if configured:
        try:
            p = Path(configured)
            if p.exists() and p.is_file():
                return p
        except Exception:
            pass

    for exe in option.exe_names:
        found = shutil.which(exe)
        if found:
            try:
                p = Path(found)
                if p.exists():
                    return p
            except Exception:
                pass

    roots = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("APPDATA"),
    ]
    roots = [Path(r) for r in roots if r]

    for root in roots:
        for dir_name in option.common_dir_names:
            base = root / dir_name
            for exe in option.exe_names:
                for candidate in (
                    base / exe,
                    base / "bin" / exe,
                    base / "qt" / exe,
                    base / "x64" / exe,
                    base / "windows" / exe,
                    base / "Release" / exe,
                    base / "ReleaseLTO" / exe,
                ):
                    try:
                        if candidate.exists() and candidate.is_file():
                            return candidate
                    except Exception:
                        pass

    return None


def can_auto_download(option: EmulatorOption) -> bool:
    return bool(option.direct_download_url or option.github_repo)


def resolve_direct_download_url(option: EmulatorOption, timeout_s: float = 10.0) -> Optional[str]:
    if option.direct_download_url:
        return option.direct_download_url

    if not option.github_repo:
        return None

    try:
        import requests

        api_url = f"https://api.github.com/repos/{option.github_repo}/releases/latest"
        r = requests.get(
            api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AIOBrowser",
            },
            timeout=timeout_s,
        )
        if r.status_code != 200:
            return None
        data = r.json() or {}
        assets = data.get("assets") or []
        if not isinstance(assets, list):
            return None

        patterns = [re.compile(p, re.IGNORECASE) for p in (option.github_asset_patterns or ())]
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "")
            url = asset.get("browser_download_url")
            if not url:
                continue
            if patterns and any(p.search(name) for p in patterns):
                return url

        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "").lower()
            url = asset.get("browser_download_url")
            if not url:
                continue
            if ("win" in name or "windows" in name) and (name.endswith(".zip") or name.endswith(".7z")):
                return url

    except Exception:
        return None

    return None

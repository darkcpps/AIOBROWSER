"""Tests for the cross-platform emulator detection helpers."""
import os

from core import emulators
from core.emulators import (
    EMULATORS,
    find_emulator_executable,
    normalize_platform,
    pick_platform,
)


def test_candidate_exe_names_includes_linux_binaries(monkeypatch):
    monkeypatch.setattr(emulators.os, "name", "posix")
    names = emulators._candidate_exe_names(EMULATORS["dolphin"])
    assert "dolphin-emu" in names
    assert "Dolphin.exe" in names
    # Linux names should be tried before Windows ones.
    assert names.index("dolphin-emu") < names.index("Dolphin.exe")


def test_candidate_exe_names_windows_only_uses_exe(monkeypatch):
    monkeypatch.setattr(emulators.os, "name", "nt")
    names = emulators._candidate_exe_names(EMULATORS["duckstation"])
    assert "duckstation-qt" not in names
    assert "duckstation-qt-x64-ReleaseLTO.exe" in names


def test_every_emulator_declares_linux_names():
    for option in EMULATORS.values():
        assert option.linux_exe_names, option.id


def test_platform_search_roots_linux(monkeypatch):
    monkeypatch.setattr(emulators.os, "name", "posix")
    monkeypatch.setattr(emulators.sys, "platform", "linux")
    roots = {str(p) for p in emulators._platform_search_roots()}
    assert "/usr/bin" in roots
    assert "/usr/local/bin" in roots


def test_find_emulator_executable_uses_configured_path(tmp_path):
    exe = tmp_path / "myduck"
    exe.write_text("binary")
    found = find_emulator_executable(
        EMULATORS["duckstation"], {"duckstation": str(exe)}
    )
    assert found == exe


def test_find_emulator_executable_returns_none_when_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(emulators.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        emulators, "_platform_search_roots", lambda: [tmp_path / "nothing"]
    )
    assert find_emulator_executable(EMULATORS["retroarch"]) is None


# --- existing platform-normalisation coverage ---------------------------------


def test_normalize_platform_common_consoles():
    assert normalize_platform("PlayStation 2") == "ps2"
    assert normalize_platform("Nintendo Switch") == "switch"
    assert normalize_platform("Game Boy Advance") == "gba"
    assert normalize_platform("Game Boy Color") == "gbc"
    assert normalize_platform("Super Nintendo") == "snes"
    assert normalize_platform("Sega Dreamcast") == "dreamcast"


def test_normalize_platform_distinguishes_substring_families():
    # Regression: "nes" is a substring of "snes" and "game boy" is a substring
    # of "game boy advance"/"game boy color".
    assert normalize_platform("SNES") == "snes"
    assert normalize_platform("NES") == "nes"
    assert normalize_platform("GB") == "gb"


def test_normalize_platform_rejects_unsupported():
    assert normalize_platform("PlayStation 5") is None
    assert normalize_platform("") is None
    assert normalize_platform(None) is None


def test_pick_platform_prefers_requested_platform():
    platforms = ["Nintendo Switch", "PlayStation 4"]
    assert pick_platform(platforms, "PS4") == "ps4"


def test_pick_platform_single_candidate():
    assert pick_platform(["Nintendo Switch"], None) == "switch"


def test_pick_platform_empty_input():
    assert pick_platform([], None) is None


def test_emulator_ids_are_unique():
    ids = [option.id for option in EMULATORS.values()]
    assert len(ids) == len(set(ids))


def test_every_emulator_has_download_target():
    for option in EMULATORS.values():
        assert option.download_page_url
        assert option.direct_download_url or option.github_repo

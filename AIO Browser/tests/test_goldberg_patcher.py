"""Round-trip tests for the cross-platform Goldberg patcher."""
import os

from core import goldberg_patcher


def _make_emu(tools_dir):
    emu = tools_dir / "goldberg_emu"
    emu.mkdir(parents=True)
    (emu / "steam_api.dll").write_bytes(b"EMU32")
    (emu / "steam_api64.dll").write_bytes(b"EMU64")
    return emu


def test_steam_api_files_include_linux():
    assert "libsteam_api.so" in goldberg_patcher.STEAM_API_FILES


def test_patch_and_revert_roundtrip(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    dll = game / "steam_api.dll"
    dll.write_bytes(b"ORIGINAL")

    tools = tmp_path / "tools"
    tools.mkdir()
    _make_emu(tools)

    ok, log = goldberg_patcher.patch_game(
        str(game), "1234", str(tools), nickname="Tester", language="english"
    )
    assert ok, log
    assert dll.read_bytes() == b"EMU32"
    assert (game / "steam_api.dll.bak").read_bytes() == b"ORIGINAL"
    assert (game / "steam_appid.txt").read_text() == "1234"
    assert (game / "settings" / "account_name.txt").read_text() == "Tester"
    assert (game / "settings" / "language.txt").read_text() == "english"

    ok2, log2 = goldberg_patcher.revert_patch(str(game))
    assert ok2, log2
    assert dll.read_bytes() == b"ORIGINAL"
    assert not (game / "steam_api.dll.bak").exists()
    assert not (game / "steam_appid.txt").exists()
    assert not (game / "settings").exists()


def test_patch_without_steam_library_reports_clearly(tmp_path):
    game = tmp_path / "empty"
    game.mkdir()
    tools = tmp_path / "tools"
    tools.mkdir()
    _make_emu(tools)

    ok, message = goldberg_patcher.patch_game(str(game), "1", str(tools))
    assert not ok
    assert "No Steam API library" in message


def test_ensure_goldberg_files_reuses_existing_bundle(tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()
    _make_emu(tools)

    # Must not hit the network because files already exist.
    path = goldberg_patcher.ensure_goldberg_files(str(tools))
    assert path is not None
    assert (path / "steam_api.dll").exists()


def test_backup_path_preserves_extension():
    from pathlib import Path

    assert goldberg_patcher._backup_path(Path("/g/libsteam_api.so")).name == (
        "libsteam_api.so.bak"
    )
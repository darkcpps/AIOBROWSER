"""Tests for core.steam_utils (safe to run on any platform)."""
from pathlib import Path

from core import steam_utils


def test_parse_vdf_returns_lowercase_keys():
    content = '"AppState"\n{\n "appid" "12345"\n "name" "Some Game"\n}'
    data = steam_utils.parse_vdf(content)
    assert data["appid"] == "12345"
    assert data["name"] == "Some Game"


def test_parse_vdf_handles_empty_input():
    assert steam_utils.parse_vdf("") == {}


def test_get_steam_path_does_not_raise():
    # On non-Windows platforms (or when Steam is absent) this must simply
    # return None rather than raising ImportError/AttributeError.
    result = steam_utils.get_steam_path()
    assert result is None or isinstance(result, Path)


def test_module_exposes_public_api():
    assert callable(steam_utils.get_steam_libraries)
    assert callable(steam_utils.get_installed_games)
    assert callable(steam_utils.search_steam_games)
    assert callable(steam_utils.fetch_dlcs)

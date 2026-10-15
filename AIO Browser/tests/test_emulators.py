"""Tests for the pure helpers in core.emulators."""
from core.emulators import EMULATORS, normalize_platform, pick_platform


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

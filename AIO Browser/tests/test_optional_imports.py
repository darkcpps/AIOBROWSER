"""Regression tests: optional dependencies must not break module imports.

Previously ``core.monochrome_downloader`` imported ``mutagen`` and
``core.steam_utils`` imported ``winreg`` unconditionally, so a missing optional
package (or a non-Windows platform) raised ``ImportError`` and took down the
whole application. These tests guard against that regression.
"""


def test_monochrome_downloader_imports_without_mutagen():
    import core.monochrome_downloader as monochrome

    assert hasattr(monochrome, "MonochromeDownloader")
    assert hasattr(monochrome, "MonochromeAPI")
    assert hasattr(monochrome, "MUTAGEN_AVAILABLE")


def test_steam_utils_imports_without_winreg():
    import core.steam_utils as steam_utils

    assert hasattr(steam_utils, "get_steam_path")


def test_optional_feature_modules_import_cleanly():
    # These modules wrap their optional imports (libtorrent / yt-dlp) so they
    # must import even when those packages are absent.
    import core.bittorrent_downloader  # noqa: F401
    import core.youtube_downloader  # noqa: F401

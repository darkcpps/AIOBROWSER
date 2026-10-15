"""Tests for the cross-platform FFmpeg bootstrapper."""
import os
import stat
import zipfile

from tools import ffmpeg_setup


def test_binary_names_match_platform():
    if os.name == "nt":
        assert ffmpeg_setup.ffmpeg_binary_name() == "ffmpeg.exe"
        assert ffmpeg_setup.ffprobe_binary_name() == "ffprobe.exe"
    else:
        assert ffmpeg_setup.ffmpeg_binary_name() == "ffmpeg"
        assert ffmpeg_setup.ffprobe_binary_name() == "ffprobe"


def test_get_ffmpeg_urls_returns_http_url():
    url = ffmpeg_setup.get_ffmpeg_urls()
    assert isinstance(url, str)
    assert url.startswith("http")


def test_is_ffmpeg_installed_returns_bool():
    assert isinstance(ffmpeg_setup.is_ffmpeg_installed(), bool)


def test_extract_binaries_from_zip(tmp_path):
    archive = tmp_path / "ff.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("ffmpeg-6.0/bin/" + ffmpeg_setup.ffmpeg_binary_name(), b"BIN")
        z.writestr("ffmpeg-6.0/bin/" + ffmpeg_setup.ffprobe_binary_name(), b"PROBE")
        z.writestr("ffmpeg-6.0/README.txt", b"ignore me")

    out = tmp_path / "out"
    found = ffmpeg_setup._extract_binaries(archive, out)

    assert ffmpeg_setup.ffmpeg_binary_name() in found
    assert (out / ffmpeg_setup.ffmpeg_binary_name()).read_bytes() == b"BIN"
    assert not (out / "README.txt").exists()
    if os.name != "nt":
        mode = (out / ffmpeg_setup.ffmpeg_binary_name()).stat().st_mode
        assert mode & stat.S_IXUSR
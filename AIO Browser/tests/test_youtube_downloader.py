"""Tests for core.youtube_downloader using a fake yt_dlp module."""
import types

from core import youtube_downloader as yt


def _make_fake_yt_dlp(captured, info=None):
    class FakeYDL:
        def __init__(self, opts):
            captured.update(opts)

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def download(self, urls):
            captured["urls"] = urls

        def extract_info(self, url, download=False):
            return info or {}

    return types.SimpleNamespace(YoutubeDL=FakeYDL)


def test_download_without_ytdlp(monkeypatch, tmp_path):
    monkeypatch.setattr(yt, "yt_dlp", None)
    downloader = yt.YoutubeDownloader()
    result = downloader.download("https://youtu.be/x", str(tmp_path))
    assert result.startswith("ERROR")


def test_download_audio_builds_expected_options(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(yt, "yt_dlp", _make_fake_yt_dlp(captured))

    downloader = yt.YoutubeDownloader(progress_callback=lambda t, p: None)
    result = downloader.download(
        "https://youtu.be/x", str(tmp_path), mode="audio", quality="320kbps"
    )

    assert result == "SUCCESS"
    assert captured["urls"] == ["https://youtu.be/x"]
    assert captured["format"] == "bestaudio/best"
    assert captured["postprocessors"][0]["preferredquality"] == "320"


def test_download_video_builds_resolution_format(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(yt, "yt_dlp", _make_fake_yt_dlp(captured))

    downloader = yt.YoutubeDownloader()
    result = downloader.download(
        "https://youtu.be/x", str(tmp_path), mode="video", quality="1080p"
    )

    assert result == "SUCCESS"
    assert "height<=1080" in captured["format"]
    assert captured["merge_output_format"] == "mp4"


def test_progress_hook_parses_percentage():
    downloader = yt.YoutubeDownloader()
    seen = []
    downloader.progress_callback = lambda text, progress: seen.append(progress)

    downloader._progress_hook(
        {
            "status": "downloading",
            "_percent_str": "50.0%",
            "_speed_str": "1MiB/s",
            "_eta_str": "1s",
            "_downloaded_bytes_str": "5MiB",
            "_total_bytes_str": "10MiB",
        }
    )

    assert seen == [0.5]


def test_progress_hook_raises_when_cancelled():
    downloader = yt.YoutubeDownloader()
    downloader.cancel()
    try:
        downloader._progress_hook({"status": "downloading"})
    except Exception as exc:  # noqa: BLE001 - the hook signals via a plain exception
        assert "DOWNLOAD_STOPPED" in str(exc)
    else:
        raise AssertionError("cancel() should abort the download hook")


def test_get_video_info_returns_metadata(monkeypatch):
    info = {"title": "T", "thumbnail": "u", "duration": 5, "uploader": "U"}
    monkeypatch.setattr(yt, "yt_dlp", _make_fake_yt_dlp({}, info=info))

    result = yt.get_video_info("https://youtu.be/x")

    assert result["title"] == "T"
    assert result["uploader"] == "U"


def test_get_video_info_without_ytdlp(monkeypatch):
    monkeypatch.setattr(yt, "yt_dlp", None)
    assert yt.get_video_info("https://youtu.be/x") is None

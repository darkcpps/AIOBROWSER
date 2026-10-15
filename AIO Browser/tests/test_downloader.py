"""Unit tests for core.downloader.

These tests exercise the pure download logic with a fake ``requests`` response,
so they need neither a network connection nor a Qt installation.
"""
from core import downloader


class FakeResponse:
    """Minimal stand-in for ``requests.Response`` used by ``download_file``."""

    def __init__(self, chunks, headers=None, url="https://example.com/file.zip"):
        self._chunks = list(chunks)
        self.headers = headers or {}
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=65536):
        for chunk in self._chunks:
            yield chunk


def _noop_progress(text, progress):
    pass


# --------------------------------------------------------------------------- #
# Filename helpers
# --------------------------------------------------------------------------- #
def test_extract_filename_from_content_disposition_quoted():
    value = 'attachment; filename="My Game.rar"'
    assert (
        downloader._extract_filename_from_content_disposition(value) == "My Game.rar"
    )


def test_extract_filename_from_content_disposition_utf8():
    value = "attachment; filename*=UTF-8''My%20Game.zip"
    assert (
        downloader._extract_filename_from_content_disposition(value) == "My Game.zip"
    )


def test_extract_filename_from_content_disposition_missing():
    assert downloader._extract_filename_from_content_disposition(None) is None
    assert downloader._extract_filename_from_content_disposition("inline") is None


def test_extract_filename_from_url_basename():
    assert (
        downloader._extract_filename_from_url("https://host/path/setup.exe")
        == "setup.exe"
    )


def test_extract_filename_from_url_query_parameter():
    url = "https://host/get?filename=My%20File.7z"
    assert downloader._extract_filename_from_url(url) == "My File.7z"


def test_extract_filename_from_url_no_file():
    assert downloader._extract_filename_from_url("https://host/") is None
    assert downloader._extract_filename_from_url("") is None


def test_sanitize_filename_replaces_invalid_characters():
    assert downloader._sanitize_filename("bad:name?.zip") == "bad_name_.zip"


def test_sanitize_filename_handles_reserved_names():
    assert downloader._sanitize_filename("CON") == "_CON"
    assert downloader._sanitize_filename("nul.txt") == "_nul.txt"


def test_sanitize_filename_falls_back_when_empty():
    assert downloader._sanitize_filename("...") == "downloaded_file"


def test_sanitize_filename_truncation_preserves_extension():
    name = "a" * 300 + ".zip"
    result = downloader._sanitize_filename(name)
    assert len(result) <= 240
    assert result.endswith(".zip")


# --------------------------------------------------------------------------- #
# download_file
# --------------------------------------------------------------------------- #
def test_download_file_saves_into_directory(tmp_path, monkeypatch):
    response = FakeResponse(
        [b"hello ", b"world"],
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="game.zip"',
            "content-length": "11",
        },
    )
    monkeypatch.setattr(downloader.requests, "get", lambda *a, **k: response)

    updates = []
    result = downloader.download_file(
        "https://example.com/download",
        str(tmp_path),
        lambda text, progress: updates.append((text, progress)),
        {"paused": False, "stopped": False},
    )

    assert result == "SUCCESS"
    saved = tmp_path / "game.zip"
    assert saved.read_bytes() == b"hello world"
    assert updates[-1][1] == 1.0


def test_download_file_accepts_explicit_file_path(tmp_path, monkeypatch):
    response = FakeResponse(
        [b"data"], headers={"Content-Type": "application/octet-stream"}
    )
    monkeypatch.setattr(downloader.requests, "get", lambda *a, **k: response)
    target = tmp_path / "explicit.bin"

    result = downloader.download_file(
        "https://example.com/download",
        str(target),
        _noop_progress,
        {"paused": False, "stopped": False},
    )

    assert result == "SUCCESS"
    assert target.read_bytes() == b"data"


def test_download_file_detects_html_page(tmp_path, monkeypatch):
    response = FakeResponse(
        [b"<html></html>"],
        headers={"Content-Type": "text/html; charset=utf-8"},
    )
    monkeypatch.setattr(downloader.requests, "get", lambda *a, **k: response)

    result = downloader.download_file(
        "https://example.com/page",
        str(tmp_path),
        _noop_progress,
        {"paused": False, "stopped": False},
    )

    assert result == "IS_HTML"


def test_download_file_stopped_removes_partial_file(tmp_path, monkeypatch):
    response = FakeResponse(
        [b"abc"],
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="x.zip"',
            "content-length": "3",
        },
    )
    monkeypatch.setattr(downloader.requests, "get", lambda *a, **k: response)

    result = downloader.download_file(
        "https://example.com/x",
        str(tmp_path),
        _noop_progress,
        {"paused": False, "stopped": True},
    )

    assert result == "STOPPED"
    assert not (tmp_path / "x.zip").exists()


def test_download_file_uses_provided_session(tmp_path, monkeypatch):
    response = FakeResponse(
        [b"chunk"],
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="s.zip"',
            "content-length": "5",
        },
    )
    calls = {}

    class FakeSession:
        def get(self, url, **kwargs):
            calls["url"] = url
            return response

    result = downloader.download_file(
        "https://example.com/s",
        str(tmp_path),
        _noop_progress,
        {"paused": False, "stopped": False},
        session=FakeSession(),
    )

    assert result == "SUCCESS"
    assert calls["url"] == "https://example.com/s"
    assert (tmp_path / "s.zip").read_bytes() == b"chunk"

"""Unit tests for core.bittorrent_downloader using a fake libtorrent module.

``libtorrent`` is an optional dependency, so these tests inject a small stub to
verify the control flow (success, stop, error) without the real library.
"""
import types

import pytest

from core import bittorrent_downloader as bt


class FakeFiles:
    def __init__(self, entries):
        self._entries = entries

    def num_files(self):
        return len(self._entries)

    def file_path(self, index):
        return self._entries[index][0]

    def file_size(self, index):
        return self._entries[index][1]


class FakeInfo:
    def __init__(self, entries):
        self._entries = entries

    def files(self):
        return FakeFiles(self._entries)


class FakeStatus:
    progress = 0.5
    download_rate = 1024
    num_peers = 3
    state = "downloading"


class FakeHandle:
    def __init__(self, seeded=False):
        self._seeded = seeded

    def has_metadata(self):
        return True

    def status(self):
        return FakeStatus()

    def is_seed(self):
        return self._seeded

    def pause(self):
        pass

    def resume(self):
        pass

    def torrent_file(self):
        return FakeInfo([("a.txt", 10)])


class FakeSession:
    delete_files = object()

    def __init__(self, params=None):
        self.params = params or {}

    def add_torrent(self, params):
        return FakeHandle(seeded=True)

    def remove_torrent(self, handle, flags=None):
        pass


def make_fake_lt(entries=(("a.txt", 10), ("b.bin", 20))):
    return types.SimpleNamespace(
        session=FakeSession,
        torrent_info=lambda src: FakeInfo(list(entries)),
        add_magnet_uri=lambda ses, src, params: FakeHandle(seeded=True),
    )


def test_is_available_false_without_libtorrent(monkeypatch):
    monkeypatch.setattr(bt, "lt", None)
    assert bt.is_available() is False


def test_is_available_true_when_libtorrent_present(monkeypatch):
    monkeypatch.setattr(bt, "lt", make_fake_lt())
    assert bt.is_available() is True


def test_download_torrent_without_libtorrent(monkeypatch):
    monkeypatch.setattr(bt, "lt", None)
    messages = []
    result = bt.download_torrent(
        "magnet:?xt=urn:btih:abc", "/tmp", lambda t, p: messages.append(t)
    )
    assert result == "ERROR"
    assert any("libtorrent" in m.lower() for m in messages)


def test_download_torrent_from_file_success(monkeypatch):
    monkeypatch.setattr(bt, "lt", make_fake_lt())
    result = bt.download_torrent(
        "/tmp/fake.torrent",
        "/tmp",
        lambda t, p: None,
        {"paused": False, "stopped": False},
        poll_interval_s=0,
    )
    assert result == "SUCCESS"


def test_download_torrent_from_magnet_success(monkeypatch):
    monkeypatch.setattr(bt, "lt", make_fake_lt())
    result = bt.download_torrent(
        "magnet:?xt=urn:btih:abc",
        "/tmp",
        lambda t, p: None,
        {"paused": False, "stopped": False},
        poll_interval_s=0,
    )
    assert result == "SUCCESS"


def test_download_torrent_stop_returns_stopped(monkeypatch):
    monkeypatch.setattr(bt, "lt", make_fake_lt())
    result = bt.download_torrent(
        "magnet:?xt=urn:btih:abc",
        "/tmp",
        lambda t, p: None,
        {"paused": False, "stopped": True},
        poll_interval_s=0,
    )
    assert result == "STOPPED"


def test_list_torrent_files_from_file(monkeypatch):
    monkeypatch.setattr(bt, "lt", make_fake_lt())
    files = bt.list_torrent_files("/tmp/fake.torrent")
    assert files == [
        {"index": 0, "path": "a.txt", "size": 10},
        {"index": 1, "path": "b.bin", "size": 20},
    ]


def test_list_torrent_files_without_libtorrent(monkeypatch):
    monkeypatch.setattr(bt, "lt", None)
    with pytest.raises(RuntimeError):
        bt.list_torrent_files("/tmp/fake.torrent")

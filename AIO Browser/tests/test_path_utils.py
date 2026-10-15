"""Tests for core.path_utils."""
import os

import pytest

from core import path_utils


def test_get_root_dir_points_at_project_root():
    root = path_utils.get_root_dir()
    assert root.is_dir()
    assert (root / "main_pyqt.py").exists()


def test_get_tools_dir_is_tools_folder():
    tools = path_utils.get_tools_dir()
    assert tools.name == "tools"
    assert tools.is_dir()


@pytest.mark.skipif(hasattr(os, "startfile"), reason="Windows uses os.startfile")
def test_open_path_spawns_platform_opener(monkeypatch):
    calls = []
    monkeypatch.setattr(path_utils.subprocess, "Popen", lambda args: calls.append(args))
    monkeypatch.setattr(path_utils.sys, "platform", "linux")

    assert path_utils.open_path("/tmp/example") is True
    assert calls == [["xdg-open", "/tmp/example"]]


def test_open_path_returns_false_when_opener_fails(monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("no opener available")

    monkeypatch.setattr(path_utils.subprocess, "Popen", boom)
    # Force the "no os.startfile" code path even on Windows.
    monkeypatch.delattr(path_utils.os, "startfile", raising=False)

    assert path_utils.open_path("/tmp/example") is False


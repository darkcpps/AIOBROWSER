"""Tests for core.path_utils."""
from core import path_utils


def test_get_root_dir_points_at_project_root():
    root = path_utils.get_root_dir()
    assert root.is_dir()
    assert (root / "main_pyqt.py").exists()


def test_get_tools_dir_is_tools_folder():
    tools = path_utils.get_tools_dir()
    assert tools.name == "tools"
    assert tools.is_dir()

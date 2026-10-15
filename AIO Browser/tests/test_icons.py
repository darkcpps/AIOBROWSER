"""Tests for the vector icon library.

These require PyQt6 (and a display/offscreen platform). They are skipped
gracefully when PyQt6 cannot be imported, so the core test-suite can still run
in a minimal environment.
"""
import os

import pytest

try:  # PyQt6 may be missing (or lack system libs) in minimal environments.
    from PyQt6.QtWidgets import QApplication  # noqa: F401
except Exception as exc:  # noqa: BLE001 - any import failure means "skip"
    pytest.skip(f"PyQt6 unavailable: {exc}", allow_module_level=True)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from ui.core.icons import available_icons, make_icon  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_expected_icons_are_registered():
    names = available_icons()
    for expected in (
        "gamepad",
        "search",
        "disc",
        "wrench",
        "box",
        "chip",
        "info",
        "tray",
        "gear",
        "check",
        "chevron_down",
        "warning",
        "music",
        "video",
        "trash",
    ):
        assert expected in names


def test_make_icon_renders_for_every_registered_icon(qapp):
    for name in available_icons():
        icon = make_icon(name, "#8B5CF6", 20)
        assert not icon.isNull(), name
        assert not icon.pixmap(20, 20).isNull(), name


def test_make_icon_unknown_name_is_null(qapp):
    assert make_icon("definitely_not_an_icon", "#FFFFFF", 16).isNull()
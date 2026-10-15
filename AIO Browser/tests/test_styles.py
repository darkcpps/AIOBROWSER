"""Tests for stylesheet/palette generation.

Requires PyQt6; skipped when it is unavailable.
"""
import os

import pytest

try:  # PyQt6 may be missing (or lack system libs) in minimal environments.
    from PyQt6.QtGui import QPalette  # noqa: F401
    from PyQt6.QtWidgets import QApplication  # noqa: F401
except Exception as exc:  # noqa: BLE001 - any import failure means "skip"
    pytest.skip(f"PyQt6 unavailable: {exc}", allow_module_level=True)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QPalette  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from ui.core.styles import build_palette, generate_stylesheet  # noqa: E402
from ui.themes import THEMES  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_stylesheet_contains_core_selectors():
    css = generate_stylesheet("default")
    for selector in (
        "QPushButton",
        "QLineEdit",
        "QTabBar::tab",
        "QScrollBar",
        "QCheckBox::indicator",
        "QComboBox",
        "QProgressBar",
        "QToolTip",
    ):
        assert selector in css


def test_stylesheet_generates_for_every_theme():
    for theme_name in THEMES:
        css = generate_stylesheet(theme_name)
        assert len(css) > 1000
        # The accent colour of the theme must actually be used.
        assert THEMES[theme_name]["accent_primary"] in css


def test_stylesheet_does_not_leak_unresolved_placeholders():
    css = generate_stylesheet("default")
    assert "%(" not in css


def test_palette_is_dark_for_every_theme():
    for theme_name in THEMES:
        palette = build_palette(theme_name)
        window = palette.color(QPalette.ColorRole.Window)
        text = palette.color(QPalette.ColorRole.WindowText)
        assert window.lightness() < 80
        assert text.lightness() > 120
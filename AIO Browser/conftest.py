"""Shared pytest configuration for AIO Browser.

The application is normally launched from its project root (the folder that
contains ``main_pyqt.py``) and uses absolute imports such as
``core.downloader`` and ``ui.core.styles``. Adding the project root to
``sys.path`` here lets the test-suite import those modules no matter which
directory pytest is invoked from.
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

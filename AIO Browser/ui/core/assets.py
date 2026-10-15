"""Runtime-generated image assets referenced from the Qt stylesheet.

Qt stylesheets cannot draw a checkmark or a combo-box arrow with plain CSS, so
we render tiny PNGs once (reusing the vector icon code) and reference them by
file path. Everything degrades gracefully: before a QApplication exists - or if
rendering fails - the helpers return "" and the stylesheet simply omits the
image.
"""
import hashlib
import os
import tempfile

_ASSET_DIR = None
_CACHE = {}


def _asset_dir():
    global _ASSET_DIR
    if _ASSET_DIR is None:
        base = os.path.join(tempfile.gettempdir(), "aiobrowser_assets")
        try:
            os.makedirs(base, exist_ok=True)
        except OSError:
            base = tempfile.gettempdir()
        _ASSET_DIR = base
    return _ASSET_DIR


def _css_url(path):
    return "url(%s)" % path.replace("\\", "/")


def icon_url(name, color, size=16):
    """Return a CSS ``url(...)`` for a rendered icon, or "" when unavailable."""
    key = "%s_%s_%s" % (
        name,
        size,
        hashlib.md5(str(color).encode("utf-8")).hexdigest()[:8],
    )
    if key in _CACHE:
        return _CACHE[key]

    url = ""
    try:
        from PyQt6.QtWidgets import QApplication

        # QPixmap requires a live QGuiApplication; bail out harmlessly if the
        # stylesheet is being built before the app exists.
        if QApplication.instance() is not None:
            from ui.core.icons import _pixmap

            pixmap = _pixmap(name, color, size)
            if pixmap is not None and not pixmap.isNull():
                path = os.path.join(_asset_dir(), key + ".png")
                if not os.path.exists(path):
                    pixmap.save(path, "PNG")
                if os.path.exists(path):
                    url = _css_url(path)
    except Exception:
        url = ""

    _CACHE[key] = url
    return url


def clear_cache():
    _CACHE.clear()

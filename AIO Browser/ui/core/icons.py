"""Theme-aware vector icons drawn with QPainter.

Emoji glyphs render inconsistently across platforms and show up as "tofu"
boxes on many Linux systems that do not ship an emoji font. These small vector
icons are drawn programmatically instead, so the UI looks identical everywhere
and recolours to match the active theme.
"""
import math
from functools import lru_cache

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)


def _p(s, x, y):
    """A point in unit coordinates (0..1) scaled to ``s`` pixels."""
    return QPointF(x * s, y * s)


def _poly(s, *coords):
    return QPolygonF([_p(s, x, y) for x, y in coords])


def _fill(painter, color):
    painter.setBrush(QColor(color))


def _nofill(painter):
    painter.setBrush(Qt.BrushStyle.NoBrush)


# --------------------------------------------------------------------------- #
# Individual icon drawings (all operate in a 0..1 x 0..1 box)
# --------------------------------------------------------------------------- #
def _draw_gamepad(painter, s):
    painter.drawRoundedRect(QRectF(0.12 * s, 0.34 * s, 0.76 * s, 0.40 * s), 0.15 * s, 0.15 * s)
    painter.drawLine(_p(s, 0.32, 0.54), _p(s, 0.42, 0.54))
    painter.drawLine(_p(s, 0.37, 0.49), _p(s, 0.37, 0.59))
    _fill(painter, painter.pen().color())
    painter.drawEllipse(_p(s, 0.63, 0.48), 0.035 * s, 0.035 * s)
    painter.drawEllipse(_p(s, 0.71, 0.58), 0.035 * s, 0.035 * s)
    _nofill(painter)


def _draw_search(painter, s):
    painter.drawEllipse(QRectF(0.18 * s, 0.16 * s, 0.46 * s, 0.46 * s))
    painter.drawLine(_p(s, 0.62, 0.60), _p(s, 0.84, 0.84))


def _draw_disc(painter, s):
    painter.drawEllipse(QRectF(0.14 * s, 0.14 * s, 0.72 * s, 0.72 * s))
    painter.drawEllipse(QRectF(0.40 * s, 0.40 * s, 0.20 * s, 0.20 * s))
    painter.drawArc(QRectF(0.24 * s, 0.24 * s, 0.52 * s, 0.52 * s), 40 * 16, 90 * 16)


def _draw_wrench(painter, s):
    painter.drawLine(_p(s, 0.30, 0.74), _p(s, 0.66, 0.36))
    painter.drawEllipse(QRectF(0.56 * s, 0.10 * s, 0.32 * s, 0.32 * s))
    painter.drawLine(_p(s, 0.24, 0.68), _p(s, 0.34, 0.80))


def _draw_box(painter, s):
    painter.drawPolyline(_poly(s, (0.22, 0.36), (0.5, 0.22), (0.78, 0.36),
                                  (0.78, 0.66), (0.5, 0.80), (0.22, 0.66), (0.22, 0.36)))
    painter.drawLine(_p(s, 0.5, 0.22), _p(s, 0.5, 0.5))
    painter.drawLine(_p(s, 0.22, 0.36), _p(s, 0.5, 0.5))
    painter.drawLine(_p(s, 0.78, 0.36), _p(s, 0.5, 0.5))


def _draw_chip(painter, s):
    painter.drawRoundedRect(QRectF(0.28 * s, 0.28 * s, 0.44 * s, 0.44 * s), 0.08 * s, 0.08 * s)
    for f in (0.38, 0.5, 0.62):
        painter.drawLine(_p(s, f, 0.10), _p(s, f, 0.28))
        painter.drawLine(_p(s, f, 0.72), _p(s, f, 0.90))
        painter.drawLine(_p(s, 0.10, f), _p(s, 0.28, f))
        painter.drawLine(_p(s, 0.72, f), _p(s, 0.90, f))


def _draw_info(painter, s):
    painter.drawEllipse(QRectF(0.16 * s, 0.16 * s, 0.68 * s, 0.68 * s))
    painter.drawLine(_p(s, 0.5, 0.46), _p(s, 0.5, 0.72))
    _fill(painter, painter.pen().color())
    painter.drawEllipse(_p(s, 0.5, 0.33), 0.045 * s, 0.045 * s)
    _nofill(painter)


def _draw_tray(painter, s):
    painter.drawLine(_p(s, 0.5, 0.14), _p(s, 0.5, 0.54))
    painter.drawPolyline(_poly(s, (0.34, 0.40), (0.5, 0.56), (0.66, 0.40)))
    painter.drawPolyline(_poly(s, (0.16, 0.62), (0.16, 0.86), (0.84, 0.86), (0.84, 0.62)))


def _draw_gear(painter, s):
    painter.drawEllipse(QRectF(0.35 * s, 0.35 * s, 0.30 * s, 0.30 * s))
    cx = cy = 0.5 * s
    for i in range(8):
        a = math.radians(i * 45)
        painter.drawLine(
            QPointF(cx + math.cos(a) * 0.30 * s, cy + math.sin(a) * 0.30 * s),
            QPointF(cx + math.cos(a) * 0.43 * s, cy + math.sin(a) * 0.43 * s),
        )


def _draw_check(painter, s):
    painter.drawPolyline(_poly(s, (0.20, 0.54), (0.42, 0.76), (0.82, 0.24)))


def _draw_chevron_down(painter, s):
    painter.drawPolyline(_poly(s, (0.24, 0.38), (0.5, 0.64), (0.76, 0.38)))


def _draw_chevron_right(painter, s):
    painter.drawPolyline(_poly(s, (0.38, 0.22), (0.66, 0.5), (0.38, 0.78)))


def _draw_folder(painter, s):
    path = QPainterPath()
    path.moveTo(0.14 * s, 0.78 * s)
    path.lineTo(0.14 * s, 0.24 * s)
    path.lineTo(0.40 * s, 0.24 * s)
    path.lineTo(0.49 * s, 0.37 * s)
    path.lineTo(0.86 * s, 0.37 * s)
    path.lineTo(0.86 * s, 0.78 * s)
    path.closeSubpath()
    painter.drawPath(path)


def _draw_external(painter, s):
    painter.drawPolyline(_poly(s, (0.44, 0.24), (0.80, 0.24), (0.80, 0.60)))
    painter.drawLine(_p(s, 0.80, 0.24), _p(s, 0.46, 0.58))
    painter.drawPolyline(_poly(s, (0.56, 0.38), (0.24, 0.38), (0.24, 0.78), (0.64, 0.78), (0.64, 0.46)))


def _draw_refresh(painter, s):
    painter.drawArc(QRectF(0.18 * s, 0.18 * s, 0.64 * s, 0.64 * s), 60 * 16, 260 * 16)
    painter.drawPolyline(_poly(s, (0.62, 0.14), (0.86, 0.26), (0.70, 0.44)))


def _draw_play(painter, s):
    _fill(painter, painter.pen().color())
    painter.drawPolygon(_poly(s, (0.30, 0.20), (0.82, 0.50), (0.30, 0.80)))
    _nofill(painter)


def _draw_star(painter, s):
    points = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 0.42 if i % 2 == 0 else 0.17
        points.append(QPointF(0.5 * s + math.cos(a) * r * s, 0.5 * s + math.sin(a) * r * s))
    painter.drawPolygon(QPolygonF(points))


def _draw_pause(painter, s):
    painter.drawLine(_p(s, 0.36, 0.22), _p(s, 0.36, 0.78))
    painter.drawLine(_p(s, 0.64, 0.22), _p(s, 0.64, 0.78))


def _draw_stop(painter, s):
    _fill(painter, painter.pen().color())
    painter.drawRoundedRect(QRectF(0.28 * s, 0.28 * s, 0.44 * s, 0.44 * s), 0.08 * s, 0.08 * s)
    _nofill(painter)


def _draw_trash(painter, s):
    painter.drawLine(_p(s, 0.20, 0.30), _p(s, 0.80, 0.30))
    painter.drawPolyline(_poly(s, (0.38, 0.30), (0.40, 0.18), (0.60, 0.18), (0.62, 0.30)))
    painter.drawPolyline(_poly(s, (0.28, 0.30), (0.32, 0.82), (0.68, 0.82), (0.72, 0.30)))


def _draw_music(painter, s):
    painter.drawLine(_p(s, 0.66, 0.20), _p(s, 0.66, 0.68))
    painter.drawLine(_p(s, 0.66, 0.20), _p(s, 0.86, 0.26))
    painter.drawLine(_p(s, 0.86, 0.26), _p(s, 0.86, 0.44))
    painter.drawEllipse(_p(s, 0.56, 0.72), 0.13 * s, 0.11 * s)


def _draw_video(painter, s):
    painter.drawRoundedRect(QRectF(0.14 * s, 0.26 * s, 0.72 * s, 0.48 * s), 0.10 * s, 0.10 * s)
    _fill(painter, painter.pen().color())
    painter.drawPolygon(_poly(s, (0.44, 0.40), (0.66, 0.50), (0.44, 0.60)))
    _nofill(painter)


def _draw_warning(painter, s):
    painter.drawPolyline(_poly(s, (0.5, 0.16), (0.88, 0.82), (0.12, 0.82), (0.5, 0.16)))
    painter.drawLine(_p(s, 0.5, 0.40), _p(s, 0.5, 0.60))
    _fill(painter, painter.pen().color())
    painter.drawEllipse(_p(s, 0.5, 0.71), 0.035 * s, 0.035 * s)
    _nofill(painter)


def _draw_sparkle(painter, s):
    painter.drawLine(_p(s, 0.5, 0.14), _p(s, 0.5, 0.86))
    painter.drawLine(_p(s, 0.14, 0.5), _p(s, 0.86, 0.5))
    painter.drawLine(_p(s, 0.26, 0.26), _p(s, 0.74, 0.74))
    painter.drawLine(_p(s, 0.74, 0.26), _p(s, 0.26, 0.74))


_DRAWERS = {
    "games": _draw_gamepad,
    "gamepad": _draw_gamepad,
    "search": _draw_search,
    "disc": _draw_disc,
    "software": _draw_disc,
    "wrench": _draw_wrench,
    "patcher": _draw_wrench,
    "box": _draw_box,
    "downloader": _draw_box,
    "chip": _draw_chip,
    "emulators": _draw_chip,
    "info": _draw_info,
    "tray": _draw_tray,
    "downloads": _draw_tray,
    "gear": _draw_gear,
    "settings": _draw_gear,
    "check": _draw_check,
    "chevron_down": _draw_chevron_down,
    "chevron_right": _draw_chevron_right,
    "folder": _draw_folder,
    "external": _draw_external,
    "refresh": _draw_refresh,
    "play": _draw_play,
    "star": _draw_star,
    "pause": _draw_pause,
    "stop": _draw_stop,
    "trash": _draw_trash,
    "music": _draw_music,
    "video": _draw_video,
    "warning": _draw_warning,
    "sparkle": _draw_sparkle,
}


@lru_cache(maxsize=256)
def _pixmap(name, color, size):
    drawer = _DRAWERS.get(name)
    if drawer is None:
        return None

    scale = 2  # render at 2x for crisp HiDPI output
    pixmap = QPixmap(int(size * scale), int(size * scale))
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.5, size * 0.085))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    try:
        drawer(painter, size)
    finally:
        painter.end()
    return pixmap


def make_icon(name, color, size=20):
    """Return a QIcon for ``name`` tinted with ``color`` (empty if unknown)."""
    pixmap = _pixmap(name, color, size)
    if pixmap is None:
        return QIcon()
    return QIcon(pixmap)


def available_icons():
    return sorted(_DRAWERS)

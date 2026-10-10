"""Construction de la petite carte (tuiles OpenStreetMap, filtre Matrix optionnel)."""
import math

import requests
from PySide6.QtGui import QColor, QImage, QPainter, QPen

import config as c


def latlon_to_tile(lat, lon, zoom):
    """Coordonnées flottantes de tuile pour une latitude/longitude."""
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def _download_tiles(canvas, session, tx, ty):
    n = 2 ** c.MAP_ZOOM
    p = QPainter(canvas)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = (tx + dx) % n, ty + dy
            if not 0 <= y < n:
                continue
            url = c.OSM_TILE_URL.format(z=c.MAP_ZOOM, x=x, y=y)
            try:
                r = session.get(url, headers=c.HTTP_HEADERS, timeout=c.HTTP_TIMEOUT)
                r.raise_for_status()
                p.drawImage((dx + 1) * c.TILE_SIZE, (dy + 1) * c.TILE_SIZE,
                            QImage.fromData(r.content))
            except requests.RequestException:
                pass
    p.end()


def _apply_matrix_filter(img):
    """Niveaux de gris -> inversion -> teinte verte."""
    img = img.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_RGB32)
    img.invertPixels(QImage.InvertRgb)
    p = QPainter(img)
    p.setCompositionMode(QPainter.CompositionMode_Multiply)
    p.fillRect(img.rect(), QColor(*c.MATRIX_GREEN_RGB))
    p.end()
    return img


def _draw_marker(img):
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    cx, cy = c.MAP_WIDTH // 2, c.MAP_HEIGHT // 2
    # contour blanc puis trait coloré, pour rester lisible sur tous les fonds
    for color, width in ((c.MARKER_OUTLINE_COLOR, 5), (c.MARKER_COLOR, 2)):
        p.setPen(QPen(QColor(color), width))
        p.drawEllipse(cx - 8, cy - 8, 16, 16)
        p.drawLine(cx - 14, cy, cx + 14, cy)
        p.drawLine(cx, cy - 14, cx, cy + 14)
    p.end()


def build_map(lat, lon, session):
    """Retourne un QImage MAP_WIDTH x MAP_HEIGHT centré sur (lat, lon)."""
    t = c.TILE_SIZE
    fx, fy = latlon_to_tile(lat, lon, c.MAP_ZOOM)
    tx, ty = int(fx), int(fy)

    canvas = QImage(t * 3, t * 3, QImage.Format_RGB32)
    canvas.fill(QColor("black"))
    _download_tiles(canvas, session, tx, ty)

    px = int((fx - (tx - 1)) * t)
    py = int((fy - (ty - 1)) * t)
    crop = canvas.copy(px - c.MAP_WIDTH // 2, py - c.MAP_HEIGHT // 2,
                       c.MAP_WIDTH, c.MAP_HEIGHT)
    if c.MAP_MATRIX_FILTER:
        crop = _apply_matrix_filter(crop)
    _draw_marker(crop)
    return crop
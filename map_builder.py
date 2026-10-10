"""Construction de la petite carte (tuiles OpenStreetMap, filtre Matrix optionnel).

Rapide : seules les tuiles visibles sont chargées, en parallèle, avec cache disque."""
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests
from PySide6.QtGui import QColor, QImage, QPainter, QPen

import config as c


def latlon_to_tile(lat, lon, zoom):
    """Coordonnées flottantes de tuile pour une latitude/longitude."""
    n = 2 ** zoom
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def _cache_path(z, x, y):
    return os.path.join(c.TILE_CACHE_DIR, f"{z}_{x}_{y}.png")


def _read_cache(z, x, y):
    """Octets de la tuile en cache disque (si récente), sinon None."""
    path = _cache_path(z, x, y)
    try:
        if time.time() - os.path.getmtime(path) < c.TILE_CACHE_MAX_AGE:
            with open(path, "rb") as f:
                return f.read()
    except OSError:
        pass
    return None


def _write_cache(z, x, y, data):
    try:
        os.makedirs(c.TILE_CACHE_DIR, exist_ok=True)
        with open(_cache_path(z, x, y), "wb") as f:
            f.write(data)
    except OSError:
        pass


def _fetch_tile(session, z, x, y):
    """Octets PNG d'une tuile : cache disque d'abord, réseau sinon (None si échec)."""
    data = _read_cache(z, x, y)
    if data is not None:
        return data
    try:
        r = session.get(c.OSM_TILE_URL.format(z=z, x=x, y=y),
                        headers=c.HTTP_HEADERS, timeout=c.TILE_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException:
        return None
    _write_cache(z, x, y, r.content)
    return r.content


def _visible_tiles(left, top):
    """Tuiles (dx, dy) du canevas 3x3 qui recoupent la zone affichée.
    (left, top) = coin haut-gauche de la zone dans le canevas."""
    t = c.TILE_SIZE
    right, bottom = left + c.MAP_WIDTH, top + c.MAP_HEIGHT
    tiles = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x0, y0 = (dx + 1) * t, (dy + 1) * t
            if x0 < right and x0 + t > left and y0 < bottom and y0 + t > top:
                tiles.append((dx, dy))
    return tiles


def _draw_tiles(canvas, session, tx, ty, left, top):
    """Charge en parallèle uniquement les tuiles visibles, puis les assemble."""
    n = 2 ** c.MAP_ZOOM
    jobs = []
    for dx, dy in _visible_tiles(left, top):
        y = ty + dy
        if 0 <= y < n:
            jobs.append((dx, dy, (tx + dx) % n, y))

    with ThreadPoolExecutor(max_workers=c.TILE_WORKERS) as pool:
        results = list(pool.map(
            lambda j: _fetch_tile(session, c.MAP_ZOOM, j[2], j[3]), jobs))

    p = QPainter(canvas)
    for (dx, dy, _x, _y), data in zip(jobs, results):
        if data:
            p.drawImage((dx + 1) * c.TILE_SIZE, (dy + 1) * c.TILE_SIZE,
                        QImage.fromData(data))
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

    # position de la zone affichée dans le canevas de 3x3 tuiles
    px = int((fx - (tx - 1)) * t)
    py = int((fy - (ty - 1)) * t)
    left, top = px - c.MAP_WIDTH // 2, py - c.MAP_HEIGHT // 2

    canvas = QImage(t * 3, t * 3, QImage.Format_RGB32)
    canvas.fill(QColor("black"))
    _draw_tiles(canvas, session, tx, ty, left, top)

    crop = canvas.copy(left, top, c.MAP_WIDTH, c.MAP_HEIGHT)
    if c.MAP_MATRIX_FILTER:
        crop = _apply_matrix_filter(crop)
    _draw_marker(crop)
    return crop
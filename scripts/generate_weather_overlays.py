"""
Generate pixel-art weather overlay sprites.
These are composited ON TOP of emotion frames.

Usage: python scripts/generate_weather_overlays.py
Output: src/ui/assets/sprites/weather/<state>.png
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEATHER_DIR = ROOT / "src" / "ui" / "assets" / "sprites" / "weather"

try:
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QApplication
except ImportError:
    print("PySide6 required: pip install PySide6")
    sys.exit(1)

GRID = 24
PX = 4
SIZE = GRID * PX

__ = None

COLOR = {
    "scarf_red": QColor("#E74C3C"),
    "scarf_dark": QColor("#C0392B"),
    "lens": QColor("#2C3E50"),
    "frame": QColor("#1a1a2e"),
    "rain_drop": QColor("#5DADE2"),
    "rain_dark": QColor("#3498DB"),
    "snow": QColor("#ECF0F1"),
    "snow_shade": QColor("#BDC3C7"),
    "cloud": QColor("#95A5A6"),
    "cloud_light": QColor("#BDC3C7"),
    "sun_glow": QColor("#FFF176"),
    "sweat": QColor("#85C1E9"),
}


def _render_grid(grid: list[list[tuple[str, ...] | None]]) -> QImage:
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    for r in range(GRID):
        for c in range(GRID):
            val = grid[r][c]
            if val is None:
                continue
            color = COLOR.get(val)
            if color:
                p.fillRect(QRect(c * PX, r * PX, PX, PX), color)
    p.end()
    return img


def _empty() -> list[list]:
    return [[__] * GRID for _ in range(GRID)]


def _gen_cold() -> QImage:
    g = _empty()
    # scarf around neck area (rows 15-16, cols 6-17)
    for c in range(6, 18):
        g[15][c] = "scarf_red"
        g[16][c] = "scarf_dark"
    # scarf tail hanging left
    g[17][5] = "scarf_red"
    g[18][5] = "scarf_red"
    g[19][5] = "scarf_dark"
    g[17][6] = "scarf_dark"
    g[18][6] = "scarf_dark"
    # knot
    g[15][11] = "scarf_dark"
    g[15][12] = "scarf_dark"
    return _render_grid(g)


def _gen_hot() -> QImage:
    g = _empty()
    # sunglasses on eyes area (rows 10-11, cols 6-17)
    # frame
    for c in range(6, 10):
        g[10][c] = "frame"
        g[12][c] = "frame"
    for c in range(14, 18):
        g[10][c] = "frame"
        g[12][c] = "frame"
    g[11][6] = "frame"
    g[11][9] = "frame"
    g[11][14] = "frame"
    g[11][17] = "frame"
    # lenses
    for c in range(7, 9):
        g[11][c] = "lens"
    for c in range(15, 17):
        g[11][c] = "lens"
    # bridge
    g[11][10] = "frame"
    g[11][11] = "frame"
    g[11][12] = "frame"
    g[11][13] = "frame"
    # sweat drop
    g[13][19] = "sweat"
    g[14][19] = "sweat"
    g[15][19] = "sweat"
    # sun glow top-right
    g[1][20] = "sun_glow"
    g[1][21] = "sun_glow"
    g[2][21] = "sun_glow"
    g[2][22] = "sun_glow"
    g[0][21] = "sun_glow"
    g[1][22] = "sun_glow"
    return _render_grid(g)


def _gen_rain() -> QImage:
    g = _empty()
    # rain drops scattered
    drops = [
        (1, 3),
        (3, 7),
        (2, 13),
        (4, 19),
        (1, 22),
        (6, 1),
        (5, 10),
        (7, 16),
        (6, 21),
        (20, 5),
        (21, 9),
        (20, 14),
        (22, 18),
        (21, 22),
        (22, 2),
        (23, 11),
        (22, 20),
    ]
    for r, c in drops:
        if 0 <= r < GRID and 0 <= c < GRID:
            g[r][c] = "rain_drop"
        if r + 1 < GRID:
            g[r + 1][c] = "rain_dark"
    # small cloud top
    for c in range(8, 16):
        g[0][c] = "cloud"
    for c in range(9, 15):
        g[1][c] = "cloud_light"
    return _render_grid(g)


def _gen_snow() -> QImage:
    g = _empty()
    # snowflakes scattered
    flakes = [
        (1, 4),
        (2, 9),
        (0, 15),
        (3, 20),
        (5, 2),
        (4, 12),
        (6, 18),
        (5, 23),
        (20, 3),
        (21, 8),
        (22, 14),
        (20, 19),
        (21, 23),
        (23, 6),
        (22, 11),
        (23, 17),
    ]
    for r, c in flakes:
        if 0 <= r < GRID and 0 <= c < GRID:
            g[r][c] = "snow"
    # snow on head (rows 7-8)
    for c in range(9, 19):
        g[7][c] = "snow"
    g[7][8] = "snow_shade"
    g[7][19] = "snow_shade"
    # small pile on ears
    g[3][3] = "snow"
    g[3][4] = "snow"
    g[3][20] = "snow"
    g[3][19] = "snow"
    return _render_grid(g)


def _gen_cloudy() -> QImage:
    g = _empty()
    # clouds at top
    for c in range(5, 12):
        g[0][c] = "cloud"
    for c in range(6, 11):
        g[1][c] = "cloud_light"
    for c in range(13, 20):
        g[1][c] = "cloud"
    for c in range(14, 19):
        g[2][c] = "cloud_light"
    # small cloud bits
    g[0][18] = "cloud"
    g[0][19] = "cloud"
    g[3][3] = "cloud_light"
    g[3][4] = "cloud_light"
    return _render_grid(g)


GENERATORS = {
    "cold": _gen_cold,
    "hot": _gen_hot,
    "rain": _gen_rain,
    "snow": _gen_snow,
    "cloudy": _gen_cloudy,
}


def main() -> None:
    _app = QApplication.instance() or QApplication(sys.argv)
    WEATHER_DIR.mkdir(parents=True, exist_ok=True)

    for name, gen in GENERATORS.items():
        img = gen()
        path = WEATHER_DIR / f"{name}.png"
        img.save(str(path))
        print(f"  {name} -> {path}")

    print("Done. (clear = no overlay)")


if __name__ == "__main__":
    main()

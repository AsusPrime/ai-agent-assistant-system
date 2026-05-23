"""
Generate pixel-art time-of-day overlay sprites.
Composited ON TOP of emotion frames (same as weather overlays).

Usage: python scripts/generate_tod_overlays.py
Output: src/ui/assets/sprites/timeofday/<state>.png
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOD_DIR = ROOT / "src" / "ui" / "assets" / "sprites" / "timeofday"

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
    # night
    "cap": QColor("#7B68EE"),
    "cap_dark": QColor("#5B48CE"),
    "cap_tip": QColor("#FFD93D"),
    "star": QColor("#FFF176"),
    "star_dim": QColor("#FFF9C4"),
    "moon": QColor("#FFF9C4"),
    "moon_shade": QColor("#FFE082"),
    # morning
    "coffee": QColor("#8B5E3C"),
    "coffee_dk": QColor("#6D4C2A"),
    "steam": QColor(200, 200, 200, 160),
    "sunrise": QColor("#FFB74D"),
    "sunrise_lt": QColor("#FFE0B2"),
    # evening
    "eve_moon": QColor("#FFCC80"),
    "eve_star": QColor("#FFE082"),
    "eve_dim": QColor(100, 100, 140, 60),
}


def _empty() -> list[list]:
    return [[__] * GRID for _ in range(GRID)]


def _render(grid: list[list]) -> QImage:
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


def _gen_night() -> QImage:
    g = _empty()

    # ── sleep cap on head (rows 5-8) ──
    # cap body
    for c in range(8, 17):
        g[7][c] = "cap"
    for c in range(9, 16):
        g[6][c] = "cap"
    for c in range(10, 15):
        g[5][c] = "cap_dark"
    # cap drooping to the right
    g[5][15] = "cap"
    g[5][16] = "cap"
    g[4][16] = "cap"
    g[4][17] = "cap"
    g[3][17] = "cap_dark"
    g[3][18] = "cap_dark"
    g[2][18] = "cap_dark"
    g[2][19] = "cap_dark"
    # pompom at tip
    g[1][19] = "cap_tip"
    g[1][20] = "cap_tip"
    g[2][20] = "cap_tip"

    # ── stars ──
    g[0][3] = "star"
    g[1][7] = "star_dim"
    g[3][1] = "star_dim"
    g[0][22] = "star"
    g[2][23] = "star_dim"
    g[4][21] = "star"

    # ── crescent moon top-left ──
    g[0][0] = "moon"
    g[0][1] = "moon"
    g[1][0] = "moon"
    g[1][1] = "moon_shade"
    g[2][0] = "moon"

    return _render(g)


def _gen_morning() -> QImage:
    g = _empty()

    # ── small coffee cup bottom-right ──
    # cup body
    for r in range(18, 21):
        for c in range(19, 22):
            g[r][c] = "coffee"
    # cup rim
    for c in range(18, 23):
        g[17][c] = "coffee_dk"
    # handle
    g[19][22] = "coffee_dk"
    g[20][22] = "coffee_dk"
    # saucer
    for c in range(18, 23):
        g[21][c] = "coffee_dk"

    # steam
    g[15][20] = "steam"
    g[14][19] = "steam"
    g[13][20] = "steam"
    g[16][19] = "steam"

    # ── sunrise glow top-right ──
    g[0][20] = "sunrise_lt"
    g[0][21] = "sunrise"
    g[0][22] = "sunrise"
    g[0][23] = "sunrise_lt"
    g[1][21] = "sunrise_lt"
    g[1][22] = "sunrise_lt"
    g[1][23] = "sunrise"
    g[2][22] = "sunrise_lt"
    g[2][23] = "sunrise_lt"

    return _render(g)


def _gen_evening() -> QImage:
    g = _empty()

    # ── moon top-right ──
    g[0][20] = "eve_moon"
    g[0][21] = "eve_moon"
    g[0][22] = "eve_moon"
    g[1][20] = "eve_moon"
    g[1][21] = __  # crescent cutout
    g[1][22] = "eve_moon"
    g[2][20] = "eve_moon"
    g[2][21] = "eve_moon"
    g[2][22] = "eve_moon"

    # ── a few stars ──
    g[0][3] = "eve_star"
    g[1][10] = "eve_star"
    g[3][0] = "eve_star"
    g[0][16] = "eve_star"
    g[4][23] = "eve_star"

    # ── dim overlay edges (subtle darkening) ──
    for r in range(GRID):
        g[r][0] = g[r][0] or "eve_dim"
        g[r][23] = g[r][23] or "eve_dim"

    return _render(g)


GENERATORS = {
    "night": _gen_night,
    "morning": _gen_morning,
    "evening": _gen_evening,
}


def main() -> None:
    _app = QApplication.instance() or QApplication(sys.argv)
    TOD_DIR.mkdir(parents=True, exist_ok=True)

    for name, gen in GENERATORS.items():
        img = gen()
        path = TOD_DIR / f"{name}.png"
        img.save(str(path))
        print(f"  {name} -> {path}")

    print("Done. (day = no overlay)")


if __name__ == "__main__":
    main()

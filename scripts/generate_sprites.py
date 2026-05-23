"""
Generate pixel-art Robot AI assistant sprite frames for each emotion.
Each frame is drawn on a pixel grid (1 cell = N px) for crisp retro look.

Usage: python scripts/generate_sprites.py
Output: src/ui/assets/sprites/<emotion>/frame_NNN.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPRITES_DIR = ROOT / "src" / "ui" / "assets" / "sprites"

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
K = "K"  # black / outline
M = "M"  # metal body (light silver-blue)
D = "D"  # dark metal (darker panels)
C = "C"  # cyan (LED eyes, accents)
W = "W"  # white
G = "G"  # green (status light)
R = "R"  # red (error light)
A = "A"  # antenna tip (bright cyan)
S = "S"  # screen (dark blue-gray)
H = "H"  # highlight (light cyan)
L = "L"  # blue (tears / sad)
Z = "Z"  # zzz color (lavender)
P = "P"  # panel accent (mid blue)
Y = "Y"  # yellow (spark)
T = "T"  # mouth / expression (warm orange)

COLOR_MAP = {
    "K": QColor("#1a1a2e"),
    "M": QColor("#B0BEC5"),
    "D": QColor("#78909C"),
    "C": QColor("#00E5FF"),
    "W": QColor("#FFFFFF"),
    "G": QColor("#69F0AE"),
    "R": QColor("#FF5252"),
    "A": QColor("#18FFFF"),
    "S": QColor("#37474F"),
    "H": QColor("#B2EBF2"),
    "L": QColor("#5DADE2"),
    "Z": QColor("#B8B8FF"),
    "P": QColor("#4FC3F7"),
    "Y": QColor("#FFD740"),
    "T": QColor("#FF8A65"),
}

SPRITE_META = {
    "idle": {"frame_ms": 220, "loop": True, "frames": 6},
    "thinking": {"frame_ms": 180, "loop": True, "frames": 6},
    "happy": {"frame_ms": 100, "loop": False, "frames": 8},
    "sad": {"frame_ms": 300, "loop": False, "frames": 6},
    "error": {"frame_ms": 120, "loop": False, "frames": 6},
    "greeting": {"frame_ms": 120, "loop": False, "frames": 8},
    "sleepy": {"frame_ms": 400, "loop": True, "frames": 6},
}

# ─── Base Robot template (24x24 grid) ───
# Antenna top, rectangular head with LED eyes, body with chest panel, arms, legs

_BASE = [
    # 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
    [
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        A,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 0  antenna tip
    [
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 1  antenna
    [
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 2  antenna
    [
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 3  head top
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 4
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 5
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        K,
        K,
        K,
        M,
        M,
        M,
        K,
        K,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 6  eyes row top
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        K,
        C,
        K,
        M,
        M,
        M,
        K,
        C,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 7  eyes
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        K,
        C,
        K,
        M,
        M,
        M,
        K,
        C,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 8  eyes
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        K,
        K,
        K,
        M,
        M,
        M,
        K,
        K,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 9  eyes row bottom
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 10
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        M,
        M,
        K,
        K,
        K,
        M,
        M,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 11 mouth
    [
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 12
    [
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 13 neck
    [
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
    ],  # 14 body top + arms
    [
        __,
        __,
        __,
        K,
        M,
        K,
        K,
        D,
        S,
        S,
        S,
        S,
        S,
        S,
        S,
        D,
        K,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
    ],  # 15 arms + screen
    [
        __,
        __,
        __,
        K,
        M,
        K,
        K,
        D,
        S,
        P,
        S,
        G,
        S,
        P,
        S,
        D,
        K,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
    ],  # 16 screen details
    [
        __,
        __,
        __,
        K,
        M,
        K,
        K,
        D,
        S,
        S,
        S,
        S,
        S,
        S,
        S,
        D,
        K,
        K,
        M,
        K,
        __,
        __,
        __,
        __,
    ],  # 17
    [
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        D,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
    ],  # 18 body bottom
    [
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 19 waist
    [
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        K,
        __,
        __,
        __,
        K,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 20 legs
    [
        __,
        __,
        __,
        __,
        __,
        __,
        K,
        M,
        M,
        K,
        __,
        __,
        __,
        K,
        M,
        M,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 21 legs
    [
        __,
        __,
        __,
        __,
        __,
        K,
        K,
        M,
        M,
        K,
        K,
        __,
        K,
        K,
        M,
        M,
        K,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 22 feet
    [
        __,
        __,
        __,
        __,
        __,
        K,
        K,
        K,
        K,
        K,
        K,
        __,
        K,
        K,
        K,
        K,
        K,
        K,
        __,
        __,
        __,
        __,
        __,
        __,
    ],  # 23 feet bottom
]


def _copy_grid(src: list[list]) -> list[list]:
    return [row[:] for row in src]


def _set_px(grid: list[list], r: int, c: int, val) -> None:
    if 0 <= r < GRID and 0 <= c < GRID:
        grid[r][c] = val


def _render(grid: list[list]) -> QImage:
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))
    p = QPainter(img)
    for r in range(GRID):
        for c in range(GRID):
            val = grid[r][c]
            if val is None:
                continue
            color = COLOR_MAP.get(val)
            if color is None:
                continue
            p.fillRect(QRect(c * PX, r * PX, PX, PX), color)
    p.end()
    return img


def _shift_grid(grid: list[list], dx: int, dy: int) -> list[list]:
    new = [[__] * GRID for _ in range(GRID)]
    for r in range(GRID):
        for c in range(GRID):
            nr, nc = r + dy, c + dx
            if 0 <= nr < GRID and 0 <= nc < GRID:
                new[nr][nc] = grid[r][c]
    return new


# ─── Emotion frame generators ───


def _frame_idle(frame: int, total: int) -> QImage:
    g = _copy_grid(_BASE)
    # antenna blink on frame 0,3
    if frame in (0, 3):
        _set_px(g, 0, 11, H)
    # blink eyes on frame 4
    if frame == 4:
        for r in (7, 8):
            _set_px(g, r, 8, K)
            _set_px(g, r, 14, K)
    # status light pulse
    if frame in (2, 3, 4):
        _set_px(g, 16, 11, H)
    return _render(g)


def _frame_happy(frame: int, total: int) -> QImage:
    dy = -1 if frame % 4 == 1 else 0
    g = _copy_grid(_BASE)

    # happy eyes: upward arcs ^ ^
    for r in (6, 7, 8, 9):
        _set_px(g, r, 8, M)
        _set_px(g, r, 14, M)
    _set_px(g, 6, 7, K)
    _set_px(g, 6, 8, K)
    _set_px(g, 6, 9, K)
    _set_px(g, 7, 7, C)
    _set_px(g, 7, 9, C)
    _set_px(g, 6, 13, K)
    _set_px(g, 6, 14, K)
    _set_px(g, 6, 15, K)
    _set_px(g, 7, 13, C)
    _set_px(g, 7, 15, C)

    # wide smile
    _set_px(g, 11, 9, K)
    _set_px(g, 11, 10, T)
    _set_px(g, 11, 11, T)
    _set_px(g, 11, 12, T)
    _set_px(g, 11, 13, K)
    _set_px(g, 12, 10, K)
    _set_px(g, 12, 11, K)
    _set_px(g, 12, 12, K)

    # green status light bright
    _set_px(g, 16, 11, G)
    _set_px(g, 16, 10, G)
    _set_px(g, 16, 12, G)

    # sparkles
    if frame % 3 == 0:
        _set_px(g, 1, 8, Y)
        _set_px(g, 2, 15, Y)
        _set_px(g, 0, 13, Y)

    if dy != 0:
        g = _shift_grid(g, 0, dy)
    return _render(g)


def _frame_thinking(frame: int, total: int) -> QImage:
    g = _copy_grid(_BASE)

    # eyes look to side
    look_right = (frame // 2) % 2 == 0
    offset = 1 if look_right else -1

    for r in (7, 8):
        _set_px(g, r, 8, M)
        _set_px(g, r, 14, M)
        ec1 = 8 + offset
        ec2 = 14 + offset
        if 0 <= ec1 < GRID:
            _set_px(g, r, ec1, C)
        if 0 <= ec2 < GRID:
            _set_px(g, r, ec2, C)

    # small 'o' mouth
    _set_px(g, 11, 11, K)

    # thought bubbles
    bx = 19
    if frame % 6 < 3:
        _set_px(g, 4, bx, W)
        _set_px(g, 2, bx + 1, W)
        _set_px(g, 2, bx + 2, W)
        _set_px(g, 1, bx + 2, W)
        _set_px(g, 1, bx + 3, W)
    else:
        _set_px(g, 5, bx, W)
        _set_px(g, 3, bx + 1, W)
        _set_px(g, 3, bx + 2, W)
        _set_px(g, 2, bx + 2, W)
        _set_px(g, 2, bx + 3, W)

    # antenna pulses
    _set_px(g, 0, 11, P if frame % 2 == 0 else C)

    return _render(g)


def _frame_sad(frame: int, total: int) -> QImage:
    g = _copy_grid(_BASE)

    # sad eyebrows: angled down \_/
    _set_px(g, 5, 7, K)
    _set_px(g, 6, 8, K)
    _set_px(g, 5, 15, K)
    _set_px(g, 6, 14, K)

    # dimmer eyes
    for r in (7, 8):
        _set_px(g, r, 8, P)
        _set_px(g, r, 14, P)

    # frown
    _set_px(g, 12, 10, K)
    _set_px(g, 11, 11, K)
    _set_px(g, 11, 12, K)
    _set_px(g, 12, 13, K)

    # tears
    tear_row = 10 + (frame % 4)
    if tear_row < GRID:
        _set_px(g, tear_row, 9, L)
    if tear_row + 1 < GRID:
        _set_px(g, tear_row + 1, 9, L)

    # status light dim/red
    _set_px(g, 16, 11, P)

    if frame >= 3:
        g = _shift_grid(g, 0, 1)
    return _render(g)


def _frame_error(frame: int, total: int) -> QImage:
    g = _copy_grid(_BASE)

    # X X eyes
    for r in (6, 7, 8, 9):
        _set_px(g, r, 8, M)
        _set_px(g, r, 14, M)
    _set_px(g, 7, 7, R)
    _set_px(g, 7, 9, R)
    _set_px(g, 8, 8, R)
    _set_px(g, 8, 7, R)
    _set_px(g, 8, 9, R)
    _set_px(g, 7, 8, R)
    _set_px(g, 7, 13, R)
    _set_px(g, 7, 15, R)
    _set_px(g, 8, 14, R)
    _set_px(g, 8, 13, R)
    _set_px(g, 8, 15, R)
    _set_px(g, 7, 14, R)

    # zigzag mouth
    _set_px(g, 11, 9, K)
    _set_px(g, 12, 10, K)
    _set_px(g, 11, 11, K)
    _set_px(g, 12, 12, K)
    _set_px(g, 11, 13, K)

    # red status light
    _set_px(g, 16, 11, R)
    _set_px(g, 16, 10, R)
    _set_px(g, 16, 12, R)

    # shake
    dx = 1 if frame % 2 == 0 else -1
    g = _shift_grid(g, dx, 0)

    # warning sparks
    if frame % 2 == 0:
        _set_px(g, 2, 8, Y)
        _set_px(g, 1, 14, Y)
        _set_px(g, 3, 19, Y)

    return _render(g)


def _frame_greeting(frame: int, total: int) -> QImage:
    jump_seq = [0, -1, -2, -3, -2, -1, 0, 0]
    dy = jump_seq[frame % len(jump_seq)]

    g = _copy_grid(_BASE)

    # bright sparkly eyes
    for r in (7, 8):
        _set_px(g, r, 8, H)
        _set_px(g, r, 14, H)
    _set_px(g, 7, 8, W)
    _set_px(g, 7, 14, W)

    # wide smile
    _set_px(g, 11, 9, K)
    _set_px(g, 11, 10, T)
    _set_px(g, 11, 11, T)
    _set_px(g, 11, 12, T)
    _set_px(g, 11, 13, K)
    _set_px(g, 12, 10, K)
    _set_px(g, 12, 11, K)
    _set_px(g, 12, 12, K)

    # raised arm (right arm goes up)
    if frame < 5:
        _set_px(g, 15, 18, __)
        _set_px(g, 15, 19, __)
        _set_px(g, 16, 18, __)
        _set_px(g, 16, 19, __)
        _set_px(g, 17, 18, __)
        _set_px(g, 17, 19, __)
        _set_px(g, 13, 19, K)
        _set_px(g, 12, 19, K)
        _set_px(g, 11, 19, M)
        _set_px(g, 10, 19, M)
        _set_px(g, 10, 20, K)
        _set_px(g, 11, 20, K)

    # antenna bright
    _set_px(g, 0, 11, G)

    if dy != 0:
        g = _shift_grid(g, 0, dy)

    # sparkle stars
    star_positions = [(1, 5), (0, 17), (2, 21), (4, 2), (1, 13)]
    for i, (sr, sc) in enumerate(star_positions):
        if (frame + i) % 3 == 0:
            _set_px(g, sr, sc, Y)

    return _render(g)


def _frame_sleepy(frame: int, total: int) -> QImage:
    g = _copy_grid(_BASE)

    # closed eyes (horizontal lines)
    for r in (6, 7, 8, 9):
        _set_px(g, r, 8, M)
        _set_px(g, r, 14, M)
    _set_px(g, 8, 7, K)
    _set_px(g, 8, 8, K)
    _set_px(g, 8, 9, K)
    _set_px(g, 8, 13, K)
    _set_px(g, 8, 14, K)
    _set_px(g, 8, 15, K)

    # small mouth
    if frame in (2, 3):
        _set_px(g, 11, 10, K)
        _set_px(g, 11, 11, K)
        _set_px(g, 11, 12, K)
        _set_px(g, 12, 10, K)
        _set_px(g, 12, 11, K)
        _set_px(g, 12, 12, K)
    else:
        _set_px(g, 11, 11, K)

    # zzz floating
    z_row = 3 - (frame % 3)
    z_col = 19 + (frame % 3)
    if 0 <= z_row < GRID and 0 <= z_col < GRID:
        _set_px(g, z_row, z_col, Z)
    if z_row - 2 >= 0 and z_col - 1 >= 0:
        _set_px(g, z_row - 2, z_col - 1, Z)

    # dim antenna
    _set_px(g, 0, 11, D)

    # status light dim
    _set_px(g, 16, 11, D)

    # slight sway
    dx = 1 if frame in (0, 1, 2) else 0
    if dx:
        g = _shift_grid(g, dx, 0)

    return _render(g)


GENERATORS = {
    "idle": _frame_idle,
    "thinking": _frame_thinking,
    "happy": _frame_happy,
    "sad": _frame_sad,
    "error": _frame_error,
    "greeting": _frame_greeting,
    "sleepy": _frame_sleepy,
}


def main() -> None:
    _app = QApplication.instance() or QApplication(sys.argv)

    for emotion, meta in SPRITE_META.items():
        out_dir = SPRITES_DIR / emotion
        out_dir.mkdir(parents=True, exist_ok=True)

        for old in out_dir.glob("frame_*.png"):
            old.unlink()

        gen = GENERATORS[emotion]
        n_frames = meta["frames"]
        for i in range(n_frames):
            img = gen(i, n_frames)
            path = out_dir / f"frame_{i:03d}.png"
            img.save(str(path))

        print(f"  {emotion}: {n_frames} frames -> {out_dir}")

    meta_path = SPRITES_DIR / "meta.json"
    meta_out = {}
    for emotion, m in SPRITE_META.items():
        meta_out[emotion] = {"frame_ms": m["frame_ms"], "loop": m["loop"]}
    meta_path.write_text(json.dumps(meta_out, indent=2))
    print(f"  meta.json -> {meta_path}")
    print("Done.")


if __name__ == "__main__":
    main()

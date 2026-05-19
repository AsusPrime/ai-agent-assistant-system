from __future__ import annotations

import platform

_SYSTEM = platform.system()

if _SYSTEM == "Darwin":
    FONT_FAMILY = ".AppleSystemUIFont"
    EMOJI_FAMILY = "Apple Color Emoji"
elif _SYSTEM == "Windows":
    FONT_FAMILY = "Segoe UI"
    EMOJI_FAMILY = "Segoe UI Emoji"
else:
    FONT_FAMILY = "Sans"
    EMOJI_FAMILY = "Noto Color Emoji"

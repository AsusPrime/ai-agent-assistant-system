from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget

from ui.emotions import Emotion

_SPRITES_DIR = Path(__file__).resolve().parent / "assets" / "sprites"
_WEATHER_DIR = _SPRITES_DIR / "weather"
_TOD_DIR = _SPRITES_DIR / "timeofday"


class SpriteAnimation:
    def __init__(self, frames: list[QPixmap], frame_ms: int, loop: bool) -> None:
        self.frames = frames
        self.frame_ms = frame_ms
        self.loop = loop
        self.current = 0

    @property
    def is_empty(self) -> bool:
        return len(self.frames) == 0

    def reset(self) -> None:
        self.current = 0

    def advance(self) -> bool:
        if self.is_empty:
            return False
        self.current += 1
        if self.current >= len(self.frames):
            if self.loop:
                self.current = 0
            else:
                self.current = len(self.frames) - 1
                return False
        return True

    def pixmap(self) -> QPixmap | None:
        if self.is_empty:
            return None
        return self.frames[self.current]


def _load_meta() -> dict:
    meta_path = _SPRITES_DIR / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    return {}


def _load_animation(emotion_name: str, meta: dict) -> SpriteAnimation:
    folder = _SPRITES_DIR / emotion_name
    if not folder.is_dir():
        return SpriteAnimation([], 250, True)

    frame_files = sorted(folder.glob("frame_*.png"))
    frames = []
    for f in frame_files:
        px = QPixmap(str(f))
        if not px.isNull():
            frames.append(px)

    info = meta.get(emotion_name, {})
    frame_ms = info.get("frame_ms", 250)
    loop = info.get("loop", True)
    return SpriteAnimation(frames, frame_ms, loop)


def _load_overlay(directory: Path, name: str) -> QPixmap | None:
    path = directory / f"{name}.png"
    if path.exists():
        px = QPixmap(str(path))
        if not px.isNull():
            return px
    return None


class TamagotchiWidget(QWidget):
    animation_finished = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(80, 80)

        self._emotion = Emotion.IDLE
        self._animations: dict[str, SpriteAnimation] = {}
        self._current_anim: SpriteAnimation | None = None
        self._overlays: list[QPixmap] = []

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)

        self._load_all_sprites()
        self._play(Emotion.IDLE)

    def _load_all_sprites(self) -> None:
        meta = _load_meta()
        for emotion in Emotion:
            self._animations[emotion.value] = _load_animation(emotion.value, meta)

    def reload_sprites(self) -> None:
        self._load_all_sprites()
        self._play(self._emotion)

    def set_weather(self, state: str) -> None:
        px = _load_overlay(_WEATHER_DIR, state)
        if px:
            self._overlays.append(px)
            self.update()

    def set_time_of_day(self, state: str) -> None:
        px = _load_overlay(_TOD_DIR, state)
        if px:
            self._overlays.append(px)
            self.update()

    def set_emotion(self, emotion: Emotion) -> None:
        if self._emotion == emotion:
            return
        self._emotion = emotion
        self._play(emotion)

    def _play(self, emotion: Emotion) -> None:
        self._timer.stop()

        anim = self._animations.get(emotion.value)
        if anim is None or anim.is_empty:
            anim = self._animations.get(Emotion.IDLE.value)
        if anim is None or anim.is_empty:
            self._current_anim = None
            return

        anim.reset()
        self._current_anim = anim
        self._timer.start(anim.frame_ms)
        self.update()

    def _next_frame(self) -> None:
        if self._current_anim is None:
            return

        still_playing = self._current_anim.advance()
        self.update()

        if not still_playing:
            self._timer.stop()
            self.animation_finished.emit(self._emotion.value)
            if self._emotion != Emotion.IDLE:
                self._emotion = Emotion.IDLE
                self._play(Emotion.IDLE)

    def paintEvent(self, event) -> None:
        if self._current_anim is None:
            return

        px = self._current_anim.pixmap()
        if px is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        scaled = px.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

        for overlay_px in self._overlays:
            overlay = overlay_px.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            ox = (self.width() - overlay.width()) // 2
            oy = (self.height() - overlay.height()) // 2
            painter.drawPixmap(ox, oy, overlay)

        painter.end()

from __future__ import annotations

from datetime import datetime
from enum import Enum


class Emotion(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    HAPPY = "happy"
    SAD = "sad"
    ERROR = "error"
    GREETING = "greeting"
    SLEEPY = "sleepy"


class TimeOfDay(str, Enum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    NIGHT = "night"


def get_time_of_day() -> TimeOfDay:
    hour = datetime.now().hour
    if 5 <= hour < 10:
        return TimeOfDay.MORNING
    if 10 <= hour < 18:
        return TimeOfDay.DAY
    if 18 <= hour < 23:
        return TimeOfDay.EVENING
    return TimeOfDay.NIGHT


def map_task_status_to_emotion(status: str) -> Emotion:
    mapping = {
        "pending": Emotion.THINKING,
        "running": Emotion.THINKING,
        "success": Emotion.HAPPY,
        "skipped": Emotion.IDLE,
        "error": Emotion.SAD,
        "failed": Emotion.SAD,
    }
    return mapping.get(status, Emotion.IDLE)


EMOTION_COLORS = {
    Emotion.IDLE: "#7ec8e3",
    Emotion.THINKING: "#ffd166",
    Emotion.HAPPY: "#06d6a0",
    Emotion.SAD: "#ef476f",
    Emotion.ERROR: "#ef476f",
    Emotion.GREETING: "#ffd166",
    Emotion.SLEEPY: "#b8b8ff",
}

EMOTION_KAOMOJI = {
    Emotion.IDLE: "(• ᴗ •)",
    Emotion.THINKING: "(◔ ᴗ ◔)...",
    Emotion.HAPPY: "(ᵔ ᴗ ᵔ)✧",
    Emotion.SAD: "(╥ ᴗ ╥)",
    Emotion.ERROR: "(× _ ×)",
    Emotion.GREETING: "(ノ◕ヮ◕)ノ",
    Emotion.SLEEPY: "(－ ᴗ －) zzZ",
}

TIME_KAOMOJI = {
    TimeOfDay.MORNING: "☀️",
    TimeOfDay.DAY: "🌤",
    TimeOfDay.EVENING: "🌙",
    TimeOfDay.NIGHT: "💤",
}

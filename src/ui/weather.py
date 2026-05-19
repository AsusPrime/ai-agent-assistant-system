from __future__ import annotations

from enum import Enum

import httpx


class WeatherState(str, Enum):
    CLEAR = "clear"
    HOT = "hot"
    COLD = "cold"
    RAIN = "rain"
    SNOW = "snow"
    CLOUDY = "cloudy"


def fetch_weather(timeout: float = 5.0) -> WeatherState:
    try:
        resp = httpx.get(
            "https://wttr.in/?format=j1",
            timeout=timeout,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        temp_c = int(current["temp_C"])
        code = int(current["weatherCode"])

        if code in (395, 371, 338, 335, 332, 329, 326, 323, 227, 179):
            return WeatherState.SNOW
        if code in (
            386,
            389,
            392,
            359,
            356,
            353,
            314,
            311,
            308,
            305,
            302,
            299,
            296,
            293,
            284,
            281,
            266,
            263,
            185,
            182,
            176,
            200,
        ):
            return WeatherState.RAIN
        if temp_c >= 30:
            return WeatherState.HOT
        if temp_c <= 0:
            return WeatherState.COLD
        if code in (122, 119):
            return WeatherState.CLOUDY

        return WeatherState.CLEAR

    except Exception:
        return WeatherState.CLEAR

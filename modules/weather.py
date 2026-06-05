"""
weather.py — weather section via Open-Meteo (forecast) and wttr.in (current).
No third-party dependencies: stdlib urllib only.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional

# WMO weather interpretation codes → human description
_WMO: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm + hail",
    99: "Thunderstorm + heavy hail",
}


def wmo_description(code: int) -> str:
    """Return a human-readable description for a WMO weather code."""
    return _WMO.get(code, f"WMO {code}")


def parse_forecast(daily: dict) -> List[dict]:
    """Parse an Open-Meteo daily forecast response into a list of day dicts.

    Each dict contains: date (str), description (str), hi (Optional[float]),
    lo (Optional[float]), rain (Optional[int]).
    """
    dates = daily.get("time", [])
    codes = daily.get("weathercode", [])
    hi_arr = daily.get("temperature_2m_max", [])
    lo_arr = daily.get("temperature_2m_min", [])
    rain_arr = daily.get("precipitation_probability_max", [])

    results = []
    for i, date_str in enumerate(dates):
        code = codes[i] if i < len(codes) else 0
        hi = hi_arr[i] if i < len(hi_arr) and hi_arr[i] is not None else None
        lo = lo_arr[i] if i < len(lo_arr) and lo_arr[i] is not None else None
        rain_raw = rain_arr[i] if i < len(rain_arr) and rain_arr[i] is not None else None
        rain = int(rain_raw) if rain_raw is not None else None

        results.append(
            {
                "date": date_str,
                "description": wmo_description(code),
                "hi": hi,
                "lo": lo,
                "rain": rain,
            }
        )
    return results


def parse_current(data: dict) -> Optional[dict]:
    """Parse a wttr.in ?format=j1 response into a current-conditions dict.

    Returns dict with keys: desc, temp_f, feels_f, wind_mph, humidity.
    Returns None if the response is malformed.
    """
    try:
        cur = (data.get("current_condition") or [{}])[0]
        weather_desc = cur.get("weatherDesc")
        if not isinstance(weather_desc, list):
            raise TypeError("weatherDesc is not a list")
        desc = (weather_desc[0] if weather_desc else {}).get("value", "")
        temp_f = cur.get("temp_F")
        feels_f = cur.get("FeelsLikeF")
        wind_mph = cur.get("windspeedMiles")
        humidity = cur.get("humidity")
        if not desc and temp_f is None:
            return None
        return {
            "desc": desc,
            "temp_f": temp_f,
            "feels_f": feels_f,
            "wind_mph": wind_mph,
            "humidity": humidity,
        }
    except (IndexError, KeyError, TypeError):
        return None


def _geocode(location: str) -> Optional[dict]:
    """Geocode a location string via Open-Meteo. Returns result dict or None."""
    city_only = location.split(",")[0].strip()
    params = urllib.parse.urlencode(
        {"name": city_only, "count": 1, "language": "en", "format": "json"}
    )
    req = urllib.request.Request(
        f"https://geocoding-api.open-meteo.com/v1/search?{params}",
        headers={"User-Agent": "updateme/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("results") or []
        return results[0] if results else None
    except Exception:
        return None


def _fetch_forecast(lat: float, lon: float, tz: str, days: int) -> Optional[dict]:
    """Fetch Open-Meteo daily forecast. Returns 'daily' dict or None."""
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "temperature_unit": "fahrenheit",
            "forecast_days": min(max(days, 1), 7),
            "timezone": tz,
        }
    )
    try:
        with urllib.request.urlopen(
            f"https://api.open-meteo.com/v1/forecast?{params}", timeout=10
        ) as resp:
            return json.loads(resp.read()).get("daily", {})
    except Exception:
        return None


def _fetch_current(location: str) -> Optional[dict]:
    """Fetch current conditions from wttr.in. Returns wttr.in JSON dict or None."""
    encoded = urllib.parse.quote(location)
    req = urllib.request.Request(
        f"https://wttr.in/{encoded}?format=j1",
        headers={"User-Agent": "updateme/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def show_weather(cfg) -> None:
    """Fetch and print the weather section."""
    from updateme import section_header, warn  # type: ignore

    location = cfg.location
    section_header(f"WEATHER — {location}")

    geo = _geocode(location)
    if geo is None:
        warn(f"Could not geocode location: {location}")
        return

    lat = geo["latitude"]
    lon = geo["longitude"]
    tz = geo.get("timezone", "UTC")

    daily = _fetch_forecast(lat, lon, tz, cfg.forecast_days)
    current_raw = _fetch_current(location)

    # Current conditions
    if current_raw:
        cur = parse_current(current_raw)
        if cur:
            print(
                f"  Now: {cur['desc']:<26}  {cur['temp_f']}°F"
                f"  (feels {cur['feels_f']}°F)"
                f"  Wind {cur['wind_mph']}mph"
                f"  Humidity {cur['humidity']}%"
            )

    print()
    print(f"  {'Date':<14} {'Condition':<28} {'High':>6} {'Low':>6} {'Rain':>6}")
    print(f"  {'-'*14} {'-'*28} {'-'*6} {'-'*6} {'-'*6}")

    if daily:
        days = parse_forecast(daily)
        for day in days:
            try:
                label = datetime.strptime(day["date"], "%Y-%m-%d").strftime("%a %b %-d")
            except Exception:
                label = day["date"]
            desc = day["description"][:27]
            hi = f"{day['hi']:.0f}" if day["hi"] is not None else "?"
            lo = f"{day['lo']:.0f}" if day["lo"] is not None else "?"
            rain = str(day["rain"]) if day["rain"] is not None else "?"
     
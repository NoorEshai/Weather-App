import os
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
_BASE = "https://api.openweathermap.org/data/2.5"


def _get(endpoint: str, params: dict) -> dict:
    params["appid"] = _API_KEY
    resp = requests.get(f"{_BASE}/{endpoint}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_current_weather(lat: float, lon: float) -> dict:
    """Fetch current conditions from OWM /weather."""
    data = _get("weather", {"lat": lat, "lon": lon, "units": "metric"})
    w = data["weather"][0]
    wind = data.get("wind", {})
    main = data["main"]
    return {
        "temperature_c": main["temp"],
        "feels_like_c": main["feels_like"],
        "temp_min_c": main["temp_min"],
        "temp_max_c": main["temp_max"],
        "humidity_pct": main["humidity"],
        "pressure_hpa": main["pressure"],
        "wind_speed_ms": wind.get("speed", 0),
        "wind_deg": wind.get("deg", 0),
        "wind_gust_ms": wind.get("gust"),
        "cloud_cover_pct": data["clouds"]["all"],
        "visibility_m": data.get("visibility"),
        "rain_1h_mm": data.get("rain", {}).get("1h", 0),
        "snow_1h_mm": data.get("snow", {}).get("1h", 0),
        "description": w["description"],
        "icon": w["icon"],
        "condition_id": w["id"],
        "city": data.get("name", ""),
        "sunrise": data["sys"].get("sunrise"),
        "sunset": data["sys"].get("sunset"),
        "dt": data["dt"],
        "timezone_offset": data.get("timezone", 0),
        "source": "openweathermap",
    }


def get_forecast(lat: float, lon: float) -> list[dict]:
    """Fetch 5-day / 3-hour forecast from OWM /forecast."""
    data = _get("forecast", {"lat": lat, "lon": lon, "units": "metric"})
    result = []
    for item in data["list"]:
        w = item["weather"][0]
        result.append({
            "dt": item["dt"],
            "datetime": datetime.utcfromtimestamp(item["dt"]).isoformat(),
            "temperature_c": item["main"]["temp"],
            "feels_like_c": item["main"]["feels_like"],
            "temp_min_c": item["main"]["temp_min"],
            "temp_max_c": item["main"]["temp_max"],
            "humidity_pct": item["main"]["humidity"],
            "pressure_hpa": item["main"]["pressure"],
            "wind_speed_ms": item["wind"]["speed"],
            "wind_deg": item["wind"].get("deg", 0),
            "cloud_cover_pct": item["clouds"]["all"],
            "description": w["description"],
            "icon": w["icon"],
            "condition_id": w["id"],
            "rain_3h_mm": item.get("rain", {}).get("3h", 0),
            "snow_3h_mm": item.get("snow", {}).get("3h", 0),
            "pop": item.get("pop", 0),
        })
    return result


def get_air_quality(lat: float, lon: float) -> dict:
    """Fetch air quality index from OWM /air_pollution."""
    resp = requests.get(
        "http://api.openweathermap.org/data/2.5/air_pollution",
        params={"lat": lat, "lon": lon, "appid": _API_KEY},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    item = data["list"][0]
    aqi = item["main"]["aqi"]
    labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    c = item["components"]
    return {
        "aqi": aqi,
        "aqi_label": labels.get(aqi, "Unknown"),
        "pm2_5": c.get("pm2_5"),
        "pm10": c.get("pm10"),
        "co": c.get("co"),
        "no2": c.get("no2"),
        "o3": c.get("o3"),
        "so2": c.get("so2"),
    }

import os
import logging

from backend import openweathermap_api as owm
from backend.parse_grib import grib_to_weather_dict
from backend.parse_daily import parse_daily_from_forecast

logger = logging.getLogger(__name__)

GRIB_PATH = os.getenv("GRIB_SAVE_PATH", "data/weather.grib")


# ---------------------------------------------------------------------------
# Current weather
# ---------------------------------------------------------------------------

def fetch_current(lat: float, lon: float, source: str = "auto") -> dict:
    """
    Return current weather for (lat, lon).

    source:
      "grib"        – ECMWF GRIB file only (raises if file missing)
      "openweather" – OpenWeatherMap only
      "auto"        – try GRIB first, fall back to OWM
    """
    if source == "grib":
        return _from_grib(lat, lon)
    if source == "openweather":
        return owm.get_current_weather(lat, lon)

    # auto
    if os.path.exists(GRIB_PATH):
        try:
            result = _from_grib(lat, lon)
            if result:
                return result
        except Exception as e:
            logger.warning(f"GRIB read failed, falling back to OWM: {e}")

    return owm.get_current_weather(lat, lon)


def _from_grib(lat: float, lon: float) -> dict:
    return grib_to_weather_dict(lat, lon, GRIB_PATH)


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

def fetch_forecast(lat: float, lon: float) -> dict:
    """
    Return a forecast dict with:
      - hourly: list of 3-hour OWM entries (40 entries / 5 days)
      - daily:  collapsed per-day summaries
    """
    hourly = owm.get_forecast(lat, lon)
    daily = parse_daily_from_forecast(hourly)
    return {"hourly": hourly, "daily": daily}


# ---------------------------------------------------------------------------
# Air quality
# ---------------------------------------------------------------------------

def fetch_air_quality(lat: float, lon: float) -> dict:
    try:
        return owm.get_air_quality(lat, lon)
    except Exception as e:
        logger.warning(f"Air quality fetch failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# Unified fetch (current + forecast + AQI in one call)
# ---------------------------------------------------------------------------

def fetch_all(lat: float, lon: float, source: str = "auto") -> dict:
    """Fetch everything needed for the full weather dashboard."""
    current = fetch_current(lat, lon, source)
    forecast = fetch_forecast(lat, lon)
    aqi = fetch_air_quality(lat, lon)
    return {
        "current": current,
        "hourly": forecast["hourly"],
        "daily": forecast["daily"],
        "air_quality": aqi,
    }

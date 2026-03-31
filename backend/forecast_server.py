"""
Forecast processing layer — enriches raw weather data with AI summaries,
overlay metadata, recommendations, and alerts before sending to the frontend.
"""

import logging

from backend.fetch_weather import fetch_all
from backend.location_lookup import resolve_location
from backend.overlays import get_overlay_from_weather
from backend.weather_ai import (
    get_weather_summary,
    get_recommendations,
    get_severe_weather_alert,
)

logger = logging.getLogger(__name__)


def build_weather_response(
    lat: float,
    lon: float,
    source: str = "auto",
    include_ai: bool = True,
) -> dict:
    """
    Core function called by API routes. Returns a fully enriched weather
    payload ready for the frontend.
    """
    # 1. Raw weather data
    data = fetch_all(lat, lon, source)
    current = data["current"]

    # 2. Reverse-geocode to get a city name (if not already in the weather data)
    location_info = resolve_location(lat=lat, lon=lon)
    city = (
        current.get("city")
        or (location_info.get("city") if location_info else None)
        or "Unknown"
    )

    # 3. Overlay + Apple Glass theme
    overlay = get_overlay_from_weather(current)

    # 4. AI enrichment (optional — skip if keys are missing or include_ai=False)
    summary = None
    recommendations = []
    alert = None
    if include_ai:
        try:
            summary = get_weather_summary(current, location=city)
        except Exception as e:
            logger.warning(f"AI summary skipped: {e}")
        try:
            recommendations = get_recommendations(current)
        except Exception as e:
            logger.warning(f"AI recommendations skipped: {e}")
        try:
            alert = get_severe_weather_alert(current)
        except Exception as e:
            logger.warning(f"AI alert skipped: {e}")

    # 5. Assemble final payload
    return {
        "location": {
            "lat": lat,
            "lon": lon,
            "city": city,
            "region": location_info.get("region", "") if location_info else "",
            "country": location_info.get("country", "") if location_info else "",
            "display_name": location_info.get("display_name", city) if location_info else city,
        },
        "current": current,
        "hourly": data["hourly"],
        "daily": data["daily"],
        "air_quality": data.get("air_quality", {}),
        "overlay": overlay,
        "ai": {
            "summary": summary,
            "recommendations": recommendations,
            "alert": alert,
        },
    }


def build_weather_response_from_name(
    name: str,
    source: str = "auto",
    include_ai: bool = True,
) -> dict | None:
    """
    Look up a city/place by name and return the enriched weather payload.
    Returns None if the place name cannot be resolved.
    """
    from backend.location_lookup import get_location_from_name
    loc = get_location_from_name(name)
    if not loc:
        return None
    return build_weather_response(
        lat=loc["lat"],
        lon=loc["lon"],
        source=source,
        include_ai=include_ai,
    )

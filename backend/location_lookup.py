import logging
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

logger = logging.getLogger(__name__)

_geolocator = Nominatim(user_agent="weather_app_v1", timeout=10)


def get_location_from_ip(ip: str = None) -> dict | None:
    """Geolocate via IP address using ip-api.com (free, no key needed)."""
    try:
        url = f"http://ip-api.com/json/{ip or ''}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("status") == "success":
            return {
                "lat": data["lat"],
                "lon": data["lon"],
                "city": data.get("city", "Unknown"),
                "region": data.get("regionName", ""),
                "country": data.get("country", ""),
                "timezone": data.get("timezone", "UTC"),
                "source": "ip",
            }
    except Exception as e:
        logger.warning(f"IP geolocation failed: {e}")
    return None


def get_location_from_coords(lat: float, lon: float) -> dict:
    """Reverse-geocode coordinates to a human-readable location."""
    try:
        location = _geolocator.reverse(f"{lat},{lon}", language="en")
        if location:
            addr = location.raw.get("address", {})
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("county")
                or "Unknown"
            )
            return {
                "lat": lat,
                "lon": lon,
                "city": city,
                "region": addr.get("state", ""),
                "country": addr.get("country", ""),
                "display_name": location.address,
                "source": "coords",
            }
    except GeocoderTimedOut:
        logger.warning("Reverse geocode timed out")
    except GeocoderUnavailable as e:
        logger.warning(f"Geocoder unavailable: {e}")
    except Exception as e:
        logger.warning(f"Reverse geocode failed: {e}")
    return {"lat": lat, "lon": lon, "city": "Unknown", "region": "", "country": "", "source": "coords"}


def get_location_from_name(name: str) -> dict | None:
    """Forward-geocode a place name to coordinates."""
    try:
        location = _geolocator.geocode(name, language="en")
        if location:
            addr = location.raw.get("address", {})
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or name
            )
            return {
                "lat": location.latitude,
                "lon": location.longitude,
                "city": city,
                "region": addr.get("state", ""),
                "country": addr.get("country", ""),
                "display_name": location.address,
                "source": "search",
            }
    except Exception as e:
        logger.warning(f"Geocode for '{name}' failed: {e}")
    return None


def resolve_location(
    lat: float = None,
    lon: float = None,
    name: str = None,
    ip: str = None,
) -> dict | None:
    """
    Resolve location using the best available input, in priority order:
      1. lat/lon coordinates (most precise)
      2. place name search
      3. IP geolocation (least precise)
    """
    if lat is not None and lon is not None:
        return get_location_from_coords(lat, lon)
    if name:
        return get_location_from_name(name)
    return get_location_from_ip(ip)

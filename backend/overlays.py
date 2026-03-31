"""
Overlay system — maps weather conditions + time of day to animated GIF
background filenames and Apple Glass UI theme tokens.

Overlay files live in:  frontend/public/overlays/<filename>.gif

Naming convention:      {condition}_{period}.gif
  condition: clear, partly_cloudy, cloudy, fog, drizzle, rain,
             heavy_rain, thunderstorm, snow, hail, wind, blizzard
  period:    dawn, morning, afternoon, evening, dusk, night
"""

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Time-of-day
# ---------------------------------------------------------------------------

def get_period(hour: int | None = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    if 5 <= hour < 7:
        return "dawn"
    if 7 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 20:
        return "evening"
    if 20 <= hour < 22:
        return "dusk"
    return "night"


# ---------------------------------------------------------------------------
# Condition mapping from OWM condition_id
# ---------------------------------------------------------------------------

def get_condition_key(condition_id: int, wind_ms: float = 0) -> str:
    """Map OWM condition_id to an overlay condition key."""
    cid = condition_id
    if 200 <= cid <= 232:
        return "thunderstorm"
    if 300 <= cid <= 321:
        return "drizzle"
    if cid in (500, 501):
        return "rain"
    if 502 <= cid <= 531:
        return "heavy_rain"
    if 600 <= cid <= 602:
        return "snow"
    if 611 <= cid <= 622:
        return "blizzard"
    if cid in (701, 741):
        return "fog"
    if 700 <= cid <= 781:
        return "fog"
    if cid == 800:
        return "clear"
    if cid == 801:
        return "partly_cloudy"
    if cid == 802:
        return "partly_cloudy"
    if 803 <= cid <= 804:
        return "cloudy"
    if wind_ms > 14:
        return "wind"
    return "clear"


# ---------------------------------------------------------------------------
# Apple Glass theme tokens
# ---------------------------------------------------------------------------

# Each condition gets a palette: background tint, glass blur amount,
# glass tint colour, and text/icon colour mode.
_GLASS_THEMES: dict[str, dict] = {
    "clear": {
        "morning":   {"bg_gradient": ["#FFD580", "#87CEEB"], "glass_tint": "rgba(255,255,255,0.18)", "blur": 24, "mode": "light"},
        "afternoon": {"bg_gradient": ["#42A5F5", "#90CAF9"], "glass_tint": "rgba(255,255,255,0.15)", "blur": 20, "mode": "light"},
        "evening":   {"bg_gradient": ["#FF8C42", "#FFD580"], "glass_tint": "rgba(255,200,100,0.15)", "blur": 22, "mode": "light"},
        "dawn":      {"bg_gradient": ["#FDA085", "#F6D365"], "glass_tint": "rgba(255,180,80,0.18)",  "blur": 28, "mode": "light"},
        "dusk":      {"bg_gradient": ["#C94B4B", "#4B134F"], "glass_tint": "rgba(120,40,80,0.22)",  "blur": 28, "mode": "dark"},
        "night":     {"bg_gradient": ["#0F2027", "#203A43"], "glass_tint": "rgba(10,20,40,0.30)",   "blur": 32, "mode": "dark"},
    },
    "partly_cloudy": {
        "morning":   {"bg_gradient": ["#B2EBF2", "#E0F2F1"], "glass_tint": "rgba(200,230,240,0.18)", "blur": 24, "mode": "light"},
        "afternoon": {"bg_gradient": ["#78909C", "#B0BEC5"], "glass_tint": "rgba(180,200,210,0.16)", "blur": 20, "mode": "light"},
        "evening":   {"bg_gradient": ["#FF7043", "#FFCCBC"], "glass_tint": "rgba(255,160,100,0.18)", "blur": 24, "mode": "light"},
        "dawn":      {"bg_gradient": ["#ECEFF1", "#CFD8DC"], "glass_tint": "rgba(200,210,220,0.20)", "blur": 26, "mode": "light"},
        "dusk":      {"bg_gradient": ["#546E7A", "#263238"], "glass_tint": "rgba(50,70,90,0.24)",   "blur": 28, "mode": "dark"},
        "night":     {"bg_gradient": ["#1A237E", "#283593"], "glass_tint": "rgba(20,30,80,0.30)",   "blur": 32, "mode": "dark"},
    },
    "cloudy": {
        "morning":   {"bg_gradient": ["#CFD8DC", "#90A4AE"], "glass_tint": "rgba(180,195,205,0.20)", "blur": 28, "mode": "light"},
        "afternoon": {"bg_gradient": ["#78909C", "#546E7A"], "glass_tint": "rgba(100,130,150,0.20)", "blur": 24, "mode": "light"},
        "evening":   {"bg_gradient": ["#546E7A", "#37474F"], "glass_tint": "rgba(60,80,100,0.22)",  "blur": 26, "mode": "dark"},
        "dawn":      {"bg_gradient": ["#B0BEC5", "#78909C"], "glass_tint": "rgba(150,170,185,0.20)", "blur": 28, "mode": "light"},
        "dusk":      {"bg_gradient": ["#37474F", "#263238"], "glass_tint": "rgba(40,60,75,0.24)",   "blur": 28, "mode": "dark"},
        "night":     {"bg_gradient": ["#263238", "#1C313A"], "glass_tint": "rgba(20,40,55,0.32)",   "blur": 32, "mode": "dark"},
    },
    "fog": {
        "_default": {"bg_gradient": ["#B0BEC5", "#ECEFF1"], "glass_tint": "rgba(200,210,215,0.25)", "blur": 40, "mode": "light"},
    },
    "drizzle": {
        "_default": {"bg_gradient": ["#546E7A", "#78909C"], "glass_tint": "rgba(80,110,130,0.22)", "blur": 30, "mode": "dark"},
    },
    "rain": {
        "_default": {"bg_gradient": ["#37474F", "#546E7A"], "glass_tint": "rgba(50,80,100,0.24)", "blur": 28, "mode": "dark"},
    },
    "heavy_rain": {
        "_default": {"bg_gradient": ["#263238", "#37474F"], "glass_tint": "rgba(30,55,75,0.28)", "blur": 32, "mode": "dark"},
    },
    "thunderstorm": {
        "_default": {"bg_gradient": ["#1C1C2E", "#2D2D44"], "glass_tint": "rgba(20,20,50,0.35)", "blur": 36, "mode": "dark"},
    },
    "snow": {
        "_default": {"bg_gradient": ["#E8F4FD", "#C5D8ED"], "glass_tint": "rgba(200,220,240,0.22)", "blur": 30, "mode": "light"},
    },
    "blizzard": {
        "_default": {"bg_gradient": ["#ECEFF1", "#B0BEC5"], "glass_tint": "rgba(180,195,210,0.28)", "blur": 40, "mode": "light"},
    },
    "wind": {
        "_default": {"bg_gradient": ["#B0BEC5", "#78909C"], "glass_tint": "rgba(150,170,185,0.20)", "blur": 24, "mode": "light"},
    },
    "hail": {
        "_default": {"bg_gradient": ["#455A64", "#546E7A"], "glass_tint": "rgba(70,90,105,0.24)", "blur": 30, "mode": "dark"},
    },
}

# All unique overlay GIF filenames the frontend needs
ALL_OVERLAYS: list[str] = [
    f"{cond}_{period}.gif"
    for cond in [
        "clear", "partly_cloudy", "cloudy", "fog",
        "drizzle", "rain", "heavy_rain", "thunderstorm",
        "snow", "blizzard", "wind", "hail",
    ]
    for period in ["dawn", "morning", "afternoon", "evening", "dusk", "night"]
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_overlay(
    condition_id: int,
    wind_ms: float = 0,
    hour: int | None = None,
) -> dict:
    """
    Return overlay metadata for the given weather state:
      - filename:   GIF filename (relative to /overlays/)
      - condition:  condition key string
      - period:     time-of-day string
      - theme:      Apple Glass theme tokens dict
    """
    condition = get_condition_key(condition_id, wind_ms)
    period = get_period(hour)

    theme_map = _GLASS_THEMES.get(condition, {})
    theme = (
        theme_map.get(period)
        or theme_map.get("_default")
        or _GLASS_THEMES["clear"]["afternoon"]
    )

    return {
        "filename": f"{condition}_{period}.gif",
        "condition": condition,
        "period": period,
        "theme": theme,
    }


def get_overlay_from_weather(weather: dict) -> dict:
    """Convenience wrapper that accepts a full weather dict."""
    cond_id = weather.get("condition_id", 800)
    wind_ms = weather.get("wind_speed_ms", 0)
    # Use local time derived from timezone_offset if available
    tz_offset = weather.get("timezone_offset", 0)
    dt = weather.get("dt")
    if dt:
        local_ts = dt + tz_offset
        hour = datetime.utcfromtimestamp(local_ts).hour
    else:
        hour = None
    return get_overlay(cond_id, wind_ms, hour)

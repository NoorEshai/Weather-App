from collections import defaultdict
from datetime import datetime, timezone


def parse_daily_from_forecast(hourly: list[dict]) -> list[dict]:
    """
    Collapse a list of 3-hourly OWM forecast entries into per-day summaries.
    Each day picks the worst/most representative condition (lowest condition_id
    in the Thunderstorm/Rain/Snow groups, else the most frequent).
    """
    days: dict[str, list[dict]] = defaultdict(list)
    for entry in hourly:
        date = datetime.utcfromtimestamp(entry["dt"]).strftime("%Y-%m-%d")
        days[date].append(entry)

    result = []
    for date in sorted(days):
        entries = days[date]
        temps = [e["temperature_c"] for e in entries]
        feels = [e["feels_like_c"] for e in entries]
        humidities = [e["humidity_pct"] for e in entries]
        winds = [e["wind_speed_ms"] for e in entries]
        pops = [e.get("pop", 0) for e in entries]
        rain = sum(e.get("rain_3h_mm", 0) for e in entries)
        snow = sum(e.get("snow_3h_mm", 0) for e in entries)
        cloud = [e["cloud_cover_pct"] for e in entries]

        # Pick dominant condition: prefer severe (thunder/rain/snow) over fair
        cond_ids = [e["condition_id"] for e in entries]
        # Severity: lower OWM group wins (2xx > 3xx > 5xx > 6xx > 7xx > 8xx)
        dominant_id = min(cond_ids, key=lambda x: (x // 100, x))
        dominant_entry = next(e for e in entries if e["condition_id"] == dominant_id)

        # Pick representative daytime icon (prefer non-night icons)
        day_entries = [e for e in entries if not e.get("icon", "").endswith("n")]
        icon_entry = day_entries[len(day_entries) // 2] if day_entries else dominant_entry

        result.append({
            "date": date,
            "temp_min_c": round(min(temps), 1),
            "temp_max_c": round(max(temps), 1),
            "temp_avg_c": round(sum(temps) / len(temps), 1),
            "feels_like_min_c": round(min(feels), 1),
            "feels_like_max_c": round(max(feels), 1),
            "humidity_pct": round(sum(humidities) / len(humidities), 1),
            "wind_speed_max_ms": round(max(winds), 2),
            "wind_speed_avg_ms": round(sum(winds) / len(winds), 2),
            "cloud_cover_pct": round(sum(cloud) / len(cloud), 1),
            "pop": round(max(pops), 2),
            "rain_mm": round(rain, 2),
            "snow_mm": round(snow, 2),
            "description": dominant_entry["description"],
            "icon": icon_entry["icon"],
            "condition_id": dominant_id,
        })

    return result


def get_time_of_day(dt: int | None = None) -> str:
    """
    Return a time-of-day label for the given Unix timestamp (UTC).
    Labels match the overlay naming convention: dawn, morning, afternoon,
    evening, dusk, night.
    """
    if dt is None:
        from datetime import datetime
        hour = datetime.now().hour
    else:
        hour = datetime.utcfromtimestamp(dt).hour

    if 5 <= hour < 7:
        return "dawn"
    elif 7 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 20:
        return "evening"
    elif 20 <= hour < 22:
        return "dusk"
    else:
        return "night"

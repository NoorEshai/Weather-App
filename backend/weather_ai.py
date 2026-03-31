import json
import logging
import os

logger = logging.getLogger(__name__)


def _client():
    """Return (OpenAI client, model_name) using available API key.
    Keys are read lazily so load_dotenv() in main.py has already run."""
    try:
        from openai import OpenAI
    except ImportError:
        return None, None

    openai_key = os.getenv("OPENAI_API_KEY", "")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")

    if openai_key:
        return OpenAI(api_key=openai_key), "gpt-4o-mini"
    if deepseek_key:
        return OpenAI(
            api_key=deepseek_key,
            base_url="https://api.deepseek.com",
        ), "deepseek-chat"
    return None, None


def _chat(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str | None:
    client, model = _client()
    if not client:
        return None
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI request failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_weather_summary(weather: dict, location: str = "") -> str:
    """
    2-3 sentence natural-language summary of current conditions.
    Falls back to a simple template if AI is unavailable.
    """
    loc_str = location or "the user's location"
    prompt = (
        f"You are a friendly weather assistant. Write a 2-3 sentence conversational "
        f"summary of the weather in {loc_str} based on this data. "
        f"Include what to expect and one practical tip. Keep it under 60 words.\n\n"
        f"Weather: {json.dumps(weather, default=str)}"
    )
    result = _chat(prompt, max_tokens=120)
    return result if result else _fallback_summary(weather)


def get_recommendations(weather: dict) -> list[str]:
    """
    Return 3 short clothing/activity recommendations as a list of strings.
    Falls back to rule-based recommendations if AI is unavailable.
    """
    prompt = (
        f"Given this weather data, list exactly 3 short practical recommendations "
        f"(clothing, activities, precautions). "
        f"Respond with a JSON array of strings only, no explanation.\n\n"
        f"Weather: {json.dumps(weather, default=str)}"
    )
    raw = _chat(prompt, max_tokens=150, temperature=0.5)
    if raw:
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip().strip("```json").strip("```").strip()
            recs = json.loads(cleaned)
            if isinstance(recs, list):
                return [str(r) for r in recs[:3]]
        except (json.JSONDecodeError, ValueError):
            pass
    return _fallback_recommendations(weather)


def get_severe_weather_alert(weather: dict) -> str | None:
    """
    Return a short alert string if conditions are severe, else None.
    """
    cond_id = weather.get("condition_id", 800)
    wind = weather.get("wind_speed_ms", 0)
    temp = weather.get("temperature_c", 20)
    vis = weather.get("visibility_m", 10000)

    is_severe = (
        cond_id < 300  # thunderstorm
        or (500 <= cond_id < 520 and weather.get("rain_1h_mm", 0) > 10)
        or wind > 17  # ~60 km/h
        or temp < -10
        or temp > 40
        or (vis is not None and vis < 200)
    )

    if not is_severe:
        return None

    prompt = (
        f"Write a single short safety alert (under 20 words) for these severe weather "
        f"conditions. Be direct and actionable.\n\n"
        f"Weather: {json.dumps(weather, default=str)}"
    )
    raw = _chat(prompt, max_tokens=60, temperature=0.3)
    return raw if raw else _fallback_alert(weather)


# ---------------------------------------------------------------------------
# Fallbacks (no AI key required)
# ---------------------------------------------------------------------------

def _fallback_summary(weather: dict) -> str:
    temp = weather.get("temperature_c", "?")
    desc = weather.get("description", "conditions unknown")
    wind = weather.get("wind_speed_ms", 0)
    humidity = weather.get("humidity_pct", 0)
    return (
        f"Currently {temp}°C with {desc}. "
        f"Wind at {wind} m/s and humidity {humidity}%."
    )


def _fallback_recommendations(weather: dict) -> list[str]:
    recs = []
    temp = weather.get("temperature_c", 20)
    rain = weather.get("rain_1h_mm", 0) or weather.get("precipitation_mm", 0)
    wind = weather.get("wind_speed_ms", 0)
    cond_id = weather.get("condition_id", 800)

    if temp <= 0:
        recs.append("Wear a heavy coat, hat, and gloves")
    elif temp < 10:
        recs.append("Wear a warm jacket and layers")
    elif temp < 20:
        recs.append("A light jacket should do the trick")
    else:
        recs.append("Light clothing is fine")

    if 200 <= cond_id < 300:
        recs.append("Stay indoors — thunderstorms are active")
    elif rain > 0 or (300 <= cond_id < 600):
        recs.append("Bring an umbrella or rain jacket")
    else:
        recs.append("Great conditions for outdoor activities")

    if wind > 10:
        recs.append("It's quite windy — secure loose items")
    elif temp > 30:
        recs.append("Stay hydrated and seek shade midday")
    else:
        recs.append("Enjoy your day!")

    return recs[:3]


def _fallback_alert(weather: dict) -> str:
    cond_id = weather.get("condition_id", 800)
    wind = weather.get("wind_speed_ms", 0)
    temp = weather.get("temperature_c", 20)

    if cond_id < 300:
        return "Severe thunderstorm — stay indoors and away from windows."
    if wind > 17:
        return "High winds — avoid driving and secure outdoor objects."
    if temp < -10:
        return "Extreme cold — limit time outdoors and dress in layers."
    if temp > 40:
        return "Extreme heat — stay hydrated and avoid direct sunlight."
    return "Severe weather conditions — exercise caution."

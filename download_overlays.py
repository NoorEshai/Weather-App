"""
Download animated weather GIF overlays from Giphy's public CDN.
These are hand-curated Giphy IDs that match each weather condition + time of day.

Run once before starting the app:
  python download_overlays.py

GIFs are saved to: frontend/public/overlays/
"""

import os
import urllib.request
import sys

DEST = os.path.join("frontend", "public", "overlays")
os.makedirs(DEST, exist_ok=True)

# Curated Giphy IDs per (condition, period).
# Format: "condition_period" -> Giphy media ID
# Giphy direct media URL: https://media.giphy.com/media/{id}/giphy.gif
GIPHY_IDS = {
    # Clear sky
    "clear_dawn":        "l0MYAn0uKFiEaGilO",  # soft sunrise pink sky
    "clear_morning":     "3orieTFN6jkRJPPvUA",  # bright blue sky timelapse
    "clear_afternoon":   "xTiTnHXbRoaZ1hBqfS",  # sunny clear sky
    "clear_evening":     "l0MYGb1RuuYXg0l4c",   # golden hour
    "clear_dusk":        "3o6Zt4HU9uwXmXSAuI",  # purple dusk sky
    "clear_night":       "xT9IgzoKnwFNmISR8I",  # starry night sky

    # Partly cloudy
    "partly_cloudy_dawn":      "l0MYAn0uKFiEaGilO",
    "partly_cloudy_morning":   "3orieTFN6jkRJPPvUA",
    "partly_cloudy_afternoon": "l0HlBO7eyXzSZkJri",  # puffy clouds
    "partly_cloudy_evening":   "l0MYGb1RuuYXg0l4c",
    "partly_cloudy_dusk":      "3o6Zt4HU9uwXmXSAuI",
    "partly_cloudy_night":     "xT9IgzoKnwFNmISR8I",

    # Cloudy
    "cloudy_dawn":      "xT9IgG4uHPkFrsI7T2",   # grey cloudy sky
    "cloudy_morning":   "xT9IgG4uHPkFrsI7T2",
    "cloudy_afternoon": "l0HlBO7eyXzSZkJri",
    "cloudy_evening":   "3o6Zt4HU9uwXmXSAuI",
    "cloudy_dusk":      "xT9IgG4uHPkFrsI7T2",
    "cloudy_night":     "xT9IgzoKnwFNmISR8I",

    # Fog / Mist
    "fog_dawn":      "26BRv0ThflsHCqDrG",  # misty fog
    "fog_morning":   "26BRv0ThflsHCqDrG",
    "fog_afternoon": "26BRv0ThflsHCqDrG",
    "fog_evening":   "26BRv0ThflsHCqDrG",
    "fog_dusk":      "26BRv0ThflsHCqDrG",
    "fog_night":     "26BRv0ThflsHCqDrG",

    # Drizzle
    "drizzle_dawn":      "l0HlNQ03J5JxX6ltq",  # light rain drops
    "drizzle_morning":   "l0HlNQ03J5JxX6ltq",
    "drizzle_afternoon": "l0HlNQ03J5JxX6ltq",
    "drizzle_evening":   "l0HlNQ03J5JxX6ltq",
    "drizzle_dusk":      "l0HlNQ03J5JxX6ltq",
    "drizzle_night":     "l0HlNQ03J5JxX6ltq",

    # Rain
    "rain_dawn":      "3oEjHAUOqG3lSS0f1C",  # rain on window
    "rain_morning":   "3oEjHAUOqG3lSS0f1C",
    "rain_afternoon": "3oEjHAUOqG3lSS0f1C",
    "rain_evening":   "3oEjHAUOqG3lSS0f1C",
    "rain_dusk":      "3oEjHAUOqG3lSS0f1C",
    "rain_night":     "3oEjHAUOqG3lSS0f1C",

    # Heavy rain
    "heavy_rain_dawn":      "3oKIPnbKgN7TPJD3Uc",  # heavy downpour
    "heavy_rain_morning":   "3oKIPnbKgN7TPJD3Uc",
    "heavy_rain_afternoon": "3oKIPnbKgN7TPJD3Uc",
    "heavy_rain_evening":   "3oKIPnbKgN7TPJD3Uc",
    "heavy_rain_dusk":      "3oKIPnbKgN7TPJD3Uc",
    "heavy_rain_night":     "3oKIPnbKgN7TPJD3Uc",

    # Thunderstorm
    "thunderstorm_dawn":      "l0HlQotnBBTVu6FIA",  # lightning storm
    "thunderstorm_morning":   "l0HlQotnBBTVu6FIA",
    "thunderstorm_afternoon": "l0HlQotnBBTVu6FIA",
    "thunderstorm_evening":   "l0HlQotnBBTVu6FIA",
    "thunderstorm_dusk":      "l0HlQotnBBTVu6FIA",
    "thunderstorm_night":     "l0HlQotnBBTVu6FIA",

    # Snow
    "snow_dawn":      "3og0INyCmHlApMjO9q",   # snowfall
    "snow_morning":   "3og0INyCmHlApMjO9q",
    "snow_afternoon": "3og0INyCmHlApMjO9q",
    "snow_evening":   "3og0INyCmHlApMjO9q",
    "snow_dusk":      "3og0INyCmHlApMjO9q",
    "snow_night":     "3og0INyCmHlApMjO9q",

    # Blizzard
    "blizzard_dawn":      "3oKIPnAiaMCws1ZJeA",  # blizzard / heavy snow
    "blizzard_morning":   "3oKIPnAiaMCws1ZJeA",
    "blizzard_afternoon": "3oKIPnAiaMCws1ZJeA",
    "blizzard_evening":   "3oKIPnAiaMCws1ZJeA",
    "blizzard_dusk":      "3oKIPnAiaMCws1ZJeA",
    "blizzard_night":     "3oKIPnAiaMCws1ZJeA",

    # Wind
    "wind_dawn":      "xT9IgELHh7GKQKFPK8",   # blowing leaves / wind
    "wind_morning":   "xT9IgELHh7GKQKFPK8",
    "wind_afternoon": "xT9IgELHh7GKQKFPK8",
    "wind_evening":   "xT9IgELHh7GKQKFPK8",
    "wind_dusk":      "xT9IgELHh7GKQKFPK8",
    "wind_night":     "xT9IgELHh7GKQKFPK8",

    # Hail
    "hail_dawn":      "3oKIPnbKgN7TPJD3Uc",
    "hail_morning":   "3oKIPnbKgN7TPJD3Uc",
    "hail_afternoon": "3oKIPnbKgN7TPJD3Uc",
    "hail_evening":   "3oKIPnbKgN7TPJD3Uc",
    "hail_dusk":      "3oKIPnbKgN7TPJD3Uc",
    "hail_night":     "3oKIPnbKgN7TPJD3Uc",
}


def download(key: str, giphy_id: str) -> bool:
    dest_path = os.path.join(DEST, f"{key}.gif")
    if os.path.exists(dest_path):
        print(f"  skip  {key}.gif  (already exists)")
        return True

    url = f"https://media.giphy.com/media/{giphy_id}/giphy.gif"
    try:
        print(f"  fetch {key}.gif  from Giphy …", end=" ", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        print(f"OK ({len(data)//1024} KB)")
        return True
    except Exception as e:
        print(f"FAILED — {e}")
        return False


def main():
    print(f"Downloading {len(GIPHY_IDS)} weather overlay GIFs to {DEST}/\n")
    failed = []
    for key, gid in GIPHY_IDS.items():
        if not download(key, gid):
            failed.append(key)

    print(f"\nDone. {len(GIPHY_IDS) - len(failed)}/{len(GIPHY_IDS)} downloaded.")
    if failed:
        print("Failed:", ", ".join(failed))
        print("You can manually replace these in frontend/public/overlays/")
        sys.exit(1)


if __name__ == "__main__":
    main()

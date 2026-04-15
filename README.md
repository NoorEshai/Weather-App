# Atmosphere — AI-Powered Weather App

A full-stack weather application that combines real-time meteorological data with AI-generated insights and a dynamic glassmorphism UI. Built with a Python/FastAPI backend, React frontend, and dual weather data sources including ECMWF GRIB atmospheric models.

---

## Features

- **Dual weather data sources** — automatically selects between ECMWF GRIB atmospheric model data and OpenWeatherMap API, with graceful fallback
- **AI-powered summaries** — natural language weather descriptions, clothing recommendations, and severe weather alerts via OpenAI GPT-4o-mini or DeepSeek, with rule-based fallbacks when no key is present
- **Dynamic Glass UI** — 72 animated background overlays (12 weather conditions × 6 times of day) with Apple-style glassmorphism theme tokens served from the API
- **5-day forecast** — hourly and daily aggregated forecasts with precipitation probability, min/max temps, and dominant condition detection
- **Air quality index** — real-time AQI with PM2.5, PM10, O3, NO2, CO components
- **IP + coordinate + name geolocation** — resolves location from browser GPS, city name search, or automatic IP detection
- **Community reports** — users can submit and browse hyperlocal weather observations, backed by SQLite
- **Photo uploads** — community weather photo uploads via a dedicated Express.js server

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, React Router v6, Leaflet / React-Leaflet, Tailwind CSS |
| **Backend** | Python 3.12, FastAPI, Uvicorn (ASGI) |
| **Weather data** | OpenWeatherMap REST API + ECMWF GRIB via cfgrib / xarray |
| **AI** | OpenAI `gpt-4o-mini` · DeepSeek `deepseek-chat` (rule-based fallback) |
| **Geolocation** | ip-api.com (IP lookup) · Nominatim / geopy (forward & reverse geocoding) |
| **Database** | SQLite (community reports) |
| **Upload server** | Node.js, Express.js, Multer |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              React Frontend (: 3000)         │
│  Map · Hourly Scroll · Glass Overlay · Feed  │
└──────────────────┬──────────────────────────┘
                   │ REST
┌──────────────────▼──────────────────────────┐
│           FastAPI Backend (: 8000)           │
│                                             │
│  ┌─────────────┐   ┌─────────────────────┐  │
│  │forecast_    │   │   weather_ai.py     │  │
│  │server.py    │   │  OpenAI / DeepSeek  │  │
│  │(enrichment) │   └─────────────────────┘  │
│  └──────┬──────┘                            │
│         │                                   │
│  ┌──────▼──────┐   ┌─────────────────────┐  │
│  │fetch_       │   │   overlays.py       │  │
│  │weather.py   │   │  Glass theme tokens │  │
│  └──┬──────┬───┘   └─────────────────────┘  │
│     │      │                                │
│  GRIB    OWM API                            │
└─────────────────────────────────────────────┘
                   │ multipart
┌──────────────────▼──────────────────────────┐
│        Express Upload Server (: 3001)        │
│        Community photo storage               │
└─────────────────────────────────────────────┘
```

### Key design decisions

- **Source auto-selection** — `fetch_weather.py` tries the local ECMWF GRIB file first (higher resolution atmospheric data) and falls back to OpenWeatherMap if the file is absent or unreadable, without any change to the API contract.
- **Lazy AI client** — API keys are read from environment at call time, not at import time, so `load_dotenv()` always runs first regardless of module load order.
- **Overlay tokens over static CSS** — the `/api/overlay` endpoint returns gradient colours, blur radius, and tint values as JSON so the frontend can drive glassmorphism dynamically from weather state without hardcoding any visual logic.
- **Enrichment layer** — `forecast_server.py` separates data fetching from response assembly, keeping route handlers thin and the enrichment pipeline independently testable.

---

## Project Structure

```
Weather-App/
├── backend/
│   ├── main.py               # FastAPI app, CORS, all route definitions
│   ├── forecast_server.py    # Enrichment: weather + AI + overlay → payload
│   ├── fetch_weather.py      # GRIB / OWM source selector + unified fetch
│   ├── parse_grib.py         # cfgrib/xarray GRIB reader, nearest grid-point
│   ├── openweathermap_api.py # Current weather, forecast, AQI
│   ├── parse_daily.py        # 3-hourly → daily aggregation + time-of-day util
│   ├── location_lookup.py    # IP geolocation, forward/reverse geocoding
│   ├── weather_ai.py         # AI summaries, recommendations, alerts
│   ├── overlays.py           # Condition → GIF filename + Glass theme tokens
│   ├── community.py          # SQLite CRUD for community weather reports
│   └── auth.py               # Optional API key authentication dependency
├── frontend/
│   ├── src/                  # React application source
│   └── public/overlays/      # 72 animated GIF weather backgrounds
├── server/
│   └── index.cjs             # Express upload server (port 3001)
├── data/
│   ├── community.db          # SQLite database
│   └── weather.grib          # ECMWF GRIB atmospheric data (local, not in git)
└── download_overlays.py      # One-time overlay GIF downloader
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- An [OpenWeatherMap API key](https://openweathermap.org/api) (free tier works)
- Optional: OpenAI or DeepSeek key for AI features

### 1. Python backend

```bash
python -m venv venv
source venv/Scripts/activate      # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:
```env
OPENWEATHER_API_KEY=your_openweather_key
OPENAI_API_KEY=your_openai_key        # or use DEEPSEEK_API_KEY
PORT=8000
COMMUNITY_DB=data/community.db
GRIB_SAVE_PATH=data/weather.grib
```

### 2. Frontend

```bash
cd frontend && npm install
```

Create `frontend/.env`:
```env
REACT_APP_API_BASE=http://127.0.0.1:8000
```

### 3. Overlay GIFs (one-time)

```bash
python download_overlays.py
```

### 4. Run

```bash
# FastAPI backend — port 8000
uvicorn backend.main:app --reload --port 8000

# Upload server — port 3001
node server/index.cjs

# React dev server — port 3000
cd frontend && npm start
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/weather?lat=&lon=` | Full payload: current + forecast + AI + overlay |
| `GET` | `/api/weather?name=London` | Same, resolved by city name |
| `GET` | `/api/weather?ip=` | Same, resolved by IP (auto-detects if omitted) |
| `GET` | `/api/weather/current` | Current conditions only |
| `GET` | `/api/weather/forecast` | 5-day hourly + daily |
| `GET` | `/api/weather/aqi` | Air quality index + components |
| `GET` | `/api/overlay?condition_id=&hour=` | GIF filename + Apple Glass theme |
| `GET` | `/api/overlay/list` | All 72 overlay filenames |
| `GET` | `/api/location?name=` | Geocode a place name |
| `POST` | `/api/community/reports` | Submit a community weather report |
| `GET` | `/api/community/reports?lat=&lon=` | Nearby community reports |
| `POST` | `/api/upload/photo` | Upload a community weather photo |
| `GET` | `/api/health` | Health check |

### Example response — `/api/weather?name=New York`

```json
{
  "location": { "city": "New York", "lat": 40.71, "lon": -74.01 },
  "current": {
    "temperature_c": 18.4,
    "humidity_pct": 62,
    "wind_speed_ms": 4.1,
    "description": "scattered clouds",
    "source": "openweathermap"
  },
  "daily": [
    { "date": "2025-11-15", "temp_min_c": 12.1, "temp_max_c": 20.3, "pop": 0.1 }
  ],
  "overlay": {
    "filename": "partly_cloudy_afternoon.gif",
    "theme": {
      "bg_gradient": ["#78909C", "#B0BEC5"],
      "glass_tint": "rgba(180,200,210,0.16)",
      "blur": 20,
      "mode": "light"
    }
  },
  "ai": {
    "summary": "A comfortable afternoon in New York with scattered clouds and a light breeze. Great weather for being outside — a light jacket is all you'll need.",
    "recommendations": ["Light jacket recommended", "Good conditions for outdoor activities", "No rain expected today"],
    "alert": null
  }
}
```

---

## Overlay System

The dynamic overlay system maps any weather state to a specific animated background and glassmorphism theme.

**72 combinations** = 12 weather conditions × 6 time-of-day periods:

| Conditions | Periods |
|---|---|
| clear, partly cloudy, cloudy, fog | dawn, morning, afternoon |
| drizzle, rain, heavy rain, thunderstorm | evening, dusk, night |
| snow, blizzard, wind, hail | |

The API returns theme tokens directly so the frontend renders glassmorphism without any hardcoded visual logic:

```css
.glass-card {
  backdrop-filter: blur(var(--blur)) saturate(180%);
  -webkit-backdrop-filter: blur(var(--blur)) saturate(180%);
  background-color: var(--glass-tint);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
```

---

## Roadmap

- [ ] React UI — home screen, hourly scroll, 5-day cards, map view, community feed
- [ ] Live GRIB refresh — scheduled background task using `cdsapi` to pull latest ECMWF data
- [ ] Radar map overlay — OWM precipitation tile layer on the Leaflet map
- [ ] Hourly chart — temperature and precipitation sparkline (Recharts)
- [ ] Unit toggle — °C / °F, m/s / mph, mm / in
- [ ] Saved locations — localStorage-persisted favourite cities
- [ ] Push notifications — severe weather alerts via Web Push API
- [ ] PWA — service worker with offline-cached last-known weather
- [ ] JWT auth — per-user tokens replacing the shared API key
- [ ] Rate limiting — per-IP throttle middleware on weather endpoints

---

## License

MIT

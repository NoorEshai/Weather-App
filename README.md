# Weather App

A full-stack weather application with an AI-powered summary, animated Apple Glass overlays, ECMWF GRIB support, and a community reporting system.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router, Leaflet, Tailwind CSS |
| Backend | FastAPI (Python), Uvicorn |
| Weather data | OpenWeatherMap API + ECMWF GRIB (cfgrib/xarray) |
| AI | OpenAI `gpt-4o-mini` or DeepSeek (falls back to rule-based) |
| Community DB | SQLite |
| Upload server | Express.js (Node) |

---

## Project Structure

```
Weather-App/
├── backend/
│   ├── main.py             # FastAPI app + all routes
│   ├── fetch_weather.py    # GRIB vs OWM selector
│   ├── parse_grib.py       # ECMWF GRIB reader (cfgrib/xarray)
│   ├── openweathermap_api.py
│   ├── parse_daily.py      # 3-hourly → daily collapse
│   ├── location_lookup.py  # IP / name / coords geolocation
│   ├── weather_ai.py       # AI summary, recommendations, alerts
│   ├── overlays.py         # Condition → GIF + Apple Glass theme tokens
│   ├── forecast_server.py  # Enrichment layer (weather + AI + overlay)
│   ├── community.py        # SQLite community reports
│   ├── auth.py             # Optional API key auth
│   └── .env                # API keys (never commit this)
├── frontend/
│   ├── src/                # React source
│   └── public/overlays/    # Animated GIF backgrounds (72 files)
├── server/
│   └── index.cjs           # Express upload server (port 3001)
├── data/
│   ├── community.db
│   └── weather.grib        # ECMWF GRIB file (not in git)
├── download_overlays.py    # One-time GIF downloader
└── requirments.txt         # Python deps (pip install -r requirments.txt)
```

---

## Setup

### 1. Python backend

```bash
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate
pip install -r requirments.txt
```

Set keys in `backend/.env`:
```
OPENWEATHER_API_KEY=your_key
OPENAI_API_KEY=your_key        # or DEEPSEEK_API_KEY
PORT=8000
COMMUNITY_DB=data/community.db
GRIB_SAVE_PATH=data/weather.grib
```

### 2. Frontend

```bash
cd frontend
npm install
```

`frontend/.env` (plain text, no PowerShell):
```
REACT_APP_API_BASE=http://127.0.0.1:8000
```

### 3. Download overlay GIFs (one-time)

```bash
python download_overlays.py
```

---

## Running

```bash
# Terminal 1 — FastAPI backend (port 8000)
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Upload server (port 3001)
node server/index.cjs

# Terminal 3 — React dev server (port 3000)
cd frontend && npm start
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/weather?lat=&lon=` | Full weather payload (current + forecast + AI + overlay) |
| GET | `/api/weather?name=London` | Same but by city name |
| GET | `/api/weather?ip=` | Same but by IP (omit for auto-detect) |
| GET | `/api/weather/current` | Current conditions only |
| GET | `/api/weather/forecast` | 5-day hourly + daily |
| GET | `/api/weather/aqi` | Air quality index |
| GET | `/api/overlay?condition_id=&hour=` | Overlay filename + Glass theme |
| GET | `/api/overlay/list` | All 72 overlay filenames |
| GET | `/api/location?name=` | Geocode a place |
| POST | `/api/community/reports` | Submit a weather report |
| GET | `/api/community/reports?lat=&lon=` | Nearby community reports |
| POST | `/api/upload/photo` | Upload a community photo |
| GET | `/api/health` | Health check |

---

## Overlay System

72 animated GIFs cover every combination of:
- **12 conditions:** clear, partly_cloudy, cloudy, fog, drizzle, rain, heavy_rain, thunderstorm, snow, blizzard, wind, hail
- **6 time periods:** dawn, morning, afternoon, evening, dusk, night

The `/api/weather` response includes an `overlay` object with:
```json
{
  "filename": "rain_evening.gif",
  "condition": "rain",
  "period": "evening",
  "theme": {
    "bg_gradient": ["#37474F", "#546E7A"],
    "glass_tint": "rgba(50,80,100,0.24)",
    "blur": 28,
    "mode": "dark"
  }
}
```

Apply the Apple Glass effect in CSS:
```css
.glass-card {
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  background-color: var(--glass-tint);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
```

---

## Future Updates

### High priority
- [ ] **Frontend `src/`** — Build React UI: home screen, hourly scroll, 5-day forecast, map view, community feed
- [ ] **Live GRIB refresh** — Cron job or background task to fetch the latest ECMWF GRIB from CDS API (`cdsapi`) on a schedule
- [ ] **Push notifications** — Severe weather alerts via Web Push or a mobile wrapper
- [ ] **Auth hardening** — Replace the single shared `AUTH_API_KEY` with per-user JWT tokens

### Medium priority
- [ ] **Hourly chart** — Temperature/precipitation sparkline using Recharts or Chart.js
- [ ] **Unit toggle** — °C / °F, m/s / mph, mm / in
- [ ] **Saved locations** — localStorage or backend-persisted favourites
- [ ] **Community photo moderation** — Flag/remove inappropriate uploads
- [ ] **GRIB multi-step forecasts** — Parse time dimension to serve ECMWF hourly forecasts instead of a single snapshot
- [ ] **Radar map overlay** — OWM tile layer on the Leaflet map

### Low priority / ideas
- [ ] **PWA support** — Service worker + offline cached last weather
- [ ] **Accessibility** — ARIA labels, keyboard navigation, reduced-motion for GIF overlays
- [ ] **Dark/light mode** — Respect `prefers-color-scheme` independently of overlay theme
- [ ] **Better overlay GIFs** — Replace Giphy sources with self-hosted, looping, compressed WebP animations
- [ ] **Multi-language** — i18n for AI summaries and UI strings
- [ ] **Rate limiting** — FastAPI middleware to throttle `/api/weather` calls per IP

### Known issues to fix
- [ ] `frontend/.env` was accidentally saved as a PowerShell script — replace with plain text (see Setup above)
- [ ] `requirments.txt` filename has a typo — rename to `requirements.txt` and update CI/docs
- [ ] `venv/`, `node_modules/`, and `data/weather.grib` were previously committed — run `git rm --cached` to untrack them
- [ ] API keys were committed in `.env` — rotate the OpenWeather, OpenAI, and DeepSeek keys

---

## Untracking committed files

The old `.gitignore` was missing entries. Run this once to stop tracking files that should be ignored:

```bash
git rm -r --cached venv/ node_modules/ frontend/node_modules/ __pycache__/ backend/__pycache__/
git rm --cached data/weather.grib data/weather.grib.*.idx tailwindcss.exe
git commit -m "Stop tracking ignored files"
```

Then rotate any API keys that were exposed in the commit history.

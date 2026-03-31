"""
Weather App — FastAPI backend
Run with:  uvicorn backend.main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from backend import community
from backend.auth import optional_api_key
from backend.fetch_weather import fetch_air_quality
from backend.forecast_server import build_weather_response, build_weather_response_from_name
from backend.location_lookup import resolve_location
from backend.overlays import ALL_OVERLAYS, get_overlay

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "server", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Weather App API")
    community.init_db()
    yield
    logger.info("Shutting down Weather App API")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Weather App API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    lat: float
    lon: float
    condition: str
    description: str = ""
    city: str = ""
    username: str = "Anonymous"


# ---------------------------------------------------------------------------
# Weather routes
# ---------------------------------------------------------------------------

@app.get("/api/weather")
async def get_weather(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    name: Optional[str] = Query(None, description="City or place name"),
    ip: Optional[str] = Query(None, description="Client IP for geolocation"),
    source: str = Query("auto", description="'auto' | 'grib' | 'openweather'"),
    ai: bool = Query(True, description="Include AI summary and recommendations"),
    request: Request = None,
):
    """
    Main weather endpoint. Supply one of:
      - lat + lon
      - name  (city name)
      - ip    (IP address — or omit to use requester's IP)
    """
    # Resolve coordinates
    if lat is not None and lon is not None:
        pass  # already have coords
    elif name:
        data = build_weather_response_from_name(name, source=source, include_ai=ai)
        if not data:
            raise HTTPException(404, detail=f"Location '{name}' not found")
        return data
    else:
        # Geolocate by IP
        client_ip = ip or (request.client.host if request else None)
        loc = resolve_location(ip=client_ip)
        if not loc:
            raise HTTPException(503, detail="Could not determine location from IP")
        lat, lon = loc["lat"], loc["lon"]

    try:
        return build_weather_response(lat, lon, source=source, include_ai=ai)
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}", exc_info=True)
        raise HTTPException(502, detail="Weather data unavailable")


@app.get("/api/weather/current")
async def get_current(
    lat: float = Query(...),
    lon: float = Query(...),
    source: str = Query("auto"),
):
    """Current conditions only (no forecast, no AI)."""
    try:
        return build_weather_response(lat, lon, source=source, include_ai=False)
    except Exception as e:
        logger.error(f"Current weather failed: {e}", exc_info=True)
        raise HTTPException(502, detail="Weather data unavailable")


@app.get("/api/weather/forecast")
async def get_forecast(
    lat: float = Query(...),
    lon: float = Query(...),
):
    """5-day hourly + daily forecast only."""
    from backend.fetch_weather import fetch_forecast
    try:
        return fetch_forecast(lat, lon)
    except Exception as e:
        logger.error(f"Forecast failed: {e}", exc_info=True)
        raise HTTPException(502, detail="Forecast unavailable")


@app.get("/api/weather/aqi")
async def get_aqi(lat: float = Query(...), lon: float = Query(...)):
    """Air quality index."""
    try:
        return fetch_air_quality(lat, lon)
    except Exception as e:
        logger.error(f"AQI failed: {e}", exc_info=True)
        raise HTTPException(502, detail="Air quality data unavailable")


# ---------------------------------------------------------------------------
# Overlay routes
# ---------------------------------------------------------------------------

@app.get("/api/overlay")
async def get_overlay_info(
    condition_id: int = Query(800),
    wind_ms: float = Query(0),
    hour: Optional[int] = Query(None),
):
    """Return overlay filename + Apple Glass theme for given weather state."""
    return get_overlay(condition_id, wind_ms, hour)


@app.get("/api/overlay/list")
async def list_overlays():
    """Return the full list of overlay GIF filenames the frontend should have."""
    return {"overlays": ALL_OVERLAYS}


# ---------------------------------------------------------------------------
# Location routes
# ---------------------------------------------------------------------------

@app.get("/api/location")
async def get_location(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    name: Optional[str] = Query(None),
    ip: Optional[str] = Query(None),
    request: Request = None,
):
    """Resolve a location from coords, name, or IP."""
    client_ip = ip or (request.client.host if request else None)
    loc = resolve_location(lat=lat, lon=lon, name=name, ip=client_ip)
    if not loc:
        raise HTTPException(404, detail="Location not found")
    return loc


# ---------------------------------------------------------------------------
# Community routes
# ---------------------------------------------------------------------------

@app.post("/api/community/reports", status_code=201)
async def create_report(body: ReportCreate):
    """Submit a community weather report."""
    report = community.add_report(
        lat=body.lat,
        lon=body.lon,
        condition=body.condition,
        description=body.description,
        city=body.city,
        username=body.username,
    )
    return report


@app.get("/api/community/reports")
async def list_reports(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius: float = Query(1.0, description="Search radius in degrees (~111 km per degree)"),
    limit: int = Query(20, le=100),
):
    """Get community reports near a location (or all recent if no coords given)."""
    if lat is not None and lon is not None:
        return community.get_nearby_reports(lat, lon, radius_deg=radius, limit=limit)
    return community.get_recent_reports(limit=limit)


@app.get("/api/community/reports/{report_id}")
async def get_report(report_id: int):
    report = community.get_report(report_id)
    if not report:
        raise HTTPException(404, detail="Report not found")
    return report


@app.delete("/api/community/reports/{report_id}")
async def delete_report(report_id: int, _key=Depends(optional_api_key)):
    if not community.delete_report(report_id):
        raise HTTPException(404, detail="Report not found")
    return {"deleted": report_id}


# ---------------------------------------------------------------------------
# Photo upload (proxied from server/index.cjs but also available here)
# ---------------------------------------------------------------------------

@app.post("/api/upload/photo")
async def upload_photo(file: UploadFile = File(...)):
    """Save a community photo and return its URL path."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="Only image files are accepted")

    import uuid, aiofiles
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(1024 * 256):
            await f.write(chunk)

    return {"url": f"/uploads/{filename}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

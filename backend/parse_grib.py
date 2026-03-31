import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

GRIB_PATH = os.getenv("GRIB_SAVE_PATH", "data/weather.grib")

# Map of GRIB shortName -> standard key used in our weather dict
_VAR_MAP = {
    # Temperature
    "2t": "temp_k", "t2m": "temp_k", "t": "temp_k",
    # Wind components
    "10u": "u10", "u10": "u10", "u": "u10",
    "10v": "v10", "v10": "v10", "v": "v10",
    # Total precipitation (metres)
    "tp": "precip_m",
    # Surface pressure / mean sea level pressure
    "sp": "pressure_pa", "msl": "pressure_pa",
    # Relative humidity
    "2r": "humidity", "r2": "humidity", "r": "humidity",
    # Total cloud cover (0-1)
    "tcc": "cloud_cover",
    # Dewpoint
    "2d": "dewpoint_k", "d2m": "dewpoint_k",
    # Visibility
    "vis": "visibility_m",
    # Snow depth
    "sd": "snow_depth_m",
}


def _load_datasets(path: str):
    """Open GRIB file and return list of xarray datasets."""
    try:
        import cfgrib
    except ImportError:
        raise ImportError("cfgrib is required: pip install cfgrib")

    if not os.path.exists(path):
        raise FileNotFoundError(f"GRIB file not found: {path}")

    try:
        return cfgrib.open_datasets(path)
    except Exception as e:
        logger.error(f"Failed to open GRIB file '{path}': {e}")
        raise


def _nearest_indices(coord_array, value: float) -> int:
    return int(np.argmin(np.abs(np.asarray(coord_array) - value)))


def extract_raw_at(lat: float, lon: float, path: str = None) -> dict:
    """
    Extract all available variables from the GRIB file at the nearest
    grid point to (lat, lon). Returns a flat dict of shortName -> float.
    """
    path = path or GRIB_PATH
    datasets = _load_datasets(path)
    raw: dict[str, float] = {}

    for ds in datasets:
        # Determine lat/lon coordinate names
        lat_key = next((k for k in ("latitude", "lat") if k in ds.coords), None)
        lon_key = next((k for k in ("longitude", "lon") if k in ds.coords), None)
        if lat_key is None or lon_key is None:
            continue

        lat_idx = _nearest_indices(ds.coords[lat_key].values, lat)
        lon_idx = _nearest_indices(ds.coords[lon_key].values, lon)

        for var in ds.data_vars:
            if var in raw:
                continue
            try:
                arr = ds[var]
                sel = {lat_key: lat_idx, lon_key: lon_idx}
                extracted = arr.isel(**sel)
                # Collapse any remaining dimensions (e.g. time) to a scalar
                scalar = extracted.values.flat[0]
                val = float(scalar)
                if not np.isnan(val):
                    raw[var] = val
            except Exception as e:
                logger.debug("Skipping GRIB variable '%s': %s", var, e)

    return raw


def grib_to_weather_dict(lat: float, lon: float, path: str = None) -> dict:
    """
    Convert GRIB data at (lat, lon) into a standardised weather dict
    matching the format returned by openweathermap_api.get_current_weather().
    """
    raw = extract_raw_at(lat, lon, path)

    # Normalise keys via _VAR_MAP
    norm: dict[str, float] = {}
    for grib_key, std_key in _VAR_MAP.items():
        if grib_key in raw and std_key not in norm:
            norm[std_key] = raw[grib_key]

    weather: dict = {}

    # Temperature (K → °C)
    if "temp_k" in norm:
        t = norm["temp_k"]
        weather["temperature_c"] = round(t - 273.15 if t > 100 else t, 1)

    # Dewpoint (K → °C)
    if "dewpoint_k" in norm:
        d = norm["dewpoint_k"]
        weather["dewpoint_c"] = round(d - 273.15 if d > 100 else d, 1)

    # Wind speed + direction
    if "u10" in norm and "v10" in norm:
        u, v = norm["u10"], norm["v10"]
        speed = float(np.sqrt(u ** 2 + v ** 2))
        # Meteorological convention: direction wind is coming FROM
        direction = (270 - float(np.degrees(np.arctan2(v, u)))) % 360
        weather["wind_speed_ms"] = round(speed, 2)
        weather["wind_deg"] = round(direction, 1)

    # Precipitation m → mm
    if "precip_m" in norm:
        weather["precipitation_mm"] = round(norm["precip_m"] * 1000, 2)

    # Pressure Pa → hPa
    if "pressure_pa" in norm:
        weather["pressure_hpa"] = round(norm["pressure_pa"] / 100, 1)

    # Humidity
    if "humidity" in norm:
        h = norm["humidity"]
        weather["humidity_pct"] = round(h * 100 if h <= 1.0 else h, 1)

    # Cloud cover 0-1 → %
    if "cloud_cover" in norm:
        cc = norm["cloud_cover"]
        weather["cloud_cover_pct"] = round(cc * 100 if cc <= 1.0 else cc, 1)

    # Visibility
    if "visibility_m" in norm:
        weather["visibility_m"] = round(norm["visibility_m"])

    # Snow depth m → cm
    if "snow_depth_m" in norm:
        weather["snow_depth_cm"] = round(norm["snow_depth_m"] * 100, 1)

    weather["source"] = "ecmwf_grib"
    return weather

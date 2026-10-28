"""
services/weather_service.py
===========================
Weather Intelligence service wrapping Open-Meteo API and agricultural risk engine
with Streamlit 15-minute response caching per city, including real forecast time-series.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import requests
import streamlit as st

from modules.weather import geocode_city, weather_report, weather_status, WEATHER_URL, REQUEST_TIMEOUT
from utils.caching import cached_data
from utils.config import WEATHER_CACHE_TTL_SECONDS


@cached_data(ttl=WEATHER_CACHE_TTL_SECONDS)
def get_cached_weather(city: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    Fetch live Open-Meteo current conditions with a 15-minute cache.
    Does not invent forecast data when API fails.
    """
    return weather_report(city=city, manual_values=None, use_ai=use_ai)


@cached_data(ttl=WEATHER_CACHE_TTL_SECONDS)
def get_cached_forecast(city: str, days: int = 3) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetch real hourly forecast data from Open-Meteo (temperature, relative humidity, precipitation)
    for the next 3 to 7 days. Cached for 15 minutes per city.
    """
    location, err = geocode_city(city)
    if err or not location:
        return None, err or "Location not found"

    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,precipitation_probability",
                "forecast_days": max(1, min(7, days)),
                "timezone": "auto",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return None, f"Forecast API returned HTTP {response.status_code}"
        payload = response.json()
        payload["location"] = location
        return payload, None
    except Exception as exc:
        return None, f"Failed to retrieve forecast: {exc}"


def get_manual_weather(
    city: str,
    temperature: float,
    humidity: int,
    rainfall: Optional[float] = 0.0,
    use_ai: bool = True,
) -> Dict[str, Any]:
    """Run agricultural risk rules on farmer-provided manual observations."""
    manual = {
        "temperature": temperature,
        "humidity": humidity,
        "rainfall": rainfall if rainfall is not None else 0.0,
    }
    return weather_report(city=city, manual_values=manual, use_ai=use_ai)


def get_service_status() -> Dict[str, Any]:
    """Return weather service configuration status."""
    return weather_status()

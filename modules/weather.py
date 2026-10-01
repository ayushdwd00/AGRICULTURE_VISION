"""
modules/weather.py
==================
MODULE 3 - Weather & Pest Early Warning.

Workflow implemented here::

    City
      |
      v
    Open-Meteo Geocoding API          -> coordinates (+ resolved city/country)
      |
      v
    Open-Meteo Forecast API            -> temperature, humidity, rain, description
      |
      v
    Rule engine (deterministic)       -> risk flags
      |
      v
    Gemini wording (with fallback)    -> farmer friendly warning

The rules are deliberately simple and transparent (no ML):

* ``humidity > 80 %`` **and** ``20 °C <= temperature <= 30 °C`` -> fungal disease risk
* ``temperature > 35 °C``                                     -> heat stress risk
  (extended with a few documented, equally simple rules: moderate fungal risk,
  rain-favoured bacterial spread, strong-wind spraying caution, cold stress.)

Open-Meteo is free and does not require an API key. When a city cannot be
resolved or a provider request fails, the module returns a clear,
human-readable error instead of raising. A manual-values path remains available
for offline demonstrations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import requests
from utils.helpers import timestamp

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 20

def weather_status() -> Dict[str, Any]:
    """Status dictionary used by the UI."""
    return {
        "configured": True,
        "geocode_url": GEOCODE_URL,
        "weather_url": WEATHER_URL,
        "offline_rule_engine": True,
    }

# API access

def geocode_city(city: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Resolve a city name to coordinates with the Open-Meteo Geocoding API.

    Returns ``(location, error)``; ``location`` is ``None`` when the city is
    unknown (the UI shows the equivalent of a 404 message).
    """
    city = (city or "").strip()
    if not city:
        return None, "Please enter a city name."

    try:
        response = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return None, f"Could not reach the geocoding service ({exc}). Check your internet connection."

    if response.status_code != 200:
        return None, f"Geocoding failed with HTTP {response.status_code}."

    try:
        matches = response.json()
    except ValueError:
        return None, "The geocoding service returned an unexpected response."

    matches = matches.get("results") or []
    if not matches:
        return None, (
            f"City '{city}' was not found. Check the spelling or try a nearby larger city "
            "(for example: Varanasi, Lucknow, Nagpur)."
        )
    top = matches[0]
    return {
        "name": top.get("name") or city,
        "country": top.get("country") or "",
        "state": top.get("admin1") or "",
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
    }, None

def fetch_current_weather(
    city: str
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Current weather for ``city``; returns ``(weather, error)``."""
    location, error = geocode_city(city)
    if error or not location:
        return None, error

    try:
        response = requests.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,wind_speed_10m,weather_code"
                ),
                "timezone": "auto",
                "wind_speed_unit": "ms",
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return None, f"Could not reach the weather service ({exc})."

    if response.status_code != 200:
        return None, f"Weather lookup failed with HTTP {response.status_code}."

    try:
        payload = response.json()
    except ValueError:
        return None, "The weather service returned an unexpected response."

    current = payload.get("current") or {}
    weather_code = current.get("weather_code")

    weather = {
        "city": location["name"],
        "region": location.get("state"),
        "country": location["country"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "temperature": round(float(current.get("temperature_2m", 0.0)), 1),
        "feels_like": round(float(current.get("apparent_temperature", 0.0)), 1),
        "humidity": int(current.get("relative_humidity_2m", 0)),
        "pressure": current.get("surface_pressure"),
        "wind_speed": current.get("wind_speed_10m"),
        "rain_1h": current.get("precipitation"),
        "description": weather_description(weather_code),
        "source": "Open-Meteo",
        "fetched_at": timestamp(),
        "error": None,
    }
    return weather, None


def weather_description(code: Optional[int]) -> str:
    """Convert an Open-Meteo WMO weather code into readable text."""
    descriptions = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "foggy",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",
        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail",
    }
    return descriptions.get(code, "current conditions")

def manual_weather(
    city: str,
    temperature: float,
    humidity: int,
    rainfall: Optional[float] = None,
    description: str = "manually entered values",
) -> Dict[str, Any]:
    """
    Build a weather dictionary from manually entered values.

    The deterministic rule engine and AI wording work exactly the same, they just
    run on values the user read from their own weather app.
    """
    return {
        "city": (city or "manual entry").strip(),
        "region": None,
        "country": "",
        "latitude": None,
        "longitude": None,
        "temperature": float(temperature),
        "feels_like": float(temperature),
        "humidity": int(humidity),
        "pressure": None,
        "wind_speed": None,
        "rain_1h": float(rainfall) if rainfall is not None else None,
        "description": description,
        "source": "manual values (no API key)",
        "fetched_at": timestamp(),
        "error": None,
    }

# Rule engine (deterministic - no ML, no LLM)

def evaluate_risks(weather: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Apply the AgriVision weather risk rules and return the triggered risks.

    Each risk is ``{"key", "level", "title", "detail", "rule"}`` where ``rule`` is
    the literal condition that fired - so the UI can show *why* the alert exists.
    """
    temperature = float(weather.get("temperature", 0.0) or 0.0)
    humidity = float(weather.get("humidity", 0.0) or 0.0)
    rain = weather.get("rain_1h")
    wind = weather.get("wind_speed")
    risks: List[Dict[str, Any]] = []

    # Rule 1 (project brief): high humidity + mild temperature -> fungal pressure.
    if humidity > 80 and 20 <= temperature <= 30:
        risks.append(
            {
                "key": "fungal",
                "level": "HIGH",
                "title": "Fungal disease risk",
                "detail": (
                    f"Humidity {humidity:.0f}% with {temperature:.1f} C is ideal for fungal "
                    "growth (early blight, late blight, leaf mould)."
                ),
                "rule": "humidity > 80% AND 20 C <= temperature <= 30 C",
            }
        )
    elif humidity >= 70 and 18 <= temperature <= 32:
        risks.append(
            {
                "key": "fungal",
                "level": "MODERATE",
                "title": "Watch for fungal disease",
                "detail": (
                    f"Humidity {humidity:.0f}% with {temperature:.1f} C is moderately "
                    "favourable for fungal diseases."
                ),
                "rule": "humidity >= 70% AND 18 C <= temperature <= 32 C",
            }
        )

    # Rule 2 (project brief): heat stress.
    if temperature > 35:
        risks.append(
            {
                "key": "heat",
                "level": "HIGH",
                "title": "Heat stress risk",
                "detail": (
                    f"{temperature:.1f} C is above the comfort range for most vegetables - "
                    "expect wilting, flower drop and sunscald."
                ),
                "rule": "temperature > 35 C",
            }
        )

    # Documented extra rules --------------------------------------------------
    if rain is not None and rain > 0 and temperature >= 22:
        risks.append(
            {
                "key": "bacterial",
                "level": "MODERATE",
                "title": "Bacterial spread risk",
                "detail": (
                    f"Rainfall of {rain} mm with warm temperature helps bacterial spot spread "
                    "by rain splash."
                ),
                "rule": "rain_1h > 0 AND temperature >= 22 C",
            }
        )
    if wind is not None and wind >= 8:
        risks.append(
            {
                "key": "wind",
                "level": "MODERATE",
                "title": "Strong wind - spraying caution",
                "detail": f"Wind speed {wind} m/s makes spraying unsafe (drift, poor coverage).",
                "rule": "wind_speed >= 8 m/s",
            }
        )
    if temperature < 10:
        risks.append(
            {
                "key": "cold",
                "level": "MODERATE",
                "title": "Cold stress risk",
                "detail": f"{temperature:.1f} C can slow growth and damage sensitive crops.",
                "rule": "temperature < 10 C",
            }
        )
    return risks

def risk_level(risks: List[Dict[str, Any]]) -> str:
    """Overall risk level: HIGH > MODERATE > LOW."""
    levels = {str(risk.get("level", "")).upper() for risk in risks}
    if "HIGH" in levels:
        return "HIGH"
    if "MODERATE" in levels:
        return "MODERATE"
    return "LOW"

def generate_weather_message(
    weather: Dict[str, Any], risks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Farmer-friendly wording for the risk alerts.

    Thin wrapper around :func:`utils.gemini.generate_weather_message` so Module 3
    exposes the function name documented in the project brief.  The risk *levels*
    always come from :func:`evaluate_risks` and are never invented by the LLM.
    """
    from utils.gemini import generate_weather_message as _generate

    return _generate(weather, risks)

def weather_report(
    city: str, manual_values: Optional[Dict[str, Any]] = None, use_ai: bool = True
) -> Dict[str, Any]:
    """
    Full Module-3 pipeline: city -> weather -> risk rules -> AI wording.

    ``manual_values`` (``temperature`` / ``humidity`` / ``rainfall``) bypasses the API
    for offline analysis.
    """
    if manual_values:
        weather = manual_weather(
            city,
            temperature=manual_values.get("temperature", 25.0),
            humidity=manual_values.get("humidity", 70),
            rainfall=manual_values.get("rainfall"),
            description=manual_values.get("description", "manually entered values"),
        )
        error = None
    else:
        weather, error = fetch_current_weather(city)

    if weather is None:
        return {
            "city": city,
            "weather": None,
            "risks": [],
            "risk_level": None,
            "message": None,
            "error": error or "Weather lookup failed.",
            "fetched_at": timestamp(),
        }

    risks = evaluate_risks(weather)
    message = generate_weather_message(weather, risks) if use_ai else None
    return {
        "city": weather.get("city") or city,
        "weather": weather,
        "risks": risks,
        "risk_level": risk_level(risks),
        "message": message,
        "error": None,
        "fetched_at": timestamp(),
    }

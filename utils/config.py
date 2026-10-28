"""
utils/config.py
===============
Configuration constants, theme design tokens, paths, and environment settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
IMAGES_DIR: Path = ASSETS_DIR / "images"
MODELS_DIR: Path = PROJECT_ROOT / "models"
DATA_DIR: Path = PROJECT_ROOT / "data"
SAMPLE_IMAGES_DIR: Path = DATA_DIR / "sample_images"

# Load .env safely
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Application Metadata
APP_TITLE = "AgriVision — Agricultural Decision-Support Intelligence"
APP_SUBTITLE = "Smart Agriculture Super-App for Field Diagnosis, Weather Intelligence, Nutrient Planning & Verifications"
APP_VERSION = "2.0.0 (Python Streamlit Architecture)"
BRITANNICA_FERTILIZER_URL = "https://www.britannica.com/topic/fertilizer"

# Confidence & Thresholds
CONFIDENCE_THRESHOLD = 0.70
MAX_UPLOAD_SIZE_MB = 8
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Brand Design Tokens (Preserving AgriVision's Editorial Botanical Identity)
THEME_COLORS = {
    "linen": "#F7F5EE",
    "cream": "#FFFFF3",
    "surface": "#FFFFFF",
    "ink": "#111812",
    "charcoal": "#2A2A26",
    "muted": "#5E6057",
    "muted_light": "#828479",
    "border": "rgba(27, 61, 38, 0.12)",
    "border_strong": "rgba(27, 61, 38, 0.22)",
    "sage": "#2D5A27",
    "sage_deep": "#1B3D26",
    "sage_soft": "#E2F7E4",
    "sage_accent": "#BEEDC0",
    "amber_soft": "#FEF3C7",
    "amber_text": "#92400E",
    "rose_soft": "#FEE2E2",
    "rose_text": "#991B1B",
    "sky_soft": "#E0F2FE",
    "sky_text": "#0369A1",
}

# Weather Open-Meteo Endpoints
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE_TTL_SECONDS = 900  # 15 minutes cache

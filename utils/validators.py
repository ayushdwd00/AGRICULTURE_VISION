"""
utils/validators.py
===================
Input validation and sanitization for farmer and agronomist interactions.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from utils.config import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB

PRODUCT_CODE_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_/]{2,99}$")


def validate_image_upload(file: Any) -> Tuple[bool, Optional[str]]:
    """Validate uploaded image file type and size."""
    if file is None:
        return False, "Please upload or select a plant or leaf image."
    
    # Check size
    size = getattr(file, "size", None)
    if size is not None and size > MAX_UPLOAD_SIZE_BYTES:
        return False, f"Image size exceeds {MAX_UPLOAD_SIZE_MB} MiB limit. Please upload a smaller photo."
    
    # Check mime type and extension
    name = getattr(file, "name", "")
    type_ = getattr(file, "type", "")
    valid_exts = (".jpg", ".jpeg", ".png", ".webp")
    has_valid_ext = any(name.lower().endswith(ext) for ext in valid_exts)
    has_valid_type = not type_ or type_.startswith("image/")
    if not (has_valid_ext and has_valid_type):
        return False, "Unsupported file format. Please upload a JPEG, PNG, or WebP image."
    
    return True, None


def validate_land_area(value: Any) -> Tuple[bool, Optional[str], float]:
    """Validate land size in acres or hectares."""
    try:
        val = float(value)
        if val <= 0:
            return False, "Land area must be greater than zero.", 0.0
        if val > 1_000_000:
            return False, "Land area exceeds reasonable farm limit (max 1,000,000).", 0.0
        return True, None, val
    except (TypeError, ValueError):
        return False, "Please enter a valid numeric land area.", 0.0


def validate_city_name(city: str) -> Tuple[bool, Optional[str], str]:
    """Validate city name for geocoding."""
    cleaned = (city or "").strip()
    if not cleaned:
        return False, "Please enter a city or village name.", ""
    if len(cleaned) < 2:
        return False, "Location name is too short.", ""
    if len(cleaned) > 100:
        return False, "Location name is too long.", ""
    return True, None, cleaned


def validate_product_code(code: str) -> Tuple[bool, Optional[str], str]:
    """Validate product batch / serial code format."""
    cleaned = (code or "").strip().upper()
    if not cleaned:
        return False, "Please enter a product code or scan a QR code.", ""
    if len(cleaned) < 3:
        return False, "Product code must be at least 3 characters.", ""
    if not PRODUCT_CODE_REGEX.match(cleaned):
        return False, "Invalid product code format. Only letters, numbers, hyphens, and slashes are allowed.", ""
    return True, None, cleaned

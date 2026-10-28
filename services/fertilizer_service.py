"""
services/fertilizer_service.py
==============================
Deterministic fertilizer dosage & cost calculation service using reference lookups.
Includes educational context distinguishing reference dosage from customized soil tests.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import streamlit as st

from modules.fertilizer import available_crops, calculate, deficiencies_for_crop, load_fertilizer_data
from utils.caching import cached_data
from utils.config import BRITANNICA_FERTILIZER_URL


@cached_data()
def get_cached_fertilizer_data() -> Dict[str, Any]:
    """Load and cache the fertilizer lookup table from data/fertilizer_data.json."""
    return load_fertilizer_data()


def get_crops() -> List[str]:
    """Return available crop names in the fertilizer table."""
    return available_crops()


def get_deficiencies(crop: str) -> List[str]:
    """Return available deficiency options for a given crop."""
    if not crop:
        return []
    return deficiencies_for_crop(crop)


def calculate_fertilizer_plan(
    crop: str,
    deficiency: str,
    land_size: float,
    unit: str = "acres",
    bag_weight_kg: float = 45.0,
) -> Dict[str, Any]:
    """
    Perform deterministic fertilizer calculation for given acreage and deficiency.
    Also calculates number of standard bags needed.
    """
    result = calculate(crop=crop, deficiency=deficiency, land_size_acres=land_size, unit=unit)
    if result.get("error"):
        return result

    # Additional practical calculation: bag quantities
    quantity_kg = result.get("quantity", 0.0)
    if bag_weight_kg > 0 and quantity_kg > 0:
        bags_float = quantity_kg / bag_weight_kg
        bags_ceil = math.ceil(bags_float)
        result["bag_weight_kg"] = bag_weight_kg
        result["bags_exact"] = round(bags_float, 2)
        result["bags_to_buy"] = bags_ceil

    result["britannica_reference"] = BRITANNICA_FERTILIZER_URL
    return result

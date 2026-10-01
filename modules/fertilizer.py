"""
modules/fertilizer.py
=====================
MODULE 4 - Fertilizer Calculator.

**This module is deterministic / rule-based, not ML-driven.**

* The crop -> deficiency -> fertilizer -> dosage mapping lives in the static file
  ``data/fertilizer_data.json`` (a documented lookup table with indicative
  per-acre doses and prices).
* The only arithmetic performed here is::

      quantity       = dosage_per_acre x land_size_acres
      estimated_cost = quantity x cost_per_unit

* **Gemini is never used to invent fertilizer quantities or costs.**  The app
  shows a note on the page making this explicit.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from utils.helpers import FERTILIZER_DATA_PATH, load_json

def load_fertilizer_data(path: Any = FERTILIZER_DATA_PATH) -> Dict[str, Any]:
    """Load the static lookup table (raises a friendly error when missing)."""
    data = load_json(path)
    if not isinstance(data, dict) or not data.get("crops"):
        raise FileNotFoundError(
            f"Fertilizer lookup table missing or malformed: {path}. "
            "Expected data/fertilizer_data.json with a 'crops' section."
        )
    return data

def available_crops() -> List[str]:
    """Crops that have at least one recommendation in the table."""
    try:
        return sorted(load_fertilizer_data()["crops"].keys())
    except FileNotFoundError:
        return []

def deficiencies_for_crop(crop: str) -> List[str]:
    """
    Deficiencies that can be selected for a crop: the crop-specific N/P/K entries
    plus the nutrients that are shared by all crops.
    """
    data = load_fertilizer_data()
    crop_entries = data["crops"].get(crop, {})
    order = data.get("deficiency_order", [])
    shared = data.get("common_deficiency_products", {})

    names = list(crop_entries.keys()) + [name for name in shared if name not in crop_entries]
    # Preserve the documented order from the JSON file.
    ordered = [name for name in order if name in names]
    extra = [name for name in names if name not in ordered]
    return ordered + extra

def _find_product(crop: str, deficiency: str) -> Optional[Dict[str, Any]]:
    data = load_fertilizer_data()
    return (
        (data["crops"].get(crop) or {}).get(deficiency)
        or (data.get("common_deficiency_products") or {}).get(deficiency)
    )

def calculate(
    crop: str, deficiency: str, land_size_acres: float, unit: str = "acres"
) -> Dict[str, Any]:
    """
    Look up the fertiliser and scale the dose to the farmer's land size.

    Parameters
    ----------
    crop, deficiency:
        Must exist in ``data/fertilizer_data.json``.
    land_size_acres:
        Land size; when ``unit`` is ``"hectares"`` the value is converted
        (1 hectare = 2.47105 acres) before scaling.
    unit:
        ``"acres"`` (default) or ``"hectares"``.

    Returns
    -------
    A dictionary with the fertilizer name, quantity, estimated cost, the
    assumptions used and a plain-language summary.  Errors are reported through
    the ``"error"`` key - the function never raises for bad user input.
    """
    try:
        data = load_fertilizer_data()
    except FileNotFoundError as exc:
        return {"error": str(exc)}

    if crop not in data["crops"]:
        return {"error": f"Crop '{crop}' is not in the fertilizer table."}

    product = _find_product(crop, deficiency)
    if product is None:
        return {
            "error": (
                f"No recommendation for '{deficiency}' on {crop}. "
                "Pick a different deficiency or confirm the dose with your soil test report."
            )
        }

    try:
        land_size_acres = float(land_size_acres)
    except (TypeError, ValueError):
        return {"error": "Land size must be a number."}
    if not math.isfinite(land_size_acres) or land_size_acres <= 0:
        return {"error": "Land size must be greater than zero."}

    acres = land_size_acres
    if str(unit).lower().startswith("hect"):
        acres = land_size_acres * 2.47105

    dosage = float(product["dosage_per_acre"])
    cost_per_unit = float(product["cost_per_unit"])
    quantity = dosage * acres
    estimated_cost = quantity * cost_per_unit

    return {
        "error": None,
        "crop": crop,
        "deficiency": deficiency,
        "fertilizer": product["fertilizer"],
        "dosage_per_acre": dosage,
        "unit": product["unit"],
        "land_size_acres": round(acres, 3),
        "land_size_input": land_size_acres,
        "land_size_unit": unit,
        "quantity": round(quantity, 2),
        "estimated_cost": round(estimated_cost, 2),
        "cost_per_unit": cost_per_unit,
        "currency": "INR",
        "application": product.get("application", ""),
        "assumptions": (
            f"Indicative dose of {dosage:g} {product['unit']} per acre for {crop} "
            f"({deficiency}) at ~INR {cost_per_unit:g} per {product['unit']}. "
            "Real doses depend on your soil test values."
        ),
        "summary": (
            f"Apply {product['fertilizer']} at about {round(quantity, 2):g} "
            f"{product['unit']} for {round(acres, 2):g} acre(s); "
            f"estimated cost INR {round(estimated_cost):,}."
        ),
    }

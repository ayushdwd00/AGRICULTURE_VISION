"""
modules/subsidy_matcher.py
==========================
MODULE 6 - Government Scheme Matcher.

**Deterministic matching, no ML.**  ``data/schemes.json`` holds 8 publicly
available central-sector agricultural schemes (name, description, eligibility,
land-size limits, region, crop coverage, required documents and the *real*
official application link).

The four wizard steps map onto the matching rules::

    Step 1  land size (acres)      -> land_size_min_acres / land_size_max_acres
    Step 2  region (state)         -> region ("All India" matches every state)
    Step 3  crop                   -> crop_type ("Any" matches every crop)
    Step 4  additional filter      -> category (insurance, credit, irrigation, ...)

The LLM is never used here: it must not fabricate scheme names or application
links, so matching is done purely on the JSON rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.helpers import SCHEMES_PATH, load_json

#: Indian states / UTs plus the union-level option used by wizard step 2.
REGIONS: List[str] = [
    "All India",
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu",
    "Telangana", "Uttar Pradesh", "Uttarakhand", "West Bengal",
]

def load_schemes(path: Any = SCHEMES_PATH) -> Dict[str, Any]:
    """Load ``data/schemes.json`` (raises a friendly error when missing)."""
    data = load_json(path)
    if not isinstance(data, dict) or not data.get("schemes"):
        raise FileNotFoundError(
            f"Scheme list missing or malformed: {path}. "
            "Expected data/schemes.json with a 'schemes' array."
        )
    return data

def scheme_categories() -> List[str]:
    """Categories used by wizard step 4."""
    try:
        return list(load_schemes().get("meta", {}).get("categories", []))
    except FileNotFoundError:
        return []

def crop_options() -> List[str]:
    """Crop choices for wizard step 3 (built from the documented crop groups)."""
    try:
        groups = load_schemes().get("meta", {}).get("crop_groups", {})
    except FileNotFoundError:
        return ["Any"]
    crops: List[str] = []
    for values in groups.values():
        for crop in values:
            if crop not in crops:
                crops.append(crop)
    return ["Any"] + crops

def _crop_matches(
    scheme: Dict[str, Any], crop: str, crop_groups: Dict[str, List[str]]
) -> bool:
    """Does the selected crop fall inside the scheme's declared coverage?"""
    coverage = scheme.get("crop_type") or ["Any"]
    if crop in {"", "Any"} or "Any" in coverage:
        return True
    if crop in coverage:
        return True
    for group in coverage:
        if crop in crop_groups.get(group, []):
            return True
        if group.lower().startswith("any"):
            return True  # entries such as "Any horticultural crop"
    return False

def match_schemes(
    land_size_acres: float,
    region: str = "All India",
    crop: str = "Any",
    category: Optional[str] = None,
    path: Any = SCHEMES_PATH,
) -> Dict[str, Any]:
    """
    Match the wizard inputs against the static scheme rules.

    Returns ``{"matches", "near_misses", "inputs", "error"}``:

    * ``matches``     - schemes that fit the land size, region and crop (a category
      mismatch is reported as a *note* instead of hiding a relevant scheme);
    * ``near_misses`` - schemes that failed on a criterion, together with the
      reason, so the farmer can see why something did not match.
    """
    try:
        data = load_schemes(path)
    except FileNotFoundError as exc:
        return {"matches": [], "near_misses": [], "inputs": {}, "error": str(exc)}

    try:
        land_size_acres = float(land_size_acres)
    except (TypeError, ValueError):
        return {
            "matches": [], "near_misses": [], "inputs": {},
            "error": "Land size must be a number.",
        }
    if land_size_acres <= 0:
        return {
            "matches": [], "near_misses": [], "inputs": {},
            "error": "Land size must be greater than zero.",
        }

    crop_groups = data.get("meta", {}).get("crop_groups", {})
    matches: List[Dict[str, Any]] = []
    near_misses: List[Dict[str, Any]] = []

    for scheme in data["schemes"]:
        reasons: List[str] = []
        matched_reasons: List[str] = []

        minimum = float(scheme.get("land_size_min_acres", 0.0))
        maximum = float(scheme.get("land_size_max_acres", 1e9))
        if minimum <= land_size_acres <= maximum:
            matched_reasons.append(
                f"Land size fits the {minimum:g}-{maximum:g} acre window"
                if maximum < 1e8
                else f"Land size is at least {minimum:g} acre"
            )
        else:
            reasons.append(
                f"Requires between {minimum:g} and {maximum:g} acres"
                if maximum < 1e8
                else f"Requires at least {minimum:g} acre"
            )

        scheme_region = str(scheme.get("region", "All India"))
        if scheme_region == "All India" or region == "All India" or scheme_region == region:
            matched_reasons.append(
                "Available all over India"
                if scheme_region == "All India"
                else f"Operates in {scheme_region}"
            )
        else:
            reasons.append(f"Currently listed for {scheme_region}")

        if _crop_matches(scheme, crop, crop_groups):
            matched_reasons.append(
                "Crop coverage: " + ", ".join(scheme.get("crop_type") or ["Any"])
            )
        else:
            reasons.append("Crop not covered: " + ", ".join(scheme.get("crop_type") or []))

        category_mismatch = False
        if category and category != "Any":
            if str(scheme.get("category")) == category:
                matched_reasons.append(f"Matches the selected category '{category}'")
            else:
                category_mismatch = True
                reasons.append(f"Category is '{scheme.get('category')}'")

        record = {**scheme, "matched_reasons": matched_reasons, "unmet_reasons": reasons}
        if not reasons:
            matches.append(record)
        elif len(reasons) == 1 and category_mismatch:
            # Only the optional category filter differs: keep it visible as a match
            # with a note, because the scheme is otherwise a genuine fit.
            record["unmet_reasons"] = [f"Category filter: {reasons[0]}"]
            matches.append(record)
        else:
            near_misses.append(record)

    return {
        "matches": matches,
        "near_misses": near_misses,
        "inputs": {
            "land_size_acres": land_size_acres,
            "region": region,
            "crop": crop,
            "category": category,
        },
        "error": None,
    }

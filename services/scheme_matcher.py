"""
services/scheme_matcher.py
==========================
Service for matching farmers with central and state government agricultural schemes
using deterministic eligibility rules and real official links.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st

from modules.subsidy_matcher import REGIONS, crop_options, load_schemes, match_schemes, scheme_categories
from utils.caching import cached_data


@cached_data()
def get_cached_schemes_data() -> Dict[str, Any]:
    """Load and cache schemes dataset from data/schemes.json."""
    return load_schemes()


def get_scheme_options() -> Dict[str, List[str]]:
    """Return available options for wizard filtering."""
    return {
        "regions": REGIONS,
        "crops": crop_options(),
        "categories": scheme_categories(),
    }


def find_matching_schemes(
    land_size_acres: float,
    region: str = "All India",
    crop: str = "Any",
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute scheme matching based on farmer criteria."""
    cat = None if category in (None, "", "Any") else category
    return match_schemes(
        land_size_acres=land_size_acres,
        region=region,
        crop=crop,
        category=cat,
    )


def get_all_schemes() -> List[Dict[str, Any]]:
    """Return full catalog of documented public schemes."""
    try:
        data = get_cached_schemes_data()
        return data.get("schemes", [])
    except Exception:
        return []

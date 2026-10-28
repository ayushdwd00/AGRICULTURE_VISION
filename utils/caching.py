"""
utils/caching.py
================
Streamlit caching wrappers with graceful fallbacks.
"""

from __future__ import annotations

from typing import Any, Callable
import streamlit as st


def cached_resource(func: Callable) -> Callable:
    """Decorator to cache heavy, stateful objects like ML models across sessions."""
    return st.cache_resource(show_spinner=False)(func)


def cached_data(ttl: int | None = None) -> Callable:
    """Decorator to cache deterministic lookups and API responses."""
    return st.cache_data(ttl=ttl, show_spinner=False)

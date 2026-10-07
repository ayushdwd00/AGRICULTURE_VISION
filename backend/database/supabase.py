"""
backend/database/supabase.py
============================
Core Supabase connection and query execution helpers for AgriVision.

Wraps the official Supabase Python client with unified error handling,
health checking, and query execution abstractions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.supabase_client import (
    get_supabase_client,
    get_supabase_url,
    is_supabase_configured,
)

logger = logging.getLogger("agrivision.supabase")


class SupabaseDatabaseError(Exception):
    """Raised when a Supabase PostgREST operation fails."""

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.details = details


def check_connection() -> Dict[str, Any]:
    """
    Check connection status to the Supabase PostgreSQL backend.

    Returns a status dictionary suitable for health-check reporting.
    """
    if not is_supabase_configured():
        return {
            "connected": False,
            "configured": False,
            "message": "Supabase environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) are not set.",
        }

    try:
        client = get_supabase_client()
        # Simple probe: query count from products or users
        response = client.table("products").select("code", count="exact").limit(1).execute()
        return {
            "connected": True,
            "configured": True,
            "url": get_supabase_url(),
            "count": response.count if hasattr(response, "count") else len(response.data),
            "message": "Successfully connected to Supabase PostgreSQL.",
        }
    except Exception as exc:
        logger.warning("Supabase connection check failed: %s", exc)
        return {
            "connected": False,
            "configured": True,
            "error": str(exc),
            "message": f"Failed to connect to Supabase: {exc}",
        }

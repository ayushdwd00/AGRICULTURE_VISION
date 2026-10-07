"""
backend/supabase_client.py
==========================
Supabase client initialization for AgriVision.

Reads connection credentials exclusively from environment variables:
- ``SUPABASE_URL``
- ``SUPABASE_SERVICE_ROLE_KEY``

SECURITY NOTE:
The service role key bypasses Row Level Security (RLS) in Supabase.
It must NEVER be hardcoded, logged, or exposed to the frontend/browser.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

from utils.helpers import PROJECT_ROOT

# Ensure environment variables from project root .env are loaded
load_dotenv(PROJECT_ROOT / ".env", override=False)

_client: Optional[Client] = None


def get_supabase_url() -> str:
    """Return configured SUPABASE_URL or empty string."""
    return os.getenv("SUPABASE_URL", "").strip()


def get_supabase_service_key() -> str:
    """Return configured SUPABASE_SERVICE_ROLE_KEY or empty string."""
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def is_supabase_configured() -> bool:
    """Check if both required Supabase environment variables are provided."""
    return bool(get_supabase_url() and get_supabase_service_key())


def get_supabase_client() -> Client:
    """
    Get or create the singleton Supabase client instance.

    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing.
    """
    global _client
    if _client is not None:
        return _client

    url = get_supabase_url()
    key = get_supabase_service_key()

    if not url or not key:
        missing = []
        if not url:
            missing.append("SUPABASE_URL")
        if not key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        raise RuntimeError(
            f"Cannot connect to Supabase: missing required environment variable(s): {', '.join(missing)}. "
            "Please configure these in your .env file."
        )

    _client = create_client(url, key)
    return _client


def reset_supabase_client() -> None:
    """Reset the singleton instance (useful for testing and configuration changes)."""
    global _client
    _client = None

"""
backend/database package
========================
Database abstraction layer for AgriVision.

Exposes repositories and client helpers for Supabase PostgreSQL,
isolating all database queries away from application modules.
"""

from __future__ import annotations

from backend.database.repositories import (
    BookingRepository,
    MachineRepository,
    ProductRepository,
    UserRepository,
    product_database_status,
    rental_database_status,
)
from backend.database.supabase import SupabaseDatabaseError, check_connection
from backend.supabase_client import (
    get_supabase_client,
    get_supabase_url,
    is_supabase_configured,
)
from utils.database import PBKDF2_ITERATIONS, hash_password, verify_password

__all__ = [
    "BookingRepository",
    "MachineRepository",
    "ProductRepository",
    "UserRepository",
    "SupabaseDatabaseError",
    "check_connection",
    "product_database_status",
    "rental_database_status",
    "get_supabase_client",
    "get_supabase_url",
    "is_supabase_configured",
    "hash_password",
    "verify_password",
    "PBKDF2_ITERATIONS",
]

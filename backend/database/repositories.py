"""
backend/database/repositories.py
================================
Supabase PostgreSQL repositories for AgriVision.

Provides isolated database access functions for:
1. Product Registry (Module 5)
2. Rental Users (Module 7)
3. Machine Listings (Module 7)
4. Rental Bookings (Module 7)

These functions mirror the business operations currently performed via SQLite
in `utils/database.py`, `modules/product_verifier.py`, and `modules/equipment_rental.py`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.database.supabase import SupabaseDatabaseError
from backend.supabase_client import get_supabase_client

logger = logging.getLogger("agrivision.repositories")


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# 1. Product Registry Repository (Module 5)
# =============================================================================

class ProductRepository:
    """Supabase repository for verified agricultural products."""

    @staticmethod
    def get_by_code(code: str) -> Optional[Dict[str, Any]]:
        """Look up a single product by its unique code."""
        client = get_supabase_client()
        normalized = (code or "").strip().upper()
        if not normalized:
            return None
        response = client.table("products").select("*").eq("code", normalized).limit(1).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def list_all(limit: int = 100) -> List[Dict[str, Any]]:
        """List products ordered by code, up to the given limit."""
        client = get_supabase_client()
        response = (
            client.table("products")
            .select("code, product_name, manufacturer, batch, expiry, status, product_type")
            .order("code")
            .limit(limit)
            .execute()
        )
        return response.data or []

    @staticmethod
    def count() -> int:
        """Total count of products registered in the database."""
        client = get_supabase_client()
        response = client.table("products").select("code", count="exact").execute()
        return response.count if response.count is not None else len(response.data)

    @staticmethod
    def insert(product: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single product."""
        client = get_supabase_client()
        payload = {
            "code": product["code"].strip().upper(),
            "product_name": product["product_name"],
            "manufacturer": product["manufacturer"],
            "batch": product.get("batch"),
            "expiry": product.get("expiry"),
            "status": product.get("status", "Verified"),
            "product_type": product.get("product_type"),
            "registered_on": product.get("registered_on") or _utc_now_iso(),
        }
        response = client.table("products").insert(payload).execute()
        if not response.data:
            raise SupabaseDatabaseError("Failed to insert product record.")
        return response.data[0]

    @staticmethod
    def insert_bulk(products: List[Dict[str, Any]]) -> int:
        """Insert multiple products in batch."""
        if not products:
            return 0
        client = get_supabase_client()
        now = _utc_now_iso()
        rows = [
            {
                "code": p["code"].strip().upper(),
                "product_name": p["product_name"],
                "manufacturer": p["manufacturer"],
                "batch": p.get("batch"),
                "expiry": p.get("expiry"),
                "status": p.get("status", "Verified"),
                "product_type": p.get("product_type"),
                "registered_on": p.get("registered_on") or now,
            }
            for p in products
        ]
        response = client.table("products").insert(rows).execute()
        return len(response.data) if response.data else 0


# =============================================================================
# 2. Rental User Repository (Module 7)
# =============================================================================

class UserRepository:
    """Supabase repository for rental accounts (farmers and equipment owners)."""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Public user record by ID (excludes password_hash)."""
        client = get_supabase_client()
        response = client.table("users").select("*").eq("id", user_id).limit(1).execute()
        if not response.data:
            return None
        user = response.data[0]
        user.pop("password_hash", None)
        return user

    @staticmethod
    def get_by_username(username: str, include_password_hash: bool = False) -> Optional[Dict[str, Any]]:
        """Look up user by unique username (lowercase)."""
        client = get_supabase_client()
        normalized = (username or "").strip().lower()
        if not normalized:
            return None
        response = client.table("users").select("*").eq("username", normalized).limit(1).execute()
        if not response.data:
            return None
        user = response.data[0]
        if not include_password_hash:
            user.pop("password_hash", None)
        return user

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        role: str = "farmer",
        full_name: str = "",
        phone: str = "",
        location: str = "",
    ) -> Dict[str, Any]:
        """Create a new user account and return the public record."""
        client = get_supabase_client()
        normalized = (username or "").strip().lower()
        payload = {
            "username": normalized,
            "password_hash": password_hash,
            "role": role,
            "full_name": full_name.strip(),
            "phone": phone.strip(),
            "location": location.strip(),
            "created_at": _utc_now_iso(),
        }
        response = client.table("users").insert(payload).execute()
        if not response.data:
            raise SupabaseDatabaseError("Failed to create user.")
        user = response.data[0]
        user.pop("password_hash", None)
        return user

    @staticmethod
    def count() -> int:
        """Total user count."""
        client = get_supabase_client()
        response = client.table("users").select("id", count="exact").execute()
        return response.count if response.count is not None else len(response.data)


# =============================================================================
# 3. Machine Listings Repository (Module 7)
# =============================================================================

class MachineRepository:
    """Supabase repository for rental equipment listings."""

    @staticmethod
    def get_by_id(machine_id: int) -> Optional[Dict[str, Any]]:
        """Fetch machine detail with owner information."""
        client = get_supabase_client()
        # Prefer the view_machine_listings view if available, or joined query
        try:
            response = client.table("view_machine_listings").select("*").eq("id", machine_id).limit(1).execute()
            if response.data:
                return response.data[0]
        except Exception:
            # Fallback to direct table join via PostgREST
            pass

        response = (
            client.table("machines")
            .select("*, users:owner_id(username, full_name, phone)")
            .eq("id", machine_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        row = response.data[0]
        owner = row.pop("users", {}) or {}
        row["owner_username"] = owner.get("username")
        row["owner_name"] = owner.get("full_name")
        row["owner_phone"] = owner.get("phone")
        return row

    @staticmethod
    def list_machines(
        location: Optional[str] = None,
        machine_type: Optional[str] = None,
        owner_id: Optional[int] = None,
        include_unavailable: bool = True,
    ) -> List[Dict[str, Any]]:
        """List machines with optional filters."""
        client = get_supabase_client()
        query = client.table("view_machine_listings").select("*")

        if location:
            query = query.ilike("location", f"%{location.strip()}%")
        if machine_type and machine_type != "Any":
            query = query.eq("machine_type", machine_type)
        if owner_id is not None:
            query = query.eq("owner_id", owner_id)
        if not include_unavailable:
            query = query.eq("available", True)

        query = query.order("available", desc=True).order("daily_rate")
        response = query.execute()
        return response.data or []

    @staticmethod
    def create(
        owner_id: int,
        name: str,
        machine_type: str,
        hourly_rate: float,
        daily_rate: float,
        location: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Insert a machine listing."""
        client = get_supabase_client()
        now = _utc_now_iso()
        payload = {
            "name": name.strip(),
            "machine_type": machine_type,
            "hourly_rate": float(hourly_rate),
            "daily_rate": float(daily_rate),
            "location": location.strip(),
            "owner_id": int(owner_id),
            "description": description.strip(),
            "available": True,
            "created_at": now,
            "updated_at": now,
        }
        response = client.table("machines").insert(payload).execute()
        if not response.data:
            raise SupabaseDatabaseError("Failed to create machine listing.")
        return response.data[0]

    @staticmethod
    def update(machine_id: int, owner_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update machine listing owned by owner_id."""
        client = get_supabase_client()
        payload = dict(updates)
        payload["updated_at"] = _utc_now_iso()
        response = (
            client.table("machines")
            .update(payload)
            .eq("id", machine_id)
            .eq("owner_id", owner_id)
            .execute()
        )
        return response.data[0] if response.data else None

    @staticmethod
    def delete(machine_id: int, owner_id: int) -> bool:
        """Delete machine listing owned by owner_id (cascade deletes bookings)."""
        client = get_supabase_client()
        response = (
            client.table("machines")
            .delete()
            .eq("id", machine_id)
            .eq("owner_id", owner_id)
            .execute()
        )
        return bool(response.data)

    @staticmethod
    def count() -> int:
        """Total machines listed."""
        client = get_supabase_client()
        response = client.table("machines").select("id", count="exact").execute()
        return response.count if response.count is not None else len(response.data)


# =============================================================================
# 4. Booking Repository (Module 7)
# =============================================================================

class BookingRepository:
    """Supabase repository for equipment bookings and overlap validation."""

    @staticmethod
    def get_by_id(booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID with joined machine and farmer data."""
        client = get_supabase_client()
        response = client.table("view_booking_details").select("*").eq("id", booking_id).limit(1).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def list_for_machine(machine_id: int) -> List[Dict[str, Any]]:
        """List all bookings for a specific machine."""
        client = get_supabase_client()
        response = (
            client.table("view_booking_details")
            .select("*")
            .eq("machine_id", machine_id)
            .order("start_date", desc=True)
            .execute()
        )
        return response.data or []

    @staticmethod
    def list_for_farmer(farmer_id: int) -> List[Dict[str, Any]]:
        """List all bookings requested by a farmer."""
        client = get_supabase_client()
        response = (
            client.table("view_booking_details")
            .select("*")
            .eq("farmer_id", farmer_id)
            .order("start_date", desc=True)
            .execute()
        )
        return response.data or []

    @staticmethod
    def list_for_owner(owner_id: int) -> List[Dict[str, Any]]:
        """List all bookings for machines belonging to an owner."""
        client = get_supabase_client()
        response = (
            client.table("view_booking_details")
            .select("*")
            .eq("owner_id", owner_id)
            .order("start_date", desc=True)
            .execute()
        )
        return response.data or []

    @staticmethod
    def find_overlapping(machine_id: int, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """
        Check for any active booking that overlaps the requested date range.

        Overlap rule: existing.start <= requested.end AND requested.start <= existing.end
        """
        client = get_supabase_client()
        response = (
            client.table("view_booking_details")
            .select("*")
            .eq("machine_id", machine_id)
            .neq("status", "cancelled")
            .lte("start_date", end_date)
            .gte("end_date", start_date)
            .order("start_date")
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    @staticmethod
    def create(
        machine_id: int,
        farmer_id: int,
        start_date: str,
        end_date: str,
        total_cost: float,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Create a confirmed booking record."""
        client = get_supabase_client()
        payload = {
            "machine_id": int(machine_id),
            "farmer_id": int(farmer_id),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_cost": float(total_cost),
            "status": "confirmed",
            "notes": (notes or "").strip(),
            "created_at": _utc_now_iso(),
        }
        response = client.table("bookings").insert(payload).execute()
        if not response.data:
            raise SupabaseDatabaseError("Failed to create booking.")
        return response.data[0]

    @staticmethod
    def cancel(booking_id: int, user_id: int) -> bool:
        """
        Cancel a booking. Only allowed if user is farmer or machine owner.
        """
        client = get_supabase_client()
        booking = BookingRepository.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found.")
        if int(user_id) not in {int(booking["farmer_id"]), int(booking["owner_id"])}:
            raise PermissionError("Only the farmer or the machine owner can cancel this booking.")

        response = (
            client.table("bookings")
            .update({"status": "cancelled"})
            .eq("id", booking_id)
            .execute()
        )
        return bool(response.data)

    @staticmethod
    def count() -> int:
        """Total bookings count."""
        client = get_supabase_client()
        response = client.table("bookings").select("id", count="exact").execute()
        return response.count if response.count is not None else len(response.data)


# =============================================================================
# 5. Database Status Aggregators
# =============================================================================

def rental_database_status() -> Dict[str, Any]:
    """Summary counts for the Equipment Rental page."""
    try:
        return {
            "available": True,
            "users": UserRepository.count(),
            "machines": MachineRepository.count(),
            "bookings": BookingRepository.count(),
        }
    except Exception as exc:
        return {"available": False, "error": str(exc), "users": 0, "machines": 0, "bookings": 0}


def product_database_status() -> Dict[str, Any]:
    """Summary counts for the Product Verifier page."""
    try:
        count = ProductRepository.count()
        return {
            "available": count > 0,
            "count": count,
            "backend": "supabase",
        }
    except Exception as exc:
        return {"available": False, "count": 0, "error": str(exc)}

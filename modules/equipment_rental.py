"""
modules/equipment_rental.py
===========================
MODULE 7 - Equipment Rental Marketplace (functional MVP).

Roles
-----
* ``farmer``  - browses machines and books them.
* ``owner``   - lists, updates and removes their machines.

Implemented on SQLite (``utils/database.py``):

* simple authentication (username + salted PBKDF2 password hash),
* machine listings with full CRUD (create / read / update / delete),
* bookings with **overlap prevention**: a machine cannot be double-booked for
  overlapping dates.

Explicitly out of scope (per the brief): payments and reviews.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from utils.database import (
    RENTAL_DB_PATH,
    execute,
    fetch_all,
    fetch_one,
    hash_password,
    init_rental_db,
    rental_db_status,
    verify_password,
)
from utils.helpers import timestamp

MACHINE_TYPES: List[str] = [
    "Tractor",
    "Harvester",
    "Rotavator",
    "Sprayer",
    "Seed Drill",
    "Thresher",
    "Power Tiller",
    "Trailer",
    "Other",
]

ROLES: Dict[str, str] = {"farmer": "Farmer", "owner": "Machine Owner"}

def _parse_date(value: Any) -> Optional[date]:
    """Accept ``date`` objects or ``YYYY-MM-DD`` strings."""
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None

# Authentication

def register_user(
    username: str,
    password: str,
    role: str = "farmer",
    full_name: str = "",
    phone: str = "",
    location: str = "",
    db_path: Any = RENTAL_DB_PATH,
) -> Dict[str, Any]:
    """Create an account. Returns ``{"ok", "user", "error"}``."""
    username = (username or "").strip().lower()
    if len(username) < 3:
        return {"ok": False, "user": None, "error": "Username must be at least 3 characters."}
    if len(password or "") < 6:
        return {"ok": False, "user": None, "error": "Password must be at least 6 characters."}
    if role not in ROLES:
        return {"ok": False, "user": None, "error": f"Role must be one of {list(ROLES)}."}

    init_rental_db(db_path)
    if fetch_one(db_path, "SELECT id FROM users WHERE username = ?", (username,)):
        return {"ok": False, "user": None, "error": "That username is already taken."}

    try:
        user_id = execute(
            db_path,
            """
            INSERT INTO users (username, password_hash, role, full_name, phone, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, hash_password(password), role, full_name.strip(), phone.strip(),
             location.strip(), timestamp()),
        )
    except sqlite3.Error as exc:
        return {"ok": False, "user": None, "error": f"Could not create the account: {exc}"}

    return {"ok": True, "user": get_user(int(user_id), db_path), "error": None}

def login_user(username: str, password: str, db_path: Any = RENTAL_DB_PATH) -> Dict[str, Any]:
    """Verify credentials. Returns ``{"ok", "user", "error"}``."""
    init_rental_db(db_path)
    username = (username or "").strip().lower()
    if not username or not password:
        return {"ok": False, "user": None, "error": "Please enter both username and password."}

    record = fetch_one(db_path, "SELECT * FROM users WHERE username = ?", (username,))
    if not record or not verify_password(password, record["password_hash"]):
        return {"ok": False, "user": None, "error": "Invalid username or password."}

    user = {key: value for key, value in record.items() if key != "password_hash"}
    return {"ok": True, "user": user, "error": None}

def get_user(user_id: int, db_path: Any = RENTAL_DB_PATH) -> Optional[Dict[str, Any]]:
    """Public user record (never includes the password hash)."""
    record = fetch_one(db_path, "SELECT * FROM users WHERE id = ?", (user_id,))
    if not record:
        return None
    return {key: value for key, value in record.items() if key != "password_hash"}

# Machine listings (Create / Read / Update / Delete)

MACHINE_SELECT = """
SELECT m.*, u.username AS owner_username, u.full_name AS owner_name, u.phone AS owner_phone,
       (SELECT COUNT(*) FROM bookings b
         WHERE b.machine_id = m.id AND b.status != 'cancelled'
           AND date(b.end_date) >= date('now')) AS upcoming_bookings
FROM machines m
JOIN users u ON u.id = m.owner_id
"""

def list_machines(
    location: Optional[str] = None,
    machine_type: Optional[str] = None,
    owner_id: Optional[int] = None,
    include_unavailable: bool = True,
    db_path: Any = RENTAL_DB_PATH,
) -> List[Dict[str, Any]]:
    """Read machines with optional location / type / owner filters."""
    init_rental_db(db_path)
    clauses: List[str] = []
    params: List[Any] = []
    if location:
        clauses.append("LOWER(m.location) LIKE ?")
        params.append(f"%{location.strip().lower()}%")
    if machine_type and machine_type != "Any":
        clauses.append("m.machine_type = ?")
        params.append(machine_type)
    if owner_id is not None:
        clauses.append("m.owner_id = ?")
        params.append(owner_id)
    if not include_unavailable:
        clauses.append("m.available = 1")

    sql = MACHINE_SELECT + (" WHERE " + " AND ".join(clauses) if clauses else "")
    sql += " ORDER BY m.available DESC, m.daily_rate ASC"
    try:
        return fetch_all(db_path, sql, params)
    except sqlite3.Error:
        return []

def get_machine(machine_id: int, db_path: Any = RENTAL_DB_PATH) -> Optional[Dict[str, Any]]:
    """Read one machine by id."""
    init_rental_db(db_path)
    return fetch_one(db_path, MACHINE_SELECT + " WHERE m.id = ?", (machine_id,))

def add_machine(
    owner_id: int,
    name: str,
    machine_type: str,
    hourly_rate: float,
    daily_rate: float,
    location: str,
    description: str = "",
    db_path: Any = RENTAL_DB_PATH,
) -> Dict[str, Any]:
    """Create a machine listing owned by ``owner_id``."""
    init_rental_db(db_path)
    if not (name or "").strip():
        return {"ok": False, "machine_id": None, "error": "Machine name is required."}
    if not (location or "").strip():
        return {"ok": False, "machine_id": None, "error": "Location is required."}
    if float(hourly_rate) <= 0 or float(daily_rate) <= 0:
        return {"ok": False, "machine_id": None, "error": "Rates must be greater than zero."}

    try:
        machine_id = execute(
            db_path,
            """
            INSERT INTO machines (name, machine_type, hourly_rate, daily_rate, location, owner_id,
                                  description, available, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (name.strip(), machine_type, float(hourly_rate), float(daily_rate),
             location.strip(), int(owner_id), description.strip(), timestamp(), timestamp()),
        )
    except sqlite3.Error as exc:
        return {"ok": False, "machine_id": None, "error": f"Could not add the machine: {exc}"}
    return {"ok": True, "machine_id": int(machine_id), "error": None}

def update_machine(
    machine_id: int,
    owner_id: int,
    name: Optional[str] = None,
    machine_type: Optional[str] = None,
    hourly_rate: Optional[float] = None,
    daily_rate: Optional[float] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    available: Optional[bool] = None,
    db_path: Any = RENTAL_DB_PATH,
) -> Dict[str, Any]:
    """Update a listing - only the owner of the machine may do this."""
    machine = get_machine(machine_id, db_path)
    if not machine:
        return {"ok": False, "error": "Machine not found."}
    if int(machine["owner_id"]) != int(owner_id):
        return {"ok": False, "error": "You can only edit machines that you listed."}

    fields: Dict[str, Any] = {}
    if name is not None:
        fields["name"] = name.strip()
    if machine_type is not None:
        fields["machine_type"] = machine_type
    if hourly_rate is not None:
        fields["hourly_rate"] = float(hourly_rate)
    if daily_rate is not None:
        fields["daily_rate"] = float(daily_rate)
    if location is not None:
        fields["location"] = location.strip()
    if description is not None:
        fields["description"] = description.strip()
    if available is not None:
        fields["available"] = 1 if available else 0

    if not fields:
        return {"ok": False, "error": "Nothing to update."}
    if fields.get("hourly_rate") is not None and fields["hourly_rate"] <= 0:
        return {"ok": False, "error": "Hourly rate must be greater than zero."}
    if fields.get("daily_rate") is not None and fields["daily_rate"] <= 0:
        return {"ok": False, "error": "Daily rate must be greater than zero."}

    fields["updated_at"] = timestamp()
    assignments = ", ".join(f"{column} = ?" for column in fields)
    try:
        execute(
            db_path,
            f"UPDATE machines SET {assignments} WHERE id = ? AND owner_id = ?",
            [*fields.values(), machine_id, owner_id],
        )
    except sqlite3.Error as exc:
        return {"ok": False, "error": f"Could not update the machine: {exc}"}
    return {"ok": True, "error": None}

def delete_machine(machine_id: int, owner_id: int, db_path: Any = RENTAL_DB_PATH) -> Dict[str, Any]:
    """Delete a listing (and its bookings, via ``ON DELETE CASCADE``)."""
    machine = get_machine(machine_id, db_path)
    if not machine:
        return {"ok": False, "error": "Machine not found."}
    if int(machine["owner_id"]) != int(owner_id):
        return {"ok": False, "error": "You can only delete machines that you listed."}
    try:
        execute(
            db_path, "DELETE FROM machines WHERE id = ? AND owner_id = ?", (machine_id, owner_id)
        )
    except sqlite3.Error as exc:
        return {"ok": False, "error": f"Could not delete the machine: {exc}"}
    return {"ok": True, "error": None}

# Bookings (Create / Read + overlap prevention)

BOOKING_SELECT = """
SELECT b.*, m.name AS machine_name, m.machine_type, m.hourly_rate, m.daily_rate,
       m.location AS machine_location, m.owner_id,
       f.username AS farmer_username, f.full_name AS farmer_name, f.phone AS farmer_phone
FROM bookings b
JOIN machines m ON m.id = b.machine_id
JOIN users f ON f.id = b.farmer_id
"""

def bookings_for_machine(machine_id: int, db_path: Any = RENTAL_DB_PATH) -> List[Dict[str, Any]]:
    """All bookings of one machine (newest first)."""
    init_rental_db(db_path)
    return fetch_all(
        db_path,
        BOOKING_SELECT + " WHERE b.machine_id = ? ORDER BY date(b.start_date) DESC",
        (machine_id,),
    )

def bookings_for_farmer(farmer_id: int, db_path: Any = RENTAL_DB_PATH) -> List[Dict[str, Any]]:
    """All bookings made by one farmer."""
    init_rental_db(db_path)
    return fetch_all(
        db_path,
        BOOKING_SELECT + " WHERE b.farmer_id = ? ORDER BY date(b.start_date) DESC",
        (farmer_id,),
    )

def bookings_for_owner(owner_id: int, db_path: Any = RENTAL_DB_PATH) -> List[Dict[str, Any]]:
    """All bookings received for the machines of one owner."""
    init_rental_db(db_path)
    return fetch_all(
        db_path,
        BOOKING_SELECT + " WHERE m.owner_id = ? ORDER BY date(b.start_date) DESC",
        (owner_id,),
    )

def find_overlapping_booking(
    machine_id: int, start_date: Any, end_date: Any, db_path: Any = RENTAL_DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    Return an existing (non-cancelled) booking that overlaps the requested range.

    Inclusive-range overlap test::

        existing.start <= requested.end  AND  requested.start <= existing.end
    """
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end:
        return None
    init_rental_db(db_path)
    return fetch_one(
        db_path,
        BOOKING_SELECT
        + """
        WHERE b.machine_id = ?
          AND b.status != 'cancelled'
          AND date(b.start_date) <= date(?)
          AND date(?) <= date(b.end_date)
        ORDER BY date(b.start_date) LIMIT 1
        """,
        (machine_id, end.isoformat(), start.isoformat()),
    )

def estimate_cost(machine: Dict[str, Any], start_date: Any, end_date: Any) -> Dict[str, Any]:
    """Inclusive-day cost estimate (daily rate x number of days)."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end or end < start:
        return {"days": 0, "total_cost": 0.0, "daily_rate": None}
    days = (end - start).days + 1
    daily_rate = float(machine.get("daily_rate") or 0.0)
    return {"days": days, "total_cost": round(daily_rate * days, 2), "daily_rate": daily_rate}

def create_booking(
    machine_id: int,
    farmer_id: int,
    start_date: Any,
    end_date: Any,
    notes: str = "",
    db_path: Any = RENTAL_DB_PATH,
) -> Dict[str, Any]:
    """
    Book a machine for an inclusive date range.

    Rejects: unknown machine, unavailable machine, invalid or past dates, and -
    most importantly - any range that overlaps an existing booking of the same
    machine (no double booking).
    """
    machine = get_machine(machine_id, db_path)
    if not machine:
        return {"ok": False, "booking_id": None, "error": "Machine not found."}
    if not machine.get("available"):
        return {
            "ok": False, "booking_id": None,
            "error": "This machine is currently marked unavailable.",
        }

    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end:
        return {"ok": False, "booking_id": None, "error": "Please pick valid start and end dates."}
    if end < start:
        return {
            "ok": False, "booking_id": None,
            "error": "The end date must be on or after the start date.",
        }
    if start < date.today():
        return {"ok": False, "booking_id": None, "error": "The start date cannot be in the past."}

    clash = find_overlapping_booking(machine_id, start, end, db_path)
    if clash:
        return {
            "ok": False,
            "booking_id": None,
            "error": (
                f"This machine is already booked from {clash['start_date']} to {clash['end_date']}"
                f" by {clash.get('farmer_name') or clash.get('farmer_username')}. "
                "Please choose different dates."
            ),
            "clash": clash,
        }

    cost = estimate_cost(machine, start, end)
    try:
        booking_id = execute(
            db_path,
            """
            INSERT INTO bookings (machine_id, farmer_id, start_date, end_date, total_cost, status,
                                  notes, created_at)
            VALUES (?, ?, ?, ?, ?, 'confirmed', ?, ?)
            """,
            (machine_id, int(farmer_id), start.isoformat(), end.isoformat(),
             cost["total_cost"], notes.strip(), timestamp()),
        )
    except sqlite3.Error as exc:
        return {"ok": False, "booking_id": None, "error": f"Could not save the booking: {exc}"}

    return {
        "ok": True,
        "booking_id": int(booking_id),
        "error": None,
        "days": cost["days"],
        "total_cost": cost["total_cost"],
    }

def cancel_booking(booking_id: int, user_id: int, db_path: Any = RENTAL_DB_PATH) -> Dict[str, Any]:
    """
    Cancel a booking.

    Allowed for the farmer who booked it and for the owner of the machine - it
    keeps the demo marketplace usable without introducing payments (payments and
    reviews are explicitly out of scope).
    """
    booking = fetch_one(
        db_path,
        """
        SELECT b.*, m.owner_id FROM bookings b
        JOIN machines m ON m.id = b.machine_id
        WHERE b.id = ?
        """,
        (booking_id,),
    )
    if not booking:
        return {"ok": False, "error": "Booking not found."}
    if int(user_id) not in {int(booking["farmer_id"]), int(booking["owner_id"])}:
        return {
            "ok": False,
            "error": "Only the farmer or the machine owner can cancel this booking.",
        }
    try:
        execute(db_path, "UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    except sqlite3.Error as exc:
        return {"ok": False, "error": f"Could not cancel the booking: {exc}"}
    return {"ok": True, "error": None}

def marketplace_status(db_path: Any = RENTAL_DB_PATH) -> Dict[str, Any]:
    """Counts + demo credentials used by the UI (initialises the DB if needed)."""
    try:
        init_rental_db(db_path)
    except sqlite3.Error:  # pragma: no cover - defensive
        pass
    status = rental_db_status(db_path)
    status["demo_accounts"] = [
        {"username": "farmer_demo", "password": "farmer123", "role": "farmer"},
        {"username": "owner_demo", "password": "owner123", "role": "owner"},
    ]
    return status

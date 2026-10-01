"""
utils/database.py
=================
Small SQLite helper layer shared by Module 5 (product registry) and Module 7
(equipment rental marketplace).

Contents
--------
* ``get_connection``  - context-managed connection with row access by name
* ``hash_password`` / ``verify_password`` - salted PBKDF2-SHA256 (stdlib only)
* ``init_products_db``  - product registry schema + demo rows
* ``init_rental_db``    - users / machines / bookings schema + demo rows
* tiny ``fetch_all`` / ``fetch_one`` / ``execute`` helpers

Everything is local SQLite - no server, no ORM, no external service.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from utils.helpers import PRODUCTS_DB_PATH, RENTAL_DB_PATH, timestamp

PBKDF2_ITERATIONS = 120_000

# Connection helpers

@contextmanager
def get_connection(db_path: "Path | str") -> Iterator[sqlite3.Connection]:
    """Context-managed SQLite connection (row access by column name)."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def fetch_all(
    db_path: "Path | str", sql: str, params: Iterable[Any] = ()
) -> List[Dict[str, Any]]:
    """Run a SELECT and return all rows as dictionaries."""
    with get_connection(db_path) as connection:
        return [dict(row) for row in connection.execute(sql, tuple(params)).fetchall()]

def fetch_one(
    db_path: "Path | str", sql: str, params: Iterable[Any] = ()
) -> Optional[Dict[str, Any]]:
    """Run a SELECT and return the first row (or ``None``)."""
    with get_connection(db_path) as connection:
        row = connection.execute(sql, tuple(params)).fetchone()
        return dict(row) if row else None

def execute(db_path: "Path | str", sql: str, params: Iterable[Any] = ()) -> int:
    """Run an INSERT/UPDATE/DELETE and return ``lastrowid`` (or rowcount)."""
    with get_connection(db_path) as connection:
        cursor = connection.execute(sql, tuple(params))
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

# Password hashing (stdlib PBKDF2 - no extra dependency)

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """``pbkdf2_sha256$iterations$salt$hash`` - safe to store in SQLite."""
    if not password:
        raise ValueError("Password must not be empty.")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of a password against a stored hash."""
    try:
        algorithm, iterations, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except (ValueError, AttributeError, TypeError):
        return False

# MODULE 5 - product registry

PRODUCTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    code          TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    manufacturer  TEXT NOT NULL,
    batch         TEXT,
    expiry        TEXT,
    status        TEXT NOT NULL DEFAULT 'Verified',
    product_type  TEXT,
    registered_on TEXT
);
"""

#: Demo registry.  A real deployment would query a trusted manufacturer /
#: authorised-registry database; this is clearly a *simulated* college demo
#: database, exactly as described in the project brief for Module 5.
DEMO_PRODUCTS: List[Dict[str, Any]] = [
    {
        "code": "AGV-1001",
        "product_name": "AgriShield Mancozeb 75% WP",
        "manufacturer": "Demo Agro Chemicals Pvt Ltd",
        "batch": "MCZ-2405",
        "expiry": "2027-04-30",
        "status": "Verified",
        "product_type": "Fungicide",
    },
    {
        "code": "AGV-1002",
        "product_name": "AgriShield Neem Oil 1500 ppm",
        "manufacturer": "Demo Agro Chemicals Pvt Ltd",
        "batch": "NEM-2312",
        "expiry": "2026-12-31",
        "status": "Verified",
        "product_type": "Bio-pesticide",
    },
    {
        "code": "AGV-1003",
        "product_name": "GreenGrow Urea 46% N",
        "manufacturer": "Demo Fertiliser Cooperative",
        "batch": "URE-2501",
        "expiry": "2028-06-30",
        "status": "Verified",
        "product_type": "Fertilizer",
    },
    {
        "code": "AGV-1004",
        "product_name": "GreenGrow DAP 18-46-0",
        "manufacturer": "Demo Fertiliser Cooperative",
        "batch": "DAP-2410",
        "expiry": "2028-01-31",
        "status": "Verified",
        "product_type": "Fertilizer",
    },
    {
        "code": "AGV-1005",
        "product_name": "CropCare Imidacloprid 17.8% SL",
        "manufacturer": "Demo Crop Science Ltd",
        "batch": "IMD-2308",
        "expiry": "2026-03-15",
        "status": "Recalled",
        "product_type": "Insecticide",
    },
    {
        "code": "AGV-1006",
        "product_name": "CropCare Glyphosate 41% SL",
        "manufacturer": "Demo Crop Science Ltd",
        "batch": "GLY-2201",
        "expiry": "2025-11-30",
        "status": "Verified",
        "product_type": "Herbicide",
    },
    {
        "code": "AGV-1007",
        "product_name": "SoilBoost Bio-fertiliser (Azotobacter)",
        "manufacturer": "Demo Bio Inputs",
        "batch": "BIO-2502",
        "expiry": "2027-05-31",
        "status": "Verified",
        "product_type": "Bio-fertilizer",
    },
    {
        "code": "AGV-1008",
        "product_name": "SoilBoost Zinc Sulphate 21%",
        "manufacturer": "Demo Bio Inputs",
        "batch": "ZNS-2411",
        "expiry": "2029-02-28",
        "status": "Verified",
        "product_type": "Micronutrient",
    },
    {
        "code": "AGV-1009",
        "product_name": "HarvestPlus MOP (Muriate of Potash)",
        "manufacturer": "Demo Fertiliser Cooperative",
        "batch": "MOP-2409",
        "expiry": "2028-09-30",
        "status": "Verified",
        "product_type": "Fertilizer",
    },
    {
        "code": "AGV-1010",
        "product_name": "HarvestPlus Sulphur 90% WDG",
        "manufacturer": "Demo Fertiliser Cooperative",
        "batch": "SUL-2306",
        "expiry": "2027-08-31",
        "status": "Suspended",
        "product_type": "Fungicide",
    },
]

def init_products_db(db_path: "Path | str" = PRODUCTS_DB_PATH, force: bool = False) -> Path:
    """Create the product registry table and (on first run) insert the demo rows."""
    path = Path(db_path)
    with get_connection(path) as connection:
        connection.executescript(PRODUCTS_SCHEMA)
        if force:
            connection.execute("DELETE FROM products")
        existing = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if not existing:
            connection.executemany(
                """
                INSERT INTO products
                    (code, product_name, manufacturer, batch, expiry, status,
                     product_type, registered_on)
                VALUES (:code, :product_name, :manufacturer, :batch, :expiry,
                        :status, :product_type, :registered_on)
                """,
                [{**row, "registered_on": timestamp()} for row in DEMO_PRODUCTS],
            )
    return path

def product_registry_count(db_path: "Path | str" = PRODUCTS_DB_PATH) -> int:
    """Number of products currently stored (0 when the database is missing)."""
    try:
        row = fetch_one(db_path, "SELECT COUNT(*) AS total FROM products")
        return int(row["total"]) if row else 0
    except sqlite3.Error:
        return 0

# MODULE 7 - equipment rental marketplace

RENTAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('farmer', 'owner')),
    full_name     TEXT,
    phone         TEXT,
    location      TEXT,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS machines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    machine_type TEXT,
    hourly_rate  REAL NOT NULL,
    daily_rate   REAL NOT NULL,
    location     TEXT,
    owner_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description  TEXT,
    available    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT,
    updated_at   TEXT
);

CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id  INTEGER NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    farmer_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    total_cost  REAL,
    status      TEXT NOT NULL DEFAULT 'confirmed',
    notes       TEXT,
    created_at  TEXT
);
"""

DEMO_USERS = [
    {
        "username": "farmer_demo",
        "password": "farmer123",
        "role": "farmer",
        "full_name": "Ramesh Kumar (demo farmer)",
        "phone": "9000000001",
        "location": "Varanasi",
    },
    {
        "username": "owner_demo",
        "password": "owner123",
        "role": "owner",
        "full_name": "Suresh Singh (demo machine owner)",
        "phone": "9000000002",
        "location": "Varanasi",
    },
]

DEMO_MACHINES = [
    {
        "name": "Mahindra 275 DI Tractor",
        "machine_type": "Tractor",
        "hourly_rate": 800.0,
        "daily_rate": 5200.0,
        "location": "Varanasi",
        "description": "42 HP tractor with plough - suitable for 1-5 acre fields.",
    },
    {
        "name": "Kubota Combine Harvester",
        "machine_type": "Harvester",
        "hourly_rate": 2500.0,
        "daily_rate": 15000.0,
        "location": "Chandauli",
        "description": "Self-propelled harvester for wheat and paddy.",
    },
    {
        "name": "Rotavator (6 feet)",
        "machine_type": "Rotavator",
        "hourly_rate": 600.0,
        "daily_rate": 3800.0,
        "location": "Varanasi",
        "description": "Soil preparation attachment, needs a 35 HP+ tractor.",
    },
    {
        "name": "Power Sprayer (battery)",
        "machine_type": "Sprayer",
        "hourly_rate": 150.0,
        "daily_rate": 900.0,
        "location": "Ramnagar",
        "description": "16 litre battery sprayer for pesticide / fungicide application.",
    },
]

def init_rental_db(db_path: "Path | str" = RENTAL_DB_PATH, force: bool = False) -> Path:
    """Create the rental tables and seed demo users + machine listings once."""
    path = Path(db_path)
    with get_connection(path) as connection:
        connection.executescript(RENTAL_SCHEMA)
        if force:
            connection.execute("DELETE FROM bookings")
            connection.execute("DELETE FROM machines")
            connection.execute("DELETE FROM users")

        existing_users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if not existing_users:
            for user in DEMO_USERS:
                connection.execute(
                    """
                    INSERT INTO users (username, password_hash, role, full_name, phone,
                                       location, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["username"],
                        hash_password(user["password"]),
                        user["role"],
                        user["full_name"],
                        user["phone"],
                        user["location"],
                        timestamp(),
                    ),
                )

        existing_machines = connection.execute("SELECT COUNT(*) FROM machines").fetchone()[0]
        if not existing_machines:
            owner = connection.execute(
                "SELECT id FROM users WHERE role = 'owner' ORDER BY id LIMIT 1"
            ).fetchone()
            if owner is None:
                owner = connection.execute(
                    "SELECT id FROM users ORDER BY id LIMIT 1"
                ).fetchone()
            owner_id = owner["id"]
            for machine in DEMO_MACHINES:
                connection.execute(
                    """
                    INSERT INTO machines (name, machine_type, hourly_rate, daily_rate, location,
                                          owner_id, description, available, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        machine["name"],
                        machine["machine_type"],
                        machine["hourly_rate"],
                        machine["daily_rate"],
                        machine["location"],
                        owner_id,
                        machine["description"],
                        timestamp(),
                        timestamp(),
                    ),
                )
    return path

def rental_db_status(db_path: "Path | str" = RENTAL_DB_PATH) -> Dict[str, Any]:
    """Counts used by the Equipment Rental page and the dashboard."""
    try:
        users = fetch_one(db_path, "SELECT COUNT(*) AS total FROM users") or {"total": 0}
        machines = fetch_one(db_path, "SELECT COUNT(*) AS total FROM machines") or {"total": 0}
        bookings = fetch_one(db_path, "SELECT COUNT(*) AS total FROM bookings") or {"total": 0}
        return {
            "available": True,
            "users": int(users["total"]),
            "machines": int(machines["total"]),
            "bookings": int(bookings["total"]),
        }
    except sqlite3.Error as exc:  # pragma: no cover - schema problems
        return {"available": False, "error": str(exc), "users": 0, "machines": 0, "bookings": 0}

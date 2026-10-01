"""
modules/product_verifier.py
===========================
MODULE 5 - Agricultural Product Verifier.

Checks a product code against a local SQLite registry created by
``utils.database.init_products_db`` and reports the product identity, batch,
expiry and verification status.

* The registry in this college project is a **simulated demo database** (stated on
  the page).  A real deployment would query a trusted manufacturer /
  authorised-registry API.
* QR codes are decoded with OpenCV's built-in ``QRCodeDetector`` (no extra
  dependency).  Barcode (EAN/UPC) decoding would need an additional library that is
  not part of the AgriVision stack, so manual code entry stays the reliable
  fallback.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from utils.database import (
    PRODUCTS_DB_PATH,
    fetch_all,
    fetch_one,
    init_products_db,
    product_registry_count,
)
from utils.helpers import load_image_from_bytes

CODE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-_/]{2,}")

def normalize_code(raw: str) -> str:
    """Trim and upper-case a code typed / scanned by the user."""
    return str(raw or "").strip().upper()

def extract_code_from_qr_text(text: str) -> str:
    """
    Pull a product code out of decoded QR text.

    QR labels often contain a full URL, so the longest alphanumeric token
    (ignoring common URL parts) is used as the code.
    """
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    candidates = CODE_PATTERN.findall(cleaned.upper())
    codes = [token for token in candidates if not token.startswith(("HTTP", "WWW", "HTTPS"))]
    if not codes:
        return normalize_code(cleaned)
    for token in codes:
        if token.startswith("AGV"):
            return token
    return max(codes, key=len)

def decode_qr_from_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Decode the first QR code found in an uploaded image.

    Returns ``{"code", "raw_text", "error"}``; ``error`` explains the problem when
    no QR code could be read (the UI then asks for manual entry).
    """
    try:
        import cv2
        import numpy as np
    except ImportError:  # pragma: no cover - OpenCV is part of the stack
        return {"code": "", "raw_text": "", "error": "OpenCV is not available for QR decoding."}

    try:
        image = load_image_from_bytes(image_bytes)
    except ValueError as exc:
        return {"code": "", "raw_text": "", "error": str(exc)}

    array = np.asarray(image.convert("RGB"))[:, :, ::-1].copy()  # RGB -> BGR for OpenCV
    try:
        detector = cv2.QRCodeDetector()
        decoded_text, _points, _straight = detector.detectAndDecode(array)
        if not decoded_text:
            return {
                "code": "",
                "raw_text": "",
                "error": (
                    "No QR code was detected in that image. Make sure the code is sharp and "
                    "fills most of the frame, or type the product code manually."
                ),
            }
        return {
            "code": extract_code_from_qr_text(decoded_text),
            "raw_text": decoded_text,
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - OpenCV runtime problem
        return {"code": "", "raw_text": "", "error": f"QR decoding failed: {exc}"}

def _parse_expiry(value: Optional[str]) -> Optional[date]:
    """Parse the stored expiry date (tolerates a few common formats)."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None

def verify_product(code: str, db_path: Any = PRODUCTS_DB_PATH) -> Dict[str, Any]:
    """
    Verify a product code against the registry.

    Returns ``{"found", "verified", "product", "message", "checks", "error"}``.
    ``found`` is ``False`` for unknown codes, which the UI shows as
    "⚠️ Product not found in registry".
    """
    normalized = normalize_code(code)
    if not normalized:
        return {
            "found": False, "verified": False, "product": None,
            "message": "Please enter a product code.", "checks": [], "error": "empty code",
        }

    try:
        init_products_db(db_path)
        product = fetch_one(db_path, "SELECT * FROM products WHERE code = ?", (normalized,))
    except Exception as exc:
        return {
            "found": False, "verified": False, "product": None,
            "message": f"Could not read the product registry: {exc}",
            "checks": [], "error": str(exc),
        }

    if not product:
        return {
            "found": False, "verified": False, "product": None,
            "message": "⚠️ Product not found in registry", "checks": [], "error": None,
        }

    status = str(product.get("status") or "").strip()
    expiry = _parse_expiry(product.get("expiry"))
    today = date.today()
    expired = bool(expiry and expiry < today)

    checks: List[str] = [
        f"Code found in registry: {product['code']}",
        f"Registered status: {status}",
    ]
    if expiry:
        days = (expiry - today).days
        checks.append(
            f"Expiry date {expiry} has passed ({abs(days)} days ago)."
            if expired
            else f"Valid until {expiry} ({days} days remaining)."
        )
    if product.get("batch"):
        checks.append(f"Batch number on record: {product['batch']}")

    verified = status.lower() == "verified" and not expired
    if status.lower() == "recalled":
        message = "🔴 Product has been RECALLED by the manufacturer - do not use it."
    elif status.lower() == "suspended":
        message = "🟠 Product registration is suspended - check with the dealer before buying."
    elif expired:
        message = (
            f"🟠 Product is registered, but the recorded expiry date ({expiry}) has passed - "
            "do not use it."
        )
    elif verified:
        message = "🟢 Product Verified"
    else:
        message = f"🟠 Product status is '{status}' - verify with the manufacturer."

    return {
        "found": True,
        "verified": verified,
        "product": product,
        "message": message,
        "checks": checks,
        "expired": expired,
        "error": None,
    }

def list_registry(db_path: Any = PRODUCTS_DB_PATH, limit: int = 100) -> List[Dict[str, Any]]:
    """All registry rows (used by the 'show registry' expander)."""
    try:
        init_products_db(db_path)
        return fetch_all(
            db_path,
            "SELECT code, product_name, manufacturer, batch, expiry, status, product_type "
            "FROM products ORDER BY code LIMIT ?",
            (limit,),
        )
    except Exception:  # pragma: no cover - defensive
        return []

def verifier_status(db_path: Any = PRODUCTS_DB_PATH) -> Dict[str, Any]:
    """Status dictionary for the UI."""
    try:
        init_products_db(db_path)
        count = product_registry_count(db_path)
        return {
            "available": count > 0,
            "count": count,
            "db_path": str(db_path),
            "simulated": True,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {"available": False, "count": 0, "db_path": str(db_path), "error": str(exc)}

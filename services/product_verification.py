"""
services/product_verification.py
================================
Service for agricultural product authenticity verification and QR scanning
against local SQLite registry.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from modules.product_verifier import decode_qr_from_image, list_registry, verifier_status, verify_product
from utils.database import init_products_db


def verify_product_code(code: str) -> Dict[str, Any]:
    """Verify an agricultural input product code against the SQLite registry."""
    init_products_db()
    return verify_product(code)


def verify_product_qr_image(image_bytes: bytes) -> Dict[str, Any]:
    """Decode QR code from uploaded image and check against registry."""
    init_products_db()
    qr_result = decode_qr_from_image(image_bytes)
    if qr_result.get("error"):
        return {
            "qr": qr_result,
            "verification": {
                "found": False,
                "verified": False,
                "message": qr_result["error"],
                "checks": [],
                "product": None,
                "expired": False,
                "error": qr_result["error"],
            },
        }

    code = qr_result.get("code")
    verification = verify_product(code)
    return {"qr": qr_result, "verification": verification}


def get_registered_products(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve items from the demo product registry."""
    init_products_db()
    return list_registry(limit=limit)


def get_verifier_info() -> Dict[str, Any]:
    """Return status and count of the product database."""
    init_products_db()
    return verifier_status()

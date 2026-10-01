"""Small signed bearer-token helper for rental account endpoints."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict

from dotenv import load_dotenv
from utils.helpers import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env", override=False)
_configured_secret = os.getenv("AGRIVISION_AUTH_SECRET", "").encode("utf-8")
_SECRET = _configured_secret or secrets.token_bytes(32)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def issue_token(user_id: int, role: str, lifetime_seconds: int = 86_400) -> str:
    """Issue a compact HMAC-signed token; the signing key is never returned."""
    payload = _encode(
        json.dumps(
            {"sub": int(user_id), "role": role, "exp": int(time.time()) + lifetime_seconds},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signature = _encode(hmac.new(_SECRET, payload.encode("ascii"), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def read_token(token: str) -> Dict[str, Any]:
    """Validate a token and return its claims, raising ValueError if invalid."""
    try:
        payload, signature = token.split(".", 1)
        expected = _encode(hmac.new(_SECRET, payload.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid token")
        padding = "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload + padding))
        if int(claims["exp"]) <= int(time.time()):
            raise ValueError("expired token")
        if int(claims["sub"]) <= 0 or claims["role"] not in {"farmer", "owner"}:
            raise ValueError("invalid claims")
        return claims
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid token") from exc

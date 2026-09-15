"""HMAC-SHA256 action-token signer (generalized DLQ-resubmit pattern).

Tokens are ``payload_b64url.signature_b64url`` strings. The payload is a
sorted-keys JSON dict with ``exp`` (unix seconds) and ``act`` (action name).
Signature verification uses ``hmac.compare_digest`` for constant time.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from typing import Any


class InvalidActionToken(ValueError):
    """Token is malformed, mis-signed, expired, or scoped to a different action."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def issue_action_token(
    secret: str,
    *,
    action: str,
    ttl_seconds: int = 24 * 60 * 60,
    payload: dict[str, Any] | None = None,
) -> str:
    if not secret:
        raise ValueError("secret must not be empty")
    body: dict[str, Any] = {
        "exp": int(time.time()) + int(ttl_seconds),
        "act": action,
    }
    if payload:
        body.update(payload)
    payload_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(sig)}"


def verify_action_token(
    secret: str,
    token: str,
    *,
    expected_action: str,
) -> dict[str, Any]:
    if not secret:
        raise InvalidActionToken("secret must not be empty")
    if not isinstance(token, str) or "." not in token:
        raise InvalidActionToken("malformed token")
    parts = token.split(".")
    if len(parts) != 2:
        raise InvalidActionToken("malformed token: expected 2 sections")
    payload_part, sig_part = parts
    try:
        payload_bytes = _b64url_decode(payload_part)
        provided_sig = _b64url_decode(sig_part)
    except (ValueError, binascii.Error) as exc:
        raise InvalidActionToken(f"base64 decode failed: {exc}") from exc

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        raise InvalidActionToken("signature mismatch")
    try:
        body = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise InvalidActionToken(f"payload not JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise InvalidActionToken("payload not a JSON object")
    if body.get("act") != expected_action:
        raise InvalidActionToken(
            f"token not scoped to {expected_action!r} (got {body.get('act')!r})"
        )
    exp = body.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise InvalidActionToken("token expired")
    return body


__all__ = [
    "InvalidActionToken",
    "issue_action_token",
    "verify_action_token",
]

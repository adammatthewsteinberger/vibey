"""HMAC signature verification for webhooks."""

from __future__ import annotations

import hashlib
import hmac


def verify_hmac_signature(
    secret: str,
    raw_body: bytes,
    header_value: str,
    *,
    prefix: str = "sha256=",
) -> bool:
    """Constant-time HMAC-SHA256 verify (GitHub/Sumo ``sha256=…`` style).

    Parameters
    ----------
    secret:
        Shared signing secret.
    raw_body:
        Raw request body bytes (must not be re-serialized JSON).
    header_value:
        Value of the signature header (may include ``sha256=`` prefix).
    prefix:
        Expected algorithm prefix in the header value.
    """
    if not secret or not header_value:
        return False
    provided = header_value.strip()
    if provided.startswith(prefix):
        provided = provided[len(prefix) :]
    elif "=" in provided:
        provided = provided.split("=", 1)[1]
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided.lower())


__all__ = ["verify_hmac_signature"]

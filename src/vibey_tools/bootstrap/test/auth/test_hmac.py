"""Auth HMAC tests."""

from __future__ import annotations

import hashlib
import hmac

from vibey_bootstrap.auth import verify_hmac_signature


def test_verify_hmac_valid() -> None:
    body = b'{"ok": true}'
    secret = "s3cret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(secret, body, sig) is True


def test_verify_hmac_invalid() -> None:
    assert verify_hmac_signature("secret", b"body", "sha256=bad") is False

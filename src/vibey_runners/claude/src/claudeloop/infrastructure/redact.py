# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Recursive redaction of secret-shaped keys and credential-looking strings.

Used by structlog, the JSONL audit log, and the per-run events.jsonl sink so
PII/credential masking is consistent everywhere (see SECURITY.md)."""

from __future__ import annotations

import re
from typing import Any, TypeVar

T = TypeVar("T")

REDACTED_VALUE = "***REDACTED***"

_REDACTED_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization_token",
        "access_token",
        "refresh_token",
        "client_secret",
        "secret_value",
        "secret",
        "password",
        "authorization",
        "x-api-key",
        "x_api_key",
        "anthropic_api_key",
        "bearer",
    }
)

# sk-ant-..., sk-..., Bearer tokens, long hex-ish secrets
_CREDENTIAL_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
)


def redact_string(value: str) -> str:
    redacted = value
    for pattern in _CREDENTIAL_PATTERNS:
        redacted = pattern.sub(REDACTED_VALUE, redacted)
    return redacted


def redact(value: T) -> T:
    """Recursively redact secret keys and credential-shaped substrings."""
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if key_str.lower().replace("-", "_") in _REDACTED_KEYS:
                out[key] = REDACTED_VALUE
            else:
                out[key] = redact(item)
        return out  # type: ignore[return-value]
    if isinstance(value, list):
        return [redact(item) for item in value]  # type: ignore[return-value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)  # type: ignore[return-value]
    if isinstance(value, str):
        return redact_string(value)  # type: ignore[return-value]
    return value

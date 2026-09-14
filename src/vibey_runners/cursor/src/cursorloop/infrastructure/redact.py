# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Recursive redaction of secret-shaped keys and Cursor credential strings.

Used as a structlog processor and by audit/event sinks so credential masking
is consistent. Cursor API keys use the fixed ``crsr_`` prefix — that pattern
is scrubbed even when the key name is innocuous.
"""

from __future__ import annotations

import re
from typing import Any

REDACTED_VALUE = "***"

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
        "cursor_api_key",
        "bearer",
    }
)

_CRSR_PATTERN = re.compile(r"crsr_[A-Za-z0-9]{16,}")


def _normalize_key(key: object) -> str:
    return str(key).lower().replace("-", "_")


def redact_string(value: str) -> str:
    return _CRSR_PATTERN.sub(REDACTED_VALUE, value)


def redact(value: Any) -> Any:
    """Recursively redact secret keys and ``crsr_`` credential substrings."""
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            if _normalize_key(key) in _REDACTED_KEYS:
                out[key] = REDACTED_VALUE
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        return redact_string(value)
    return value


def redact_event(_logger: object, _method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: redact in place and return the event dict."""
    redacted = redact(event_dict)
    if not isinstance(redacted, dict):
        return event_dict
    event_dict.clear()
    event_dict.update(redacted)
    return event_dict

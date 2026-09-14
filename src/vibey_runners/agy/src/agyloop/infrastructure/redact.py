# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Redact credential-shaped keys from snapshot / log payloads."""

from __future__ import annotations

from typing import Any

_SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "access_token",
        "refresh_token",
        "client_secret",
        "google_api_key",
        "x-goog-api-key",
        "private_key",
        "client_email",
    }
)


def redact(value: Any) -> Any:
    """Return a copy of ``value`` with secret-shaped keys replaced by ``***``."""
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, inner in value.items():
            if str(key).lower() in _SECRET_KEYS:
                redacted[str(key)] = "***"
            else:
                redacted[str(key)] = redact(inner)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value

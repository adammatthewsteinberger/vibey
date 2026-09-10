# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Recursive redaction of secret-shaped keys and credential-looking strings."""

from __future__ import annotations

import re

REDACTED_VALUE = "***REDACTED***"

_REDACTED_KEYS = frozenset(
    {
        "openai_api_key",
        "codex_api_key",
        "authorization",
        "access_token",
        "refresh_token",
        "client_secret",
        "api_key",
        "secret_value",
        "secret",
        "password",
        "token",
    }
)

_SK_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{16,}")


def _normalize_key(key: object) -> str:
    return str(key).lower().replace("-", "_")


def redact_string(value: str) -> str:
    return _SK_PATTERN.sub(REDACTED_VALUE, value)


def redact[T](value: T) -> T:
    """Recursively scrub secret keys and ``sk-`` credential substrings."""
    if isinstance(value, dict):
        out: dict[object, object] = {}
        for key, item in value.items():
            if _normalize_key(key) in _REDACTED_KEYS:
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

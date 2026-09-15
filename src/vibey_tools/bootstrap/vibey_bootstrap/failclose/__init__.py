"""Fail-closed-for-auth / fail-open-for-features env helpers.

``ConfigurationError`` is re-exported from :mod:`vibey_bootstrap.models.exceptions`
so callers see a single canonical class regardless of which import path
they use. v1 callers of ``ConfigurationError`` keep working unchanged.

Use:
- :func:`require_env` for tenant_id, connection strings, secrets — anything
  whose absence MUST stop the pipeline.
- :func:`optional_env` for endpoint URLs that have sensible defaults or
  feature flags with documented fallback semantics.
- :func:`fail_open_env` for "feature disabled when None" semantics — comment
  every call site with the threat consequence of the open default.
"""

from __future__ import annotations

import os

from vibey_bootstrap.models.exceptions import ConfigurationError


def require_env(name: str, *, message: str | None = None) -> str:
    """Return ``os.environ[name]`` when truthy; raise ``ConfigurationError`` otherwise."""
    raw = os.environ.get(name, "")
    if not raw or not raw.strip():
        raise ConfigurationError(
            message or f"Required environment variable {name!r} is missing or empty"
        )
    return raw.strip()


def optional_env(name: str, *, default: str = "") -> str:
    """Return ``os.environ.get(name, default).strip()``."""
    return os.environ.get(name, default).strip()


def fail_open_env(name: str) -> str | None:
    """Return the env value when truthy, else None — for "feature disabled" semantics."""
    raw = os.environ.get(name)
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


__all__ = [
    "ConfigurationError",  # alias of v1's class
    "fail_open_env",
    "optional_env",
    "require_env",
]

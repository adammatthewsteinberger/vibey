"""Constant-time comparison + FastAPI API-key helper.

The :func:`compare_secrets` helper centralizes the None/empty/bytes-coercion
dance so call sites can just call it without re-implementing the safe pattern.

The FastAPI API-key helper is fail-open-when-unset by default (matches the
v1 reference behavior); apps that want strict mode pass
``fail_open_when_unset=False``.
"""

from __future__ import annotations

import hmac
import logging

_logger = logging.getLogger(__name__)


def compare_secrets(a: str | bytes | None, b: str | bytes | None) -> bool:
    """Constant-time equality. Returns False on any None / empty input.

    Coerces str to bytes via UTF-8. Bytes inputs pass through unchanged.
    """
    if not a or not b:
        return False
    a_b = a.encode("utf-8") if isinstance(a, str) else a
    b_b = b.encode("utf-8") if isinstance(b, str) else b
    return hmac.compare_digest(a_b, b_b)


async def verify_api_key_header(
    x_api_key: str | None,
    *,
    env_var: str = "API_KEY",
    fail_open_when_unset: bool = True,
) -> None:
    """FastAPI dependency. Raises ``HTTPException(401)`` on mismatch.

    When ``fail_open_when_unset`` is True (default) and the env var is unset
    or empty, the check passes — matches the v1 reference behavior. Strict
    mode (env required) is opt-in via ``fail_open_when_unset=False``.

    Imports FastAPI lazily so this module is importable without the ``fastapi``
    extra; only callers that actually invoke the function pay the dep.
    """
    import os

    expected = os.environ.get(env_var, "").strip()
    if not expected:
        if fail_open_when_unset:
            return
        from fastapi import HTTPException  # type: ignore[import-not-found]

        raise HTTPException(status_code=401, detail="API key not configured")
    if not compare_secrets(x_api_key, expected):
        _logger.debug(
            "API key validation failed",
            extra={"operation": "verify_api_key_header"},
        )
        from fastapi import HTTPException  # type: ignore[import-not-found]

        raise HTTPException(status_code=401, detail="Unauthorized")


__all__ = ["compare_secrets", "verify_api_key_header"]

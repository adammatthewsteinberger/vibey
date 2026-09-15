"""Optional httpx async HTTP client stack."""

from __future__ import annotations

from typing import Any

from vibey_bootstrap.http._common import DEFAULT_TIMEOUT, check_ssrf, inject_traceparent


def build_async_client(**kwargs: Any) -> Any:
    """Return an ``httpx.AsyncClient`` with sane defaults."""
    import httpx  # type: ignore[import-untyped]

    defaults = {"timeout": httpx.Timeout(DEFAULT_TIMEOUT)}
    defaults.update(kwargs)
    return httpx.AsyncClient(**defaults)  # type: ignore[arg-type]


async def async_request_with_retry(
    method: str,
    url: str,
    *,
    client: Any | None = None,
    headers: dict[str, str] | None = None,
    allow_private: bool = False,
    **kwargs: Any,
) -> Any:
    """Async HTTP request with traceparent and SSRF guard."""
    check_ssrf(url, allow_private=allow_private)
    hdrs = inject_traceparent(headers)
    owns_client = client is None
    c = client or build_async_client()
    try:
        return await c.request(method.upper(), url, headers=hdrs, **kwargs)
    finally:
        if owns_client:
            await c.aclose()


__all__ = ["async_request_with_retry", "build_async_client"]

"""Async HTTP client tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("httpx")

from vibey_bootstrap.http.async_client import async_request_with_retry, build_async_client


@pytest.mark.asyncio
async def test_async_request_with_retry() -> None:
    client = MagicMock()
    client.request = AsyncMock(return_value=MagicMock(status_code=200))
    with patch("vibey_bootstrap.http.async_client.check_ssrf"):
        resp = await async_request_with_retry("GET", "https://example.com", client=client)
    assert resp.status_code == 200


def test_build_async_client() -> None:
    client = build_async_client()
    assert client is not None

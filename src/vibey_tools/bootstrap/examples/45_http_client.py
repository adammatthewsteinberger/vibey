"""Example 45 — hardened HTTP client."""

from __future__ import annotations

from vibey_bootstrap.http import build_session, request_with_retry

session = build_session()
resp = request_with_retry("GET", "https://httpbin.org/get", session=session)
print(resp.status_code)

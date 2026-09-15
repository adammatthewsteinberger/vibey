"""Identity v3 extensions tests."""

from __future__ import annotations

import time

from vibey_bootstrap.identity import TokenCache


def test_token_cache_stores_and_returns() -> None:
    TokenCache.invalidate()
    TokenCache.cache_token("tenant-a", "scope", "tok", expires_at=time.time() + 3600)
    assert TokenCache.get_cached_token("tenant-a", "scope") == "tok"


def test_token_cache_invalidate_clears() -> None:
    TokenCache.cache_token("tenant-b", "scope", "tok", expires_at=time.time() + 3600)
    TokenCache.invalidate("tenant-b")
    assert TokenCache.get_cached_token("tenant-b", "scope") is None

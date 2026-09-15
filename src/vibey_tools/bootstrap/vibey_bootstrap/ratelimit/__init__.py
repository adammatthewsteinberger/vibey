"""In-process token-bucket rate limiter.

Belt-and-suspenders for L7 rate limiting at ingress (Istio EnvoyFilter is
fine; this defends against a sidecar-wedged or local-dev scenario where the
ingress filter isn't in the path).

The :func:`fastapi_rate_limit` helper builds a dependency callable that
returns 429 with an empty body on rejection — detail strings leak budget
state.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from vibey_bootstrap.counters import bump_counter


class TokenBucket:
    def __init__(
        self,
        *,
        budget: float,
        refill_per_second: float,
        name: str = "default",
        counter_namespace: str = "ratelimit",
    ) -> None:
        if budget < 0 or refill_per_second < 0:
            raise ValueError("budget and refill_per_second must be non-negative")
        self._budget = float(budget)
        self._refill = float(refill_per_second)
        self._tokens = float(budget)
        self._name = name
        self._namespace = counter_namespace
        self._last = time.monotonic()
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def budget(self) -> float:
        return self._budget

    def consume(self, n: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self._budget, self._tokens + elapsed * self._refill)
            self._last = now
            if self._tokens >= n:
                self._tokens -= n
                bump_counter(f"{self._namespace}.{self._name}.allowed")
                return True
            bump_counter(f"{self._namespace}.{self._name}.rejected")
            return False

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self._name,
                "tokens": round(self._tokens, 3),
                "budget": self._budget,
                "refill_per_second": self._refill,
                "last_refill_age_seconds": round(time.monotonic() - self._last, 3),
            }


def fastapi_rate_limit(
    bucket: TokenBucket,
    *,
    detail: str | None = None,
) -> Callable[..., Any]:
    """FastAPI dependency factory. 429 + empty body on rejection.

    ``detail`` is intentionally ignored by default — leak-resistant. Passing
    a string opts into showing it (not recommended for public endpoints).
    """

    async def _check() -> None:
        if bucket.consume(1.0):
            return
        from fastapi import HTTPException  # type: ignore[import-not-found]

        raise HTTPException(status_code=429, detail=detail)

    return _check


def webhook_bucket(*, name: str = "webhook") -> TokenBucket:
    """Preset for Microsoft-Graph-style webhooks: 240 burst, 4/s sustained."""
    return TokenBucket(budget=240.0, refill_per_second=4.0, name=name)


def admin_bucket(*, name: str = "admin") -> TokenBucket:
    """Preset for manual-trigger endpoints: 30 burst, 0.5/s sustained."""
    return TokenBucket(budget=30.0, refill_per_second=0.5, name=name)


class MultiUnitLimiter:
    """Multi-unit sliding window limiter (pages/records/seconds/chars/calls)."""

    def __init__(
        self,
        *,
        limits: dict[str, tuple[float, float]],
        fail_closed: bool | None = None,
        name: str = "multi",
    ) -> None:
        self._buckets = {
            unit: TokenBucket(budget=budget, refill_per_second=refill, name=f"{name}.{unit}")
            for unit, (budget, refill) in limits.items()
        }
        if fail_closed is None:
            import os

            fail_closed = os.environ.get("RATE_LIMIT_FAIL_CLOSED", "0") == "1"
        self._fail_closed = fail_closed

    def allow(self, unit: str, amount: float = 1.0) -> bool:
        bucket = self._buckets.get(unit)
        if bucket is None:
            return not self._fail_closed
        return bucket.consume(amount)


__all__ = [
    "MultiUnitLimiter",
    "TokenBucket",
    "admin_bucket",
    "fastapi_rate_limit",
    "webhook_bucket",
]

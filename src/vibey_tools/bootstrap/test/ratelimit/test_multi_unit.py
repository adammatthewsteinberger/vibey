"""Multi-unit rate limiter tests."""

from __future__ import annotations

from vibey_bootstrap.ratelimit import MultiUnitLimiter


def test_multi_unit_limiter_allows_within_budget() -> None:
    lim = MultiUnitLimiter(limits={"pages": (10.0, 1.0)}, fail_closed=False)
    assert lim.allow("pages", 1.0) is True

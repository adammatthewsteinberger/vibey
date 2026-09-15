"""Tests for ``vibey_bootstrap.ratelimit``."""

from __future__ import annotations

import threading
import time

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.ratelimit import TokenBucket, fastapi_rate_limit


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


def test_admits_within_budget() -> None:
    bucket = TokenBucket(budget=10, refill_per_second=0, name="t")
    for _ in range(10):
        assert bucket.consume() is True
    assert bucket.consume() is False
    assert counter_snapshot().get("ratelimit.t.rejected", 0) == 1
    assert counter_snapshot().get("ratelimit.t.allowed", 0) == 10


def test_refills_smoothly() -> None:
    bucket = TokenBucket(budget=10, refill_per_second=10, name="t")
    # drain
    for _ in range(10):
        bucket.consume()
    assert bucket.consume() is False
    time.sleep(0.55)  # should refill ~5 tokens
    admitted = sum(1 for _ in range(10) if bucket.consume())
    assert 3 <= admitted <= 7  # tolerant range


def test_thread_safe() -> None:
    bucket = TokenBucket(budget=50, refill_per_second=0, name="t")
    results: list[bool] = []
    results_lock = threading.Lock()

    def worker() -> None:
        ok = bucket.consume()
        with results_lock:
            results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(results) == 50
    assert sum(1 for r in results if not r) == 50


def test_snapshot_returns_state() -> None:
    bucket = TokenBucket(budget=10, refill_per_second=1, name="snap")
    snap = bucket.snapshot()
    assert snap["name"] == "snap"
    assert snap["budget"] == 10
    assert snap["refill_per_second"] == 1


def test_fastapi_rate_limit_returns_429() -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    bucket = TokenBucket(budget=2, refill_per_second=0, name="rl_app")
    dep = fastapi_rate_limit(bucket)
    app = FastAPI()

    from fastapi import Depends

    @app.get("/ping", dependencies=[Depends(dep)])
    def ping() -> dict:
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    r = client.get("/ping")
    assert r.status_code == 429
    # Default detail is None; FastAPI renders as {"detail": null} — that's fine.

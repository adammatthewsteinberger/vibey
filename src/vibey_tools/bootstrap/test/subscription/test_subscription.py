"""Tests for ``vibey_bootstrap.subscription``."""

from __future__ import annotations

import threading
import time

import pytest

from vibey_bootstrap.alerts import (
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.subscription import (
    RenewableResource,
    SubscriptionGone,
    ensure_resource,
    renewal_loop,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])


def test_ensure_resource_returns_existing() -> None:
    existing = RenewableResource(id="A", handle="h")

    def list_fn() -> list[RenewableResource[str]]:
        return [existing]

    def create_fn() -> RenewableResource[str]:
        raise AssertionError("create_fn must not be called when one exists")

    out = ensure_resource(operation="t.ensure", list_fn=list_fn, create_fn=create_fn)
    assert out is existing


def test_ensure_resource_creates_when_none() -> None:
    created: list[str] = []

    def list_fn() -> list[RenewableResource[str]]:
        return []

    def create_fn() -> RenewableResource[str]:
        created.append("x")
        return RenewableResource(id="B", handle="h")

    out = ensure_resource(operation="t.ensure", list_fn=list_fn, create_fn=create_fn)
    assert out.id == "B"
    assert created == ["x"]


def test_renewal_loop_recreates_on_gone() -> None:
    state = {"renew_calls": 0}
    resource = RenewableResource(id="orig", handle="h")
    recreated: list[RenewableResource[str]] = []

    def renew_fn(rid: str) -> RenewableResource[str]:
        state["renew_calls"] += 1
        if state["renew_calls"] == 1:
            raise SubscriptionGone("upstream reaped")
        # Second iteration: succeed quickly, then signal stop
        return resource

    def recreate_fn() -> RenewableResource[str]:
        new = RenewableResource(id="fresh", handle="h")
        recreated.append(new)
        return new

    stop = threading.Event()

    def runner() -> None:
        renewal_loop(
            resource,
            stop_event=stop,
            renew_fn=renew_fn,
            recreate_fn=recreate_fn,
            interval_seconds=0.05,
            operation="t.renew",
        )

    t = threading.Thread(target=runner)
    t.start()
    time.sleep(0.25)
    stop.set()
    t.join(timeout=2.0)
    assert recreated, "expected recreate after SubscriptionGone"
    assert counter_snapshot().get("subscription.recreated", 0) >= 1


def test_renewal_loop_exits_critical_alert_on_non_gone() -> None:
    """Non-SubscriptionGone exception fires CRITICAL email + exits the loop."""
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    reset_alerts()
    register_dispatcher(sender, recipients=["ops@example.com"])

    resource = RenewableResource(id="orig", handle="h")

    def renew_fn(rid: str) -> RenewableResource[str]:
        raise ValueError("unexpected")

    stop = threading.Event()
    runner = threading.Thread(
        target=renewal_loop,
        args=(resource,),
        kwargs=dict(
            stop_event=stop,
            renew_fn=renew_fn,
            recreate_fn=None,
            interval_seconds=0.05,
            operation="t.renew_crash",
        ),
    )
    runner.start()
    runner.join(timeout=2.0)
    assert not runner.is_alive()
    matched = [r for r in received if "t.renew_crash" in r[1] or "renewal raised" in r[1]]
    assert matched, f"expected CRITICAL email; got subjects: {[r[1] for r in received]}"


def test_renewal_loop_respects_stop_event_promptly() -> None:
    resource = RenewableResource(id="orig", handle="h")

    def renew_fn(rid: str) -> RenewableResource[str]:
        return resource

    stop = threading.Event()
    started = time.monotonic()
    runner = threading.Thread(
        target=renewal_loop,
        args=(resource,),
        kwargs=dict(
            stop_event=stop,
            renew_fn=renew_fn,
            recreate_fn=None,
            interval_seconds=60.0,  # long interval — must not block stop
            operation="t.renew_stop",
        ),
    )
    runner.start()
    time.sleep(0.05)
    stop.set()
    runner.join(timeout=6.0)
    elapsed = time.monotonic() - started
    assert not runner.is_alive()
    assert elapsed < 6.0  # well under the 60s nominal interval

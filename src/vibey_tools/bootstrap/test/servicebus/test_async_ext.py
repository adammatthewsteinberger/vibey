"""Service Bus async extension tests."""

from __future__ import annotations

from vibey_bootstrap.servicebus import ReplayGuard, service_bus_transport_type


def test_replay_guard_dedupes() -> None:
    guard = ReplayGuard(max_size=100, ttl_seconds=60.0)
    assert guard.seen("msg-1") is False
    assert guard.seen("msg-1") is True


def test_service_bus_transport_type_default() -> None:
    assert service_bus_transport_type() in ("amqp", "websocket")

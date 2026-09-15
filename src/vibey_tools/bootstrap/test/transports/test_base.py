"""Tests for _BufferedShipper base class."""

from __future__ import annotations

import logging

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper


class _StubShipper(_BufferedShipper):
    def __init__(self, **kw) -> None:
        super().__init__(counter_prefix="stub", **kw)
        self.shipped: list[list[str]] = []

    def _ship(self, batch: list[str]) -> ShipResult:
        self.shipped.append(list(batch))
        return ShipResult(ok=True, count=len(batch))


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def test_emit_buffers_until_flush() -> None:
    h = _StubShipper(flush_interval=3600.0, batch_size=100)
    try:
        h.emit(_record())
        assert h.shipped == []
        h.flush()
        assert len(h.shipped) == 1
        assert h.shipped[0] == ["hi"]
    finally:
        h.close()


def test_batch_size_triggers_flush_event() -> None:
    h = _StubShipper(batch_size=2, flush_interval=3600.0)
    try:
        h._flush_now.clear()
        h.emit(_record("a"))
        assert not h._flush_now.is_set()
        h.emit(_record("b"))
        assert h._flush_now.is_set()
    finally:
        h.close()


def test_overflow_counts_dropped() -> None:
    h = _StubShipper(max_buffer=2, flush_interval=3600.0, batch_size=100)
    try:
        for i in range(5):
            h.emit(_record(str(i)))
    finally:
        h.close()
    assert counter_snapshot().get("stub.transport.dropped", 0) >= 1


def test_ship_failure_bumps_error() -> None:
    class _FailShipper(_BufferedShipper):
        def _ship(self, batch: list[str]) -> ShipResult:
            return ShipResult(ok=False, count=0)

    before = counter_snapshot().get("stubfail.transport.error", 0)
    h = _FailShipper(counter_prefix="stubfail", flush_interval=3600.0)
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    assert counter_snapshot().get("stubfail.transport.error", 0) == before + 1

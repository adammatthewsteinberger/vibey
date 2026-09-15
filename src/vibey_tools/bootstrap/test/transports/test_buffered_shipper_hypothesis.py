"""Property-based tests for _BufferedShipper batch splitting and overflow."""

from __future__ import annotations

import logging
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.transports._base import ShipResult, _BufferedShipper

pytestmark = pytest.mark.usefixtures("allow_counter_reset")


@pytest.fixture(autouse=True)
def allow_counter_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_BOOTSTRAP_ALLOW_RESET", "1")


@pytest.fixture(autouse=True)
def isolated_counters() -> None:
    _reset_counters()
    yield
    _reset_counters()


class _RecordingShipper(_BufferedShipper):
    """Minimal shipper that records batches and never touches the network."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(counter_prefix="hypo", flush_interval=3600.0, **kwargs)
        self.shipped: list[list[str]] = []
        self.setFormatter(logging.Formatter("%(message)s"))

    def _ship(self, batch: list[str]) -> ShipResult:
        self.shipped.append(list(batch))
        return ShipResult(ok=True, count=len(batch))


def _record(msg: str) -> logging.LogRecord:
    return logging.LogRecord("hypo", logging.INFO, __file__, 1, msg, None, None)


@settings(max_examples=80, deadline=None)
@given(
    batch_size=st.integers(min_value=1, max_value=50),
    lines=st.lists(st.text(min_size=0, max_size=40), min_size=0, max_size=120),
)
def test_take_batch_respects_count(batch_size: int, lines: list[str]) -> None:
    h = _RecordingShipper(batch_size=batch_size)
    try:
        with h._lock:
            h._buffer.extend(lines)

        taken: list[list[str]] = []
        while True:
            batch = h._take_batch()
            if not batch:
                break
            taken.append(batch)
            assert len(batch) <= batch_size

        flat = [line for batch in taken for line in batch]
        assert flat == lines
    finally:
        h.close()


@settings(max_examples=60, deadline=None)
@given(
    max_batch_bytes=st.integers(min_value=8, max_value=512),
    lines=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=80,
        ),
        min_size=1,
        max_size=80,
    ),
)
def test_take_batch_respects_byte_budget(max_batch_bytes: int, lines: list[str]) -> None:
    h = _RecordingShipper(batch_size=10_000, max_batch_bytes=max_batch_bytes)
    try:
        with h._lock:
            h._buffer.extend(lines)

        taken: list[list[str]] = []
        while True:
            batch = h._take_batch()
            if not batch:
                break
            taken.append(batch)
            if len(batch) > 1:
                nbytes = sum(len(line.encode("utf-8")) + 1 for line in batch)
                assert nbytes <= max_batch_bytes

        flat = [line for batch in taken for line in batch]
        assert flat == lines
    finally:
        h.close()


@settings(max_examples=50, deadline=None)
@given(
    max_buffer=st.integers(min_value=1, max_value=20),
    extra_emits=st.integers(min_value=0, max_value=30),
)
def test_overflow_increments_dropped_counter(max_buffer: int, extra_emits: int) -> None:
    _reset_counters()
    total = max_buffer + extra_emits
    h = _RecordingShipper(max_buffer=max_buffer, batch_size=10_000)
    try:
        for i in range(total):
            h.emit(_record(str(i)))
        dropped = counter_snapshot().get("hypo.transport.dropped", 0)
        assert dropped == extra_emits
        assert len(h._buffer) == max_buffer
    finally:
        h.close()


@settings(max_examples=40, deadline=None)
@given(
    lines=st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=30,
        ),
        min_size=1,
        max_size=60,
    ),
    batch_size=st.integers(min_value=1, max_value=15),
)
def test_flush_preserves_emit_order(lines: list[str], batch_size: int) -> None:
    h = _RecordingShipper(batch_size=batch_size)
    try:
        for line in lines:
            h.emit(_record(line))
        h.flush()
        shipped = [line for batch in h.shipped for line in batch]
        assert shipped == lines
    finally:
        h.close()

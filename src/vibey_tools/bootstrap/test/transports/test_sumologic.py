"""SumoLogicHandler: buffering, batch POST shape, status handling, counters, close.

The handler ships via a ``requests.Session`` whose mounted ``urllib3`` Retry
adapter owns the 408/429/5xx backoff + ``Retry-After`` logic. These tests
monkeypatch ``handler._session.post`` directly, so they assert the handler's own
behavior (batching, headers, gzip, status-driven counters) independent of the
adapter's internal retries.
"""

from __future__ import annotations

import gzip
import json
import logging
from collections.abc import Iterator

import pytest

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.transports.sumologic import SumoLogicHandler, make_sumo_logic_handler


class _FakeResp:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.text = ""


class _PostRecorder:
    """Stand-in for ``requests.Session.post`` that records calls."""

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls: list[dict] = []

    def __call__(self, url, data=None, headers=None, timeout=None):  # noqa: ANN001
        self.calls.append({"url": url, "data": data, "headers": headers or {}, "timeout": timeout})
        return _FakeResp(self.status_code)


def _record(msg: str = "hi", **extra: object) -> logging.LogRecord:
    rec = logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


def _handler(*, status_code: int = 200, **kw) -> tuple[SumoLogicHandler, _PostRecorder]:
    """Build a handler with its session.post replaced by a recorder.

    Returns ``(handler, recorder)``. The background thread is kept effectively
    idle (long flush_interval, high batch_size) so tests drive flushing
    explicitly via ``flush()`` / ``close()``.
    """
    kw.setdefault("endpoint_url", "https://example.test/receiver")
    kw.setdefault("flush_interval", 3600.0)
    kw.setdefault("batch_size", 1000)
    h = SumoLogicHandler(**kw)
    recorder = _PostRecorder(status_code=status_code)
    h._session.post = recorder  # type: ignore[method-assign]
    return h, recorder


@pytest.fixture(autouse=True)
def _isolate_root() -> Iterator[None]:
    # Handlers are never attached to root in these tests, but guard anyway.
    yield


def test_emit_buffers_without_immediate_post() -> None:
    h, rec = _handler()
    try:
        h.emit(_record())
        assert rec.calls == []  # nothing posted until flush/size/interval
    finally:
        h.close()


def test_flush_posts_newline_delimited_json_with_headers() -> None:
    h, rec = _handler(source_category="prod/app", source_host="host-1")
    try:
        h.emit(_record("one", user_id="u1"))
        h.emit(_record("two"))
        h.flush()
    finally:
        h.close()
    assert len(rec.calls) == 1
    call = rec.calls[0]
    assert call["headers"]["X-Sumo-Category"] == "prod/app"
    assert call["headers"]["X-Sumo-Host"] == "host-1"
    assert call["headers"]["X-Sumo-Name"] == "vibey-bootstrap"
    lines = call["data"].decode().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["message"] == "one"
    assert json.loads(lines[0])["user_id"] == "u1"
    assert json.loads(lines[1])["message"] == "two"


def test_size_trigger_sets_flush_event() -> None:
    h, _rec = _handler(batch_size=2, flush_interval=3600.0)
    try:
        h._flush_now.clear()
        h.emit(_record())
        assert h._flush_now.is_set() is False
        h.emit(_record())
        assert h._flush_now.is_set() is True  # crossed batch_size
    finally:
        h.close()


def test_success_counters() -> None:
    h, _rec = _handler()
    try:
        h.emit(_record())
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    snap = counter_snapshot()
    assert snap.get("sumologic.transport.ok", 0) >= 1
    assert snap.get("sumologic.transport.records", 0) == 2


def test_429_bumps_throttled_and_error_and_drops() -> None:
    h, rec = _handler(status_code=429)
    before = counter_snapshot().get("sumologic.transport.throttled", 0)
    try:
        h.emit(_record())
        h.flush()  # must not raise
    finally:
        h.close()
    snap = counter_snapshot()
    assert snap.get("sumologic.transport.throttled", 0) == before + 1
    assert snap.get("sumologic.transport.error", 0) >= 1
    assert len(rec.calls) >= 1  # posted (and dropped) — not retried in-handler


def test_401_bumps_error_but_not_throttled() -> None:
    before_thr = counter_snapshot().get("sumologic.transport.throttled", 0)
    before_err = counter_snapshot().get("sumologic.transport.error", 0)
    h, _rec = _handler(status_code=401)
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    snap = counter_snapshot()
    assert snap.get("sumologic.transport.error", 0) == before_err + 1
    assert snap.get("sumologic.transport.throttled", 0) == before_thr  # unchanged


def test_never_raises_on_network_exception_and_bumps_error() -> None:
    h, _rec = _handler()

    def boom(url, data=None, headers=None, timeout=None):  # noqa: ANN001
        raise ConnectionError("down")

    h._session.post = boom  # type: ignore[method-assign]
    before = counter_snapshot().get("sumologic.transport.error", 0)
    try:
        h.emit(_record())
        h.flush()  # must not raise
    finally:
        h.close()
    assert counter_snapshot().get("sumologic.transport.error", 0) == before + 1


def test_gzip_above_threshold() -> None:
    h, rec = _handler(gzip_threshold=10)
    try:
        h.emit(_record("a fairly long message that exceeds ten bytes easily"))
        h.flush()
    finally:
        h.close()
    call = rec.calls[0]
    assert call["headers"].get("Content-Encoding") == "gzip"
    # Body is real gzip and decompresses back to NDJSON.
    decoded = gzip.decompress(call["data"]).decode()
    assert json.loads(decoded.split("\n")[0])["message"].startswith("a fairly long")


def test_no_gzip_below_threshold() -> None:
    h, rec = _handler(gzip_threshold=10_000)
    try:
        h.emit(_record("tiny"))
        h.flush()
    finally:
        h.close()
    call = rec.calls[0]
    assert "Content-Encoding" not in call["headers"]
    assert json.loads(call["data"].decode())["message"] == "tiny"


def test_source_token_sets_auth_header() -> None:
    h, rec = _handler(source_token="abc123")
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    assert rec.calls[0]["headers"]["x-sumo-token"] == "abc123"


def test_fields_set_x_sumo_fields_header() -> None:
    h, rec = _handler(fields={"a": "1", "b": "2"})
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    assert rec.calls[0]["headers"]["X-Sumo-Fields"] == "a=1,b=2"


def test_byte_cap_splits_into_multiple_posts() -> None:
    # Each formatted record is well over 200 bytes; a 600-byte cap forces splits.
    h, rec = _handler(batch_size=1000, max_batch_bytes=600, gzip_threshold=10_000)
    try:
        big = "x" * 300
        for _ in range(5):
            h.emit(_record(big))
        h.flush()
    finally:
        h.close()
    assert len(rec.calls) >= 3  # 5 large records cannot fit in one 600B POST


def test_overflow_drops_and_counts() -> None:
    h, _rec = _handler(max_buffer=2)
    try:
        for _ in range(5):
            h.emit(_record())
    finally:
        h.close()
    assert counter_snapshot().get("sumologic.transport.dropped", 0) >= 1


def test_close_is_idempotent() -> None:
    h, _rec = _handler()
    h.emit(_record())
    h.close()
    h.close()  # second close must be a no-op, not raise


def test_close_does_final_flush() -> None:
    h, rec = _handler()
    h.emit(_record())
    h.close()  # buffered record flushed on close
    assert len(rec.calls) == 1


def test_make_factory_returns_none_without_url() -> None:
    assert make_sumo_logic_handler() is None


def test_make_factory_builds_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SUMO_LOGIC_COLLECTOR_URL", "https://example.test/r")
    monkeypatch.setenv("SUMO_LOGIC_SOURCE_CATEGORY", "cat")
    monkeypatch.setenv("SUMO_LOGIC_BATCH_SIZE", "7")
    monkeypatch.setenv("SUMO_LOGIC_COLLECTOR_TOKEN", "tok")
    monkeypatch.setenv("SUMO_LOGIC_FIELDS", "env=prod,team=core")
    h = make_sumo_logic_handler()
    assert isinstance(h, SumoLogicHandler)
    try:
        assert h.source_category == "cat"
        assert h.batch_size == 7
        assert h.source_token == "tok"
        assert h.fields == {"env": "prod", "team": "core"}
    finally:
        h.close()


def test_make_factory_returns_none_when_requests_missing(monkeypatch) -> None:
    monkeypatch.setenv("SUMO_LOGIC_COLLECTOR_URL", "https://example.test/r")

    def _no_requests() -> object:
        raise ImportError("No module named 'requests'")

    monkeypatch.setattr("vibey_bootstrap.transports.sumologic._build_session", _no_requests)
    assert make_sumo_logic_handler() is None

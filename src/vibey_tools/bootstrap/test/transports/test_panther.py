"""PantherHandler tests."""

from __future__ import annotations

import json
import logging

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.transports.panther import PantherHandler, make_panther_handler


class _FakeResp:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code


class _PostRecorder:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls: list[dict] = []

    def __call__(self, url, data=None, headers=None, timeout=None):  # noqa: ANN001
        self.calls.append({"url": url, "data": data, "headers": headers or {}})
        return _FakeResp(self.status_code)


def _record(msg: str = "hi") -> logging.LogRecord:
    return logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)


def _handler(**kw) -> tuple[PantherHandler, _PostRecorder]:
    kw.setdefault("api_host", "https://panther.test")
    kw.setdefault("log_source_id", "src-1")
    kw.setdefault("log_source_token", "tok")
    kw.setdefault("flush_interval", 3600.0)
    kw.setdefault("batch_size", 1000)
    h = PantherHandler(**kw)
    rec = _PostRecorder()
    h._session.post = rec  # type: ignore[method-assign]
    return h, rec


def test_flush_posts_events_json() -> None:
    h, rec = _handler()
    try:
        h.emit(_record("one"))
        h.flush()
    finally:
        h.close()
    assert len(rec.calls) == 1
    body = json.loads(rec.calls[0]["data"].decode())
    assert "events" in body
    assert body["events"][0]["message"] == "one"


def test_429_bumps_throttled() -> None:
    before = counter_snapshot().get("panther.transport.throttled", 0)
    h, _rec = _handler()
    h._session.post = _PostRecorder(status_code=429)  # type: ignore[method-assign]
    try:
        h.emit(_record())
        h.flush()
    finally:
        h.close()
    assert counter_snapshot().get("panther.transport.throttled", 0) == before + 1


def test_make_factory_returns_none_without_config() -> None:
    assert make_panther_handler() is None

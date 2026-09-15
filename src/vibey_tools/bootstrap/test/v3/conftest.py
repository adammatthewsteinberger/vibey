"""Shared fixtures and helpers for v3.0.0 test suites."""

from __future__ import annotations

import gzip
import json
import logging
from collections.abc import Callable
from typing import Any

import pytest


class FakeResp:
    """Minimal HTTP response stand-in."""

    def __init__(self, status_code: int = 200, body: dict | None = None) -> None:
        self.status_code = status_code
        self.text = ""
        self._body = body or {}

    def json(self) -> dict:
        return self._body


class PostRecorder:
    """Records ``requests.Session.post`` calls."""

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls: list[dict[str, Any]] = []
        self.raise_exc: Exception | None = None

    def __call__(self, url, data=None, headers=None, timeout=None):  # noqa: ANN001
        if self.raise_exc:
            raise self.raise_exc
        self.calls.append(
            {"url": url, "data": data, "headers": dict(headers or {}), "timeout": timeout}
        )
        return FakeResp(self.status_code)


def log_record(msg: str = "hi", **extra: object) -> logging.LogRecord:
    rec = logging.LogRecord("svc.test", logging.INFO, __file__, 1, msg, None, None)
    for key, value in extra.items():
        setattr(rec, key, value)
    return rec


def patch_session_post(handler: Any, recorder: PostRecorder) -> None:
    """Attach a post recorder to HTTP-based handlers."""
    handler._session.post = recorder  # type: ignore[method-assign]


@pytest.fixture
def isolated_counters():
    from vibey_bootstrap.counters import _reset_counters

    _reset_counters()
    yield
    _reset_counters()


def ndjson_lines(data: bytes) -> list[dict]:
    text = data.decode() if isinstance(data, bytes) else data
    if isinstance(text, bytes):
        text = gzip.decompress(text).decode()
    return [json.loads(line) for line in text.strip().split("\n") if line]


HandlerFactory = Callable[..., logging.Handler]

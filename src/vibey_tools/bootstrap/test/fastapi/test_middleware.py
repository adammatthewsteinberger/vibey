"""Tests for ``vibey_bootstrap.fastapi_middleware``."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.fastapi_middleware import install_middleware


@pytest.fixture
def sender_calls() -> list[tuple[list[str], str, str]]:
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    reset_state()
    register_dispatcher(sender, recipients=["ops@example.com"])
    yield received
    reset_state()


def _make_app() -> FastAPI:
    app = FastAPI()
    install_middleware(app)

    @app.get("/health/live")
    def live() -> dict:
        return {"status": "ok"}

    @app.get("/api/work")
    def work() -> dict:
        return {"ok": True}

    @app.get("/api/boom")
    def boom() -> dict:
        raise HTTPException(status_code=500, detail="oh no")

    @app.get("/api/crash")
    def crash() -> dict:
        raise RuntimeError("explosion")

    return app


def test_middleware_skips_probes(
    sender_calls: list[tuple[list[str], str, str]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = _make_app()
    client = TestClient(app)
    with caplog.at_level("DEBUG", logger="vibey_bootstrap.fastapi_middleware"):
        r = client.get("/health/live")
    assert r.status_code == 200
    assert not any("→ HTTP" in record.message for record in caplog.records)


def test_middleware_fires_alert_on_5xx(
    sender_calls: list[tuple[list[str], str, str]],
) -> None:
    app = _make_app()
    client = TestClient(app)
    r = client.get("/api/boom")
    assert r.status_code == 500
    pending = drain_pending_alerts()
    matched = [p for p in pending if "http_5xx" in p.dedup_key]
    assert matched


def test_middleware_fires_alert_on_uncaught(
    sender_calls: list[tuple[list[str], str, str]],
) -> None:
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    client.get("/api/crash")
    pending = drain_pending_alerts()
    matched = [p for p in pending if "http_crash" in p.dedup_key]
    assert matched

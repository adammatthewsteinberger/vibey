"""Tests for ``vibey_bootstrap.auth``."""

from __future__ import annotations

import time
from typing import Any

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vibey_bootstrap.auth import (
    WebhookDedup,
    install_graph_webhook_route,
    validation_token_handshake,
    verify_webhook_client_state,
)
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.failclose import ConfigurationError
from vibey_bootstrap.ratelimit import TokenBucket


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_counters()
    monkeypatch.delenv("GRAPH_WEBHOOK_CLIENT_STATE", raising=False)


class TestWebhookDedup:
    def test_suppresses_duplicate(self) -> None:
        d = WebhookDedup()
        assert d.already_seen(("sub", "msg1")) is False
        assert d.already_seen(("sub", "msg1")) is True

    def test_ttl_expires(self) -> None:
        d = WebhookDedup(ttl_seconds=0.1)
        d.already_seen(("sub", "msg1"))
        time.sleep(0.15)
        # After TTL, the key should be GC'd and re-insertion succeeds
        assert d.already_seen(("sub", "msg1")) is False

    def test_max_entries_cap(self) -> None:
        d = WebhookDedup(max_entries=10)
        for i in range(20):
            d.already_seen(("sub", f"m{i}"))
        # Inspecting through the public interface: keys present should be ≤ 10
        with d._lock:  # type: ignore[attr-defined]
            assert len(d._seen) <= 10  # type: ignore[attr-defined]


class TestClientState:
    def test_constant_time_match(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        assert verify_webhook_client_state("secret") is True

    def test_mismatch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        assert verify_webhook_client_state("wrong") is False
        assert verify_webhook_client_state(None) is False

    def test_unconfigured_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GRAPH_WEBHOOK_CLIENT_STATE", raising=False)
        with pytest.raises(ConfigurationError):
            verify_webhook_client_state("anything")


class TestValidationTokenHandshake:
    def test_echo(self) -> None:
        assert validation_token_handshake("abc123") == "abc123"

    def test_none(self) -> None:
        assert validation_token_handshake(None) is None
        assert validation_token_handshake("") is None


class TestInstallRoute:
    def _build_app(
        self,
        *,
        bucket: Any = None,
        dedup: Any = None,
    ) -> tuple[FastAPI, list[str]]:
        handler_calls: list[str] = []

        def handler(message_id: str) -> None:
            handler_calls.append(message_id)

        app = FastAPI()
        install_graph_webhook_route(
            app,
            "/webhook",
            background_handler=handler,
            rate_limit_bucket=bucket,
            dedup=dedup,
        )
        return app, handler_calls

    def test_validation_token_echo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        app, _ = self._build_app()
        client = TestClient(app)
        r = client.post("/webhook?validationToken=xyz")
        assert r.status_code == 200
        assert r.text == "xyz"

    def test_rejects_bad_client_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        app, _ = self._build_app()
        client = TestClient(app)
        r = client.post(
            "/webhook",
            json={"value": [{"clientState": "WRONG", "resourceData": {"id": "m1"}}]},
        )
        assert r.status_code == 401
        assert r.content == b""
        assert counter_snapshot().get("webhook.client_state_mismatch", 0) == 1

    def test_dispatches_when_client_state_matches(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        app, calls = self._build_app()
        client = TestClient(app)
        r = client.post(
            "/webhook",
            json={
                "value": [
                    {
                        "clientState": "secret",
                        "subscriptionId": "s1",
                        "resourceData": {"id": "m1"},
                    }
                ]
            },
        )
        assert r.status_code == 202
        # Background task runs synchronously in TestClient
        assert calls == ["m1"]
        assert counter_snapshot().get("webhook.received", 0) == 1

    def test_rate_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        bucket = TokenBucket(budget=2, refill_per_second=0, name="t")
        app, _ = self._build_app(bucket=bucket)
        client = TestClient(app)
        body = {"value": [{"clientState": "secret", "resourceData": {"id": "m"}}]}
        assert client.post("/webhook", json=body).status_code == 202
        assert client.post("/webhook", json=body).status_code == 202
        r = client.post("/webhook", json=body)
        assert r.status_code == 429
        assert r.content == b""
        assert counter_snapshot().get("webhook.rate_limited", 0) == 1

    def test_dedup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPH_WEBHOOK_CLIENT_STATE", "secret")
        d = WebhookDedup()
        app, calls = self._build_app(dedup=d)
        client = TestClient(app)
        body = {
            "value": [
                {
                    "clientState": "secret",
                    "subscriptionId": "s1",
                    "resourceData": {"id": "same-id"},
                }
            ]
        }
        client.post("/webhook", json=body)
        client.post("/webhook", json=body)
        assert calls == ["same-id"]
        assert counter_snapshot().get("webhook.dedup_skipped", 0) == 1

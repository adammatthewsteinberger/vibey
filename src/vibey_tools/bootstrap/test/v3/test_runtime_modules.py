"""Exhaustive runtime module tests for v3."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("sqlalchemy")

from vibey_bootstrap.aks import build_info, setup_async_sigterm_handler
from vibey_bootstrap.aks.leader_election import LeaderElection
from vibey_bootstrap.audit import AuditChain, verify_chain
from vibey_bootstrap.auth.hmac import verify_hmac_signature
from vibey_bootstrap.db import _reset_db, get_db, get_engine
from vibey_bootstrap.db.outbox import Outbox, drain_outbox
from vibey_bootstrap.governance import BudgetGuard
from vibey_bootstrap.http import normalize_pem, request_with_retry, write_temp_pem
from vibey_bootstrap.http._common import inject_traceparent
from vibey_bootstrap.identity import (
    TokenCache,
    _reset_token_cache,
    build_tenant_credential,
    build_tenant_credential_cached,
)
from vibey_bootstrap.ratelimit import MultiUnitLimiter as RLMU
from vibey_bootstrap.servicebus.async_ext import (
    MultiQueueRouter,
    ReplayGuard,
    service_bus_transport_type,
)

# --- identity ---


def test_build_tenant_credential_requires_client_id(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    with pytest.raises(ValueError):
        build_tenant_credential("tenant-1")


def test_build_tenant_credential_success(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_CLIENT_ID", "app-id")
    with patch("azure.identity.WorkloadIdentityCredential") as wi:
        wi.return_value = MagicMock()
        cred = build_tenant_credential("tenant-1")
        assert cred is wi.return_value


def test_build_tenant_credential_cached_hit(monkeypatch) -> None:
    TokenCache.invalidate()
    TokenCache.cache_token("t1", "scope", "cached-tok", expires_at=time.time() + 3600)
    result = build_tenant_credential_cached("t1", "scope", app_client_id="app")
    assert result == "cached-tok"


def test_build_tenant_credential_cached_miss(monkeypatch) -> None:
    TokenCache.invalidate()
    monkeypatch.setenv("AZURE_CLIENT_ID", "app-id")
    mock_cred = MagicMock()
    mock_cred.get_token.return_value = MagicMock(token="fresh", expires_on=time.time() + 3600)
    with patch("vibey_bootstrap.identity.build_tenant_credential", return_value=mock_cred):
        result = build_tenant_credential_cached("t2", "scope")
    assert result == "fresh"


def test_token_cache_eviction(monkeypatch) -> None:
    TokenCache.invalidate()
    monkeypatch.setenv("TOKEN_CACHE_MAX_SIZE", "2")
    now = time.time() + 3600
    TokenCache.cache_token("a", "s", "1", now)
    TokenCache.cache_token("b", "s", "2", now)
    TokenCache.cache_token("c", "s", "3", now)
    assert TokenCache.get_cached_token("a", "s") is None


def test_reset_token_cache() -> None:
    TokenCache.cache_token("x", "s", "t", time.time() + 60)
    _reset_token_cache()
    assert TokenCache.get_cached_token("x", "s") is None


# --- db ---


def test_get_db_closes_session(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reset_db()
    gen = get_db()
    session = next(gen)
    assert session is not None
    gen.close()
    _reset_db()


def test_get_engine_singleton(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reset_db()
    e1 = get_engine()
    e2 = get_engine()
    assert e1 is e2
    _reset_db()


# --- outbox ---


def test_outbox_claim_and_mark_sent() -> None:
    session = MagicMock()
    session.execute.return_value.rowcount = 1
    outbox = Outbox(session)
    outbox.enqueue(idempotency_key="k", payload={"a": 1})
    assert outbox.claim("fake-id") is True
    outbox.mark_sent("fake-id")


def test_outbox_mark_failed_caps_attempts() -> None:
    session = MagicMock()
    outbox = Outbox(session)
    outbox.mark_failed("id", "err", max_attempts=3)
    session.execute.assert_called()


def test_drain_outbox_claim_miss() -> None:
    session = MagicMock()
    session.execute.return_value.fetchall.return_value = [("id-1", '{"x": 1}')]
    session.execute.return_value.rowcount = 0

    count = drain_outbox(session, lambda p: None)
    assert count == 0


# --- auth / audit / governance ---


def test_hmac_sha256_prefix_variants() -> None:
    import hashlib
    import hmac

    body = b"payload"
    secret = "sec"
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(secret, body, f"sha256={digest}")
    assert verify_hmac_signature(secret, body, digest)


def test_hmac_rejects_empty() -> None:
    assert verify_hmac_signature("", b"x", "sha256=abc") is False


def test_verify_chain_single_record() -> None:
    stored: list = []

    chain = AuditChain(storage_fn=stored.append)
    r = chain.append_chained("LOGIN", actor="a", resource="/")
    assert verify_chain([r]) is True


def test_budget_guard_commit_and_check() -> None:
    guard = BudgetGuard()
    guard.set_budget("p", "month", 100.0)
    guard.commit("p", "month", 40.0)
    check = guard.check("p", "month", 50.0)
    assert check.allowed is True
    check2 = guard.check("p", "month", 70.0)
    assert check2.allowed is False


def test_multi_unit_fail_closed() -> None:
    lim = RLMU(limits={"pages": (1.0, 0.1)}, fail_closed=True)
    assert lim.allow("pages") is True
    assert lim.allow("pages") is False
    assert lim.allow("unknown_unit") is False


# --- http ---


def test_normalize_pem_crlf_and_spaces() -> None:
    pem = "-----BEGIN CERT----- line -----END CERT-----"
    out = normalize_pem(pem)
    assert "BEGIN CERT" in out


def test_write_temp_pem_creates_file() -> None:
    path = write_temp_pem("-----BEGIN\\nX\\n-----END")
    assert Path(path).exists()
    Path(path).unlink()


def test_request_with_retry_ssrf_blocked() -> None:
    with pytest.raises(ValueError):
        request_with_retry("GET", "http://169.254.169.254/")


def test_inject_traceparent_with_correlation(monkeypatch) -> None:
    from vibey_bootstrap.logging.correlation import set_correlation_id

    set_correlation_id("abc-def-ghi")
    hdrs = inject_traceparent({})
    assert "traceparent" in hdrs


# --- aks / servicebus ---


def test_build_info_all_keys(monkeypatch) -> None:
    monkeypatch.setenv("BUILD_VERSION", "3.0.0")
    monkeypatch.setenv("GIT_SHA", "abc")
    info = build_info()
    assert info["version"] == "3.0.0"
    assert info["git_sha"] == "abc"


def test_async_sigterm_handler() -> None:
    async def _run() -> None:
        stop = setup_async_sigterm_handler()
        assert isinstance(stop, asyncio.Event)

    asyncio.run(_run())


def test_leader_election_with_holder(monkeypatch) -> None:
    monkeypatch.setenv("LEADER_ELECTION_CONFIGMAP", "lock")
    monkeypatch.setenv("LEADER_HOLDER", "other-pod")
    le = LeaderElection()
    le.start()
    assert le.is_leader is False
    le.stop()


def test_replay_guard_ttl_eviction() -> None:
    guard = ReplayGuard(max_size=10, ttl_seconds=0.001)
    assert guard.seen("k") is False
    time.sleep(0.002)
    assert guard.seen("k") is False


def test_service_bus_transport_type_ws(monkeypatch) -> None:
    monkeypatch.setenv("SERVICE_BUS_TRANSPORT_TYPE", "websocket")
    assert service_bus_transport_type() == "websocket"


def test_multi_queue_router_send() -> None:
    client = MagicMock()
    sender = MagicMock()
    client.get_queue_sender.return_value = sender
    router = MultiQueueRouter(client)
    with patch("vibey_bootstrap.servicebus.async_ext.ServiceBusMessage", create=True):
        router.send("q1", b"hello")
    sender.send_messages.assert_called_once()

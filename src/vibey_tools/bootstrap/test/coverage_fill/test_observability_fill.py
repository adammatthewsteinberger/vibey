"""Heartbeat, watchdog, identity health, and the @traced decorator.

These are the observability layer, so the property under test throughout is that
observing a failure never causes one: a broken snapshot, a dead credential, or an
alerting outage degrades the signal and leaves the workload running.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from unittest.mock import MagicMock

import pytest

import vibey_bootstrap.alerts as alerts
import vibey_bootstrap.heartbeat as hb
import vibey_bootstrap.identity as identity
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.identity import CredentialKind, TokenCache, build_credential
from vibey_bootstrap.tracing import decorators as tracing
from vibey_bootstrap.tracing.decorators import traced, traced_async


@pytest.fixture(autouse=True)
def reset():
    _reset_counters()
    alerts.reset_state()
    alerts.register_dispatcher(lambda *a: None, recipients=["ops@example.com"])
    yield
    alerts.reset_state()


def run_one_tick(start, *args, **kwargs) -> None:
    """Start a monitor thread, let it run exactly one iteration, then stop it."""
    stop = threading.Event()
    thread = start(stop, *args, **kwargs)
    try:
        deadline = time.monotonic() + 3.0
        while thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.02)
            if kwargs.get("_done", lambda: False)():
                break
    finally:
        stop.set()
        thread.join(timeout=2.0)


# ═══════════════════════════════════════════════════════════ heartbeat


def test_a_malformed_interval_falls_back_to_its_default(monkeypatch):
    monkeypatch.setenv("HEARTBEAT_INTERVAL_SECONDS", "soon")
    assert hb._env_float("HEARTBEAT_INTERVAL_SECONDS", 300.0) == 300.0


def test_recording_progress_survives_a_broken_state_lock(monkeypatch):
    broken = MagicMock()
    broken.__enter__ = MagicMock(side_effect=RuntimeError("lock is wedged"))
    monkeypatch.setattr(hb, "_state_lock", broken)
    hb.record_message_settled()  # must not raise
    hb.record_consumer_iteration()  # must not raise


def test_recording_an_iteration_logs_at_debug(caplog):
    with caplog.at_level(logging.DEBUG, logger=hb.__name__):
        hb.record_consumer_iteration()
    assert "consumer_iteration recorded" in caplog.text


def test_a_heartbeat_tick_that_fails_alerts_and_keeps_ticking(caplog):
    ticks = threading.Event()

    def broken_snapshot():
        ticks.set()
        raise RuntimeError("latency store is unreadable")

    sent: list[str] = []
    stop = threading.Event()
    with caplog.at_level(logging.ERROR):
        alerts.register_dispatcher(lambda r, s, b: sent.append(s), ["ops@example.com"])
        thread = hb.start_heartbeat(stop, interval_seconds=0.05, snapshot_fn=broken_snapshot)
        assert ticks.wait(3.0)
        time.sleep(0.1)
        stop.set()
        thread.join(timeout=2.0)

    assert "heartbeat tick failed" in caplog.text
    assert not thread.is_alive()


def test_a_heartbeat_tick_survives_alerting_that_is_also_broken(monkeypatch, caplog):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    ticks = threading.Event()

    def broken_snapshot():
        ticks.set()
        raise RuntimeError("latency store is unreadable")

    stop = threading.Event()
    with caplog.at_level(logging.ERROR):
        thread = hb.start_heartbeat(stop, interval_seconds=0.05, snapshot_fn=broken_snapshot)
        assert ticks.wait(3.0)
        time.sleep(0.1)
        stop.set()
        thread.join(timeout=2.0)
    assert not thread.is_alive()


def test_a_silent_consumer_raises_the_watchdog(monkeypatch):
    sent: list[str] = []
    alerts.register_dispatcher(lambda r, s, b: sent.append(s), ["ops@example.com"])
    monkeypatch.setattr(hb, "_last_iteration_age_seconds", lambda: 9999.0)
    monkeypatch.setattr(hb, "_last_watchdog_alert_at", 0.0, raising=False)

    stop = threading.Event()
    thread = hb.start_consumer_watchdog(stop, interval_seconds=0.05, silence_threshold_seconds=1.0)
    deadline = time.monotonic() + 3.0
    while hb._last_watchdog_alert_at == 0.0 and time.monotonic() < deadline:
        time.sleep(0.02)
    stop.set()
    thread.join(timeout=2.0)

    assert hb._last_watchdog_alert_at != 0.0
    hb._last_watchdog_alert_at = 0.0


def test_the_watchdog_survives_its_own_tick_failing(monkeypatch, caplog):
    ticks = threading.Event()

    def broken_age():
        ticks.set()
        raise RuntimeError("clock is unreadable")

    monkeypatch.setattr(hb, "_last_iteration_age_seconds", broken_age)
    stop = threading.Event()
    with caplog.at_level(logging.ERROR):
        thread = hb.start_consumer_watchdog(stop, interval_seconds=0.05)
        assert ticks.wait(3.0)
        time.sleep(0.1)
        stop.set()
        thread.join(timeout=2.0)
    assert "watchdog tick failed" in caplog.text


# ═══════════════════════════════════════════════════════════ identity


def test_a_client_secret_credential_needs_all_three_parts(monkeypatch):
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    with pytest.raises(ValueError, match="requires tenant_id, client_id, and client_secret"):
        build_credential(client_secret="s", prefer=CredentialKind.CLIENT_SECRET)


@pytest.mark.parametrize(
    "raw, enabled", [("1", True), ("TRUE", True), ("on", True), ("", False), ("no", False)]
)
def test_the_mock_switch_reads_the_usual_truthy_spellings(monkeypatch, raw, enabled):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", raw)
    assert identity._mock_enabled() is enabled


def test_credential_health_short_circuits_in_mock_mode(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "1")
    assert identity.credential_health() == {"status": "ok", "mock": True}


def test_credential_health_reports_a_credential_that_cannot_be_built(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    monkeypatch.setattr(
        identity, "build_credential", MagicMock(side_effect=RuntimeError("no identity endpoint"))
    )
    result = identity.credential_health()
    assert result["status"] == "error"
    assert "no identity endpoint" in result["message"]


def test_credential_health_reports_latency_on_a_successful_token(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    token = MagicMock(expires_on=1_800_000_000)
    monkeypatch.setattr(
        identity, "build_credential", lambda: MagicMock(get_token=MagicMock(return_value=token))
    )

    result = identity.credential_health(("https://vault.azure.net/.default",))
    assert result["status"] == "ok"
    assert isinstance(result["latency_ms"], int)
    assert result["expires_on"] == 1_800_000_000
    assert counter_snapshot()["identity.token_acquired..default"] == 1


def test_credential_health_reports_a_token_request_that_fails(monkeypatch):
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "0")
    credential = MagicMock()
    credential.get_token.side_effect = RuntimeError("AADSTS700016")
    monkeypatch.setattr(identity, "build_credential", lambda: credential)

    result = identity.credential_health()
    assert result["status"] == "error"
    assert counter_snapshot()["identity.token_failed"] == 1


def test_a_token_close_to_expiry_is_treated_as_a_cache_miss():
    identity._reset_token_cache()
    TokenCache.cache_token("t", "scope", "tok", expires_at=time.time() + 30)
    assert TokenCache.get_cached_token("t", "scope") is None


def test_a_token_with_plenty_of_life_left_is_returned():
    identity._reset_token_cache()
    TokenCache.cache_token("t", "scope", "tok", expires_at=time.time() + 3600)
    assert TokenCache.get_cached_token("t", "scope") == "tok"


def test_resetting_the_token_cache_refuses_outside_a_test_environment(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="AZURE_BOOTSTRAP_ALLOW_RESET"):
        identity._reset_token_cache()


# ═══════════════════════════════════════════════════════════ @traced


def test_masking_ignores_self_and_redacts_anything_that_looks_secret():
    class Service:
        def call(self, api_key: str, tenant: str) -> None: ...

    masked = tracing._mask_args_for_log(Service.call, (Service(), "sk-live", "acme"), {}, ())
    assert "self" not in masked
    assert masked["api_key"] == "***"
    assert "acme" in masked["tenant"]


def test_masking_a_signature_it_cannot_bind_yields_nothing():
    def takes_one(a): ...

    assert tracing._mask_args_for_log(takes_one, (1, 2, 3), {}, ()) == {}


def test_the_error_alert_never_breaks_the_raising_path(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    tracing._maybe_alert_error("op", ValueError("x"), "error", logging.getLogger(__name__))


def test_the_slow_alert_never_breaks_the_calling_path(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    tracing._slow_alert("op", 9.0, 1.0)


async def test_an_async_call_is_traced_at_debug_with_masked_arguments(caplog):
    @traced(operation="svc.fetch", log_result=True, sensitive_args=("token",))
    async def fetch(token: str, url: str) -> str:
        return "payload"

    with caplog.at_level(logging.DEBUG, logger=__name__):
        assert await fetch("sk-live", "https://example.com") == "payload"

    entry = next(r for r in caplog.records if r.getMessage().startswith("→"))
    assert entry.call_args["token"] == "***"
    exit_record = next(r for r in caplog.records if r.getMessage().startswith("✓"))
    assert "payload" in exit_record.result


async def test_an_async_failure_is_recorded_alerted_and_re_raised(caplog):
    @traced(operation="svc.explode", alert_on_error="error")
    async def explode() -> None:
        raise KeyError("missing")

    sent: list[str] = []
    alerts.register_dispatcher(lambda r, s, b: sent.append(s), ["ops@example.com"])
    with caplog.at_level(logging.ERROR, logger=__name__), pytest.raises(KeyError):
        await explode()
    assert any("svc.explode" in r.getMessage() for r in caplog.records)


async def test_a_slow_async_call_raises_the_slow_alert():
    fired: list[tuple] = []

    @traced(operation="svc.slow", slow_threshold_seconds=0.001)
    async def slow() -> int:
        await asyncio.sleep(0.02)
        return 1

    import vibey_bootstrap.tracing.decorators as d

    original = d._slow_alert
    d._slow_alert = lambda *a: fired.append(a)
    try:
        assert await slow() == 1
    finally:
        d._slow_alert = original
    assert fired and fired[0][0] == "svc.slow"


def test_a_slow_sync_call_logs_its_result_when_asked(caplog):
    @traced(operation="svc.sync", log_result=True)
    def work() -> str:
        return "done"

    with caplog.at_level(logging.DEBUG, logger=__name__):
        assert work() == "done"
    exit_record = next(r for r in caplog.records if r.getMessage().startswith("✓"))
    assert "done" in exit_record.result


def test_traced_async_is_the_same_decorator():
    @traced_async(operation="svc.alias")
    def plain() -> int:
        return 7

    assert plain() == 7

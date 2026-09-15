"""AI usage governance: pricing overrides, the soft TPM cap, and threshold alerts.

The governing rule for this module is stated in its own docstrings — cost tracking and
rate limiting must never break the calling path — so most of these tests break something
and assert that the caller still gets through.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

import vibey_bootstrap.alerts as alerts
import vibey_bootstrap.openai as ai
from vibey_bootstrap.counters import _reset_counters, counter_snapshot


@pytest.fixture(autouse=True)
def reset():
    ai.reset_state()
    _reset_counters()
    alerts.reset_state()
    alerts.register_dispatcher(lambda *a: None, recipients=["ops@example.com"])
    yield
    ai.reset_state()
    alerts.reset_state()


# ── pricing ────────────────────────────────────────────────────────────────


def test_a_pricing_override_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("AI_PRICING_GPT_4O_INPUT_PER_1K", "0.01")
    monkeypatch.setenv("AI_PRICING_GPT_4O_OUTPUT_PER_1K", "0.03")
    assert ai._pricing_for("gpt-4o") == (0.01, 0.03)


def test_a_malformed_pricing_override_falls_through_to_the_table(monkeypatch):
    monkeypatch.setenv("AI_PRICING_GPT_4O_INPUT_PER_1K", "free")
    monkeypatch.setenv("AI_PRICING_GPT_4O_OUTPUT_PER_1K", "cheap")
    assert ai._pricing_for("gpt-4o") != (0.0, 0.0)  # the built-in table, not the junk


def test_an_unknown_deployment_gets_the_fallback_price():
    assert ai._pricing_for("some-model-nobody-has-priced") == ai._FALLBACK_PRICING


def test_recording_usage_that_cannot_be_priced_is_swallowed(monkeypatch):
    monkeypatch.setattr(ai, "_compute_cost", MagicMock(side_effect=RuntimeError("bad table")))
    ai.record_usage("gpt-4o", 100, 50)  # must not raise
    assert "ai.calls" not in counter_snapshot()


# ── rate-limit events ──────────────────────────────────────────────────────


def test_a_rate_limit_event_is_counted_even_when_alerting_is_broken(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    ai.record_rate_limit_event("gpt-4o", source="header")
    assert counter_snapshot()["ai.rate_limit_events"] == 1


def test_a_rate_limit_event_survives_its_own_bookkeeping_failing(monkeypatch):
    monkeypatch.setattr(ai, "bump_counter", MagicMock(side_effect=RuntimeError("counters down")))
    ai.record_rate_limit_event("gpt-4o", source="header")  # must not raise


# ── TPM limits ─────────────────────────────────────────────────────────────


def test_a_per_deployment_tpm_limit_wins_over_the_global_one(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "1000")
    monkeypatch.setenv("AI_TPM_LIMIT_GPT_4O", "50")
    assert ai._tpm_limit_for("gpt-4o") == 50


def test_a_malformed_per_deployment_limit_falls_back_to_the_global_one(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "1000")
    monkeypatch.setenv("AI_TPM_LIMIT_GPT_4O", "lots")
    assert ai._tpm_limit_for("gpt-4o") == 1000


def test_a_malformed_global_limit_means_no_limit(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "lots")
    assert ai._tpm_limit_for("gpt-4o") == 0


# ── acquire: the soft cap ──────────────────────────────────────────────────


def test_acquire_returns_immediately_when_there_is_headroom(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "1000")
    ai.record_usage("gpt-4o", 10, 10)
    started = time.monotonic()
    ai.acquire("gpt-4o", estimated_tokens=100)
    assert time.monotonic() - started < 0.5


def test_acquire_lets_the_call_through_once_max_wait_is_exceeded(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "10")
    ai.record_usage("gpt-4o", 100, 100)  # already far over the cap
    sent: list[str] = []
    monkeypatch.setattr(
        alerts, "alert_dev_team", lambda severity, subject, **kw: sent.append(subject)
    )

    ai.acquire("gpt-4o", estimated_tokens=50, timeout=0.0)

    assert any("max-wait exceeded" in s for s in sent)
    assert counter_snapshot()["ai.rate_limit_events"] == 1


def test_acquire_lets_the_call_through_even_when_the_alert_fails(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "10")
    ai.record_usage("gpt-4o", 100, 100)
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    ai.acquire("gpt-4o", estimated_tokens=50, timeout=0.0)  # must not raise


def test_acquire_waits_then_gives_up_recording_the_wait_only_once(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "10")
    monkeypatch.setattr(ai.time, "sleep", MagicMock())  # do not actually wait
    ai.record_usage("gpt-4o", 100, 100)

    ai.acquire("gpt-4o", estimated_tokens=50, timeout=0.3)

    ai.time.sleep.assert_called()
    # "proactive" once for the first wait, "proactive_timeout" once at the end.
    assert counter_snapshot()["ai.rate_limit_events"] == 2


def test_acquire_never_propagates_a_failure_from_its_own_machinery(monkeypatch):
    monkeypatch.setenv("AI_TPM_LIMIT", "10")
    monkeypatch.setattr(
        ai, "_tokens_in_window", MagicMock(side_effect=RuntimeError("state is corrupt"))
    )
    ai.acquire("gpt-4o", estimated_tokens=50)  # must not raise


# ── pruning + snapshot ─────────────────────────────────────────────────────


def test_entries_older_than_a_day_are_pruned_from_the_snapshot(monkeypatch):
    ai.record_usage("gpt-4o", 100, 100)
    entry = ai._state.recent[0]
    ai._state.recent[0] = type(entry)(
        **{**entry.__dict__, "ts": time.monotonic() - ai._DAILY_WINDOW_SECONDS - 10}
    )
    ai._prune_old()
    assert not ai._state.recent


# ── threshold alerts ───────────────────────────────────────────────────────


def test_a_threshold_alert_fires_once_then_waits_out_its_cooldown():
    assert ai._fire_threshold_alert("k", subject="s", context={}) is True
    assert ai._fire_threshold_alert("k", subject="s", context={}) is False


def test_a_threshold_alert_reports_fired_even_when_alerting_is_broken(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    assert ai._fire_threshold_alert("k", subject="s", context={}) is True


@pytest.mark.parametrize(
    "env",
    ["AI_COST_ALERT_HOURLY_DOLLARS", "AI_COST_ALERT_DAILY_DOLLARS", "AI_HIGH_USAGE_TOKENS_HOURLY"],
)
def test_a_malformed_threshold_disables_only_that_threshold(monkeypatch, env):
    monkeypatch.setenv(env, "a lot")
    ai.record_usage("gpt-4o", 1_000_000, 1_000_000)
    assert ai.check_thresholds_and_alert()["fired"] == []


def test_every_breached_threshold_is_reported(monkeypatch):
    monkeypatch.setenv("AI_COST_ALERT_HOURLY_DOLLARS", "0.000001")
    monkeypatch.setenv("AI_COST_ALERT_DAILY_DOLLARS", "0.000001")
    monkeypatch.setenv("AI_HIGH_USAGE_TOKENS_HOURLY", "1")
    ai.record_usage("gpt-4o", 5000, 5000)

    fired = {f["subject"] for f in ai.check_thresholds_and_alert()["fired"]}
    assert fired == {"hourly_cost", "daily_cost", "hourly_tokens"}


def test_reset_state_refuses_outside_a_test_environment(monkeypatch):
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError, match="test-only"):
        ai.reset_state()

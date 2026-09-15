"""Tests for ``vibey_bootstrap.openai``."""

from __future__ import annotations

import time

import pytest

from vibey_bootstrap.openai import (
    _pricing_for,
    acquire,
    check_thresholds_and_alert,
    record_usage,
    register_pricing,
    reset_state,
    usage_snapshot,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_state()


def test_record_usage_accumulates() -> None:
    record_usage("gpt-4o", 1000, 500)
    record_usage("gpt-4o", 2000, 1000)
    snap = usage_snapshot()
    cum = snap["by_deployment"]["gpt-4o"]["cumulative"]
    assert cum["prompt_tokens"] == 3000
    assert cum["completion_tokens"] == 1500
    assert cum["calls"] == 2
    # gpt-4o pricing: 0.0025 input + 0.01 output per 1k.
    # (3000/1000 * 0.0025) + (1500/1000 * 0.01) = 0.0075 + 0.015 = 0.0225
    assert cum["cost_usd"] == pytest.approx(0.0225, rel=1e-6)


def test_acquire_no_op_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_TPM_LIMIT", raising=False)
    start = time.monotonic()
    acquire("gpt-4o", 100_000)
    assert (time.monotonic() - start) < 0.1


def test_acquire_max_wait_lets_call_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_TPM_LIMIT", "1000")
    monkeypatch.setenv("AI_RATE_LIMIT_MAX_WAIT_SECONDS", "0.2")
    record_usage("gpt-4o", 1000, 0)
    start = time.monotonic()
    acquire("gpt-4o", 500)  # would exceed limit
    elapsed = time.monotonic() - start
    assert elapsed >= 0.1  # we did wait
    assert elapsed < 1.5  # but not forever — should release


def test_pricing_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PRICING_GPT_4O_INPUT_PER_1K", "0.005")
    monkeypatch.setenv("AI_PRICING_GPT_4O_OUTPUT_PER_1K", "0.02")
    in_p, out_p = _pricing_for("gpt-4o")
    assert in_p == 0.005
    assert out_p == 0.02


def test_pricing_longest_substring_wins() -> None:
    in_p, out_p = _pricing_for("gpt-4o-mini-preview")
    # gpt-4o-mini pricing (0.00015 / 0.0006), NOT gpt-4o (0.0025 / 0.01).
    assert in_p == 0.00015
    assert out_p == 0.0006


def test_register_pricing_takes_precedence() -> None:
    register_pricing("my-fancy-deployment", input_per_1k=0.123, output_per_1k=0.456)
    assert _pricing_for("my-fancy-deployment-v2") == (0.123, 0.456)


def test_threshold_alert_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two threshold breaches within the cooldown fire one alert, not two."""
    monkeypatch.setenv("AI_COST_ALERT_HOURLY_DOLLARS", "0.0001")
    record_usage("gpt-4o", 10_000, 10_000)
    result1 = check_thresholds_and_alert()
    result2 = check_thresholds_and_alert()
    fired1 = {f["key"] for f in result1["fired"]}
    fired2 = {f["key"] for f in result2["fired"]}
    assert "ai_usage.cost_hourly:gpt-4o" in fired1
    assert "ai_usage.cost_hourly:gpt-4o" not in fired2

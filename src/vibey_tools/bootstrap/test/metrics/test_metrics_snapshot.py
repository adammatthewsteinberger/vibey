"""Tests for ``vibey_bootstrap.metrics.build_metrics_snapshot``."""

from __future__ import annotations

from vibey_bootstrap.metrics import build_metrics_snapshot


def test_always_includes_latency_and_counters() -> None:
    snap = build_metrics_snapshot()
    assert "latency" in snap
    assert "alert_counters" in snap


def test_includes_bootstrap_initialized() -> None:
    snap = build_metrics_snapshot()
    assert "bootstrap_initialized" in snap


def test_includes_optional_sections_when_modules_installed() -> None:
    snap = build_metrics_snapshot()
    # openai + heartbeat are part of this repo, so always present.
    assert "ai_usage" in snap
    assert "last_sb_settle_age_seconds" in snap

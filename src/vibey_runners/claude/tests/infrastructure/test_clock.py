# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/clock.py — SystemClock and AnyioSleeper."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from claudeloop.infrastructure.clock import AnyioSleeper, SystemClock


def test_system_clock_returns_utc_datetime() -> None:
    clock = SystemClock()
    now = clock.now()
    assert isinstance(now, datetime)
    assert now.tzinfo == timezone.utc


def test_system_clock_is_recent() -> None:
    clock = SystemClock()
    now = clock.now()
    delta = abs((datetime.now(timezone.utc) - now).total_seconds())
    assert delta < 2


@pytest.mark.asyncio
async def test_sleeper_skips_when_already_past() -> None:
    clock = SystemClock()
    sleeper = AnyioSleeper(clock)
    past = clock.now() - timedelta(seconds=10)
    await sleeper.sleep_until(past)  # should not block


@pytest.mark.asyncio
async def test_sleeper_sleeps_briefly() -> None:
    clock = SystemClock()
    sleeper = AnyioSleeper(clock)
    target = clock.now() + timedelta(milliseconds=50)
    await sleeper.sleep_until(target)
    assert clock.now() >= target

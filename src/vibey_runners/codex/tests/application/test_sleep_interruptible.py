# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tri-state sleep_interruptible: polls control inbox, returns early on stop/wind-down."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from codexloop.application.runner import AutonomousRunner, RunnerContext
from codexloop.domain.control import Stop, WindDownCommand
from tests.application.fakes import (
    FakeAgentGateway,
    FakeCapacityProbe,
    FakeClock,
    FakeRunControl,
    FakeRunStateStore,
    FakeSleeper,
)


@pytest.mark.asyncio
async def test_sleep_interruptible_returns_stop_when_stop_arrives() -> None:
    """If a Stop command arrives during sleep, return 'stop' early."""
    clock = FakeClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    sleeper = FakeSleeper(clock)
    # First poll returns empty, second poll returns Stop
    control = FakeRunControl(script=[[], [Stop()]])

    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=FakeAgentGateway(),
        probe=FakeCapacityProbe(),
        store=FakeRunStateStore(),
        control=control,
    )
    runner = AutonomousRunner(ctx)

    # Sleep for 10 seconds - should return early with "stop" when polled
    target = clock.now() + timedelta(seconds=10)
    result = await runner._sleep_interruptible(target)

    assert result == "stop"
    # Should not have slept the full duration
    assert clock.now() < target


@pytest.mark.asyncio
async def test_sleep_interruptible_returns_wind_down_when_wind_down_arrives() -> None:
    """If a WindDownCommand arrives during sleep, return 'wind_down' early."""
    clock = FakeClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    sleeper = FakeSleeper(clock)
    # First poll returns empty, second poll returns WindDownCommand
    control = FakeRunControl(script=[[], [WindDownCommand(reason="capacity")]])

    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=FakeAgentGateway(),
        probe=FakeCapacityProbe(),
        store=FakeRunStateStore(),
        control=control,
    )
    runner = AutonomousRunner(ctx)

    # Sleep for 10 seconds - should return early with "wind_down"
    target = clock.now() + timedelta(seconds=10)
    result = await runner._sleep_interruptible(target)

    assert result == "wind_down"
    # Should not have slept the full duration
    assert clock.now() < target


@pytest.mark.asyncio
async def test_sleep_interruptible_returns_none_when_no_interrupt() -> None:
    """If no interrupt arrives, sleep completes and returns None."""
    clock = FakeClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    sleeper = FakeSleeper(clock)
    control = FakeRunControl([])

    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=FakeAgentGateway(),
        probe=FakeCapacityProbe(),
        store=FakeRunStateStore(),
        control=control,
    )
    runner = AutonomousRunner(ctx)

    # No commands - sleep should complete normally
    target = clock.now() + timedelta(seconds=2)
    result = await runner._sleep_interruptible(target)

    assert result is None
    # Should have advanced to target time
    assert clock.now() >= target


@pytest.mark.asyncio
async def test_sleep_interruptible_polls_periodically() -> None:
    """Sleep polls control inbox periodically during the wait."""
    clock = FakeClock(datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC))
    sleeper = FakeSleeper(clock)
    poll_count = 0

    class CountingControl(FakeRunControl):
        def poll(self):
            nonlocal poll_count
            poll_count += 1
            return super().poll()

    counting_control = CountingControl([])

    ctx = RunnerContext(
        clock=clock,
        sleeper=sleeper,
        gateway=FakeAgentGateway(),
        probe=FakeCapacityProbe(),
        store=FakeRunStateStore(),
        control=counting_control,
    )
    runner = AutonomousRunner(ctx)

    # Sleep for 3 seconds - should poll multiple times (at least 3 times: 0s, 1s, 2s, 3s)
    target = clock.now() + timedelta(seconds=3)
    await runner._sleep_interruptible(target)

    # Should have polled at least 3-4 times (once per second)
    assert poll_count >= 3

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Each application port has a fake that structurally satisfies its Protocol."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import monotonic

import pytest

from codexloop.application.ports import (
    AgentGateway,
    ApiGateway,
    AuditLog,
    CapacityProbe,
    Clock,
    Logger,
    Notifier,
    ProgressReporter,
    RunControl,
    RunEventSink,
    RunResources,
    RunSnapshotSink,
    RunStateStore,
    SavePointStore,
    SessionLock,
    Sleeper,
    StateBus,
    ThreadCatalog,
)
from tests.application.fakes import (
    FakeAgentGateway,
    FakeApiGateway,
    FakeAuditLog,
    FakeCapacityProbe,
    FakeClock,
    FakeLogger,
    FakeNotifier,
    FakeProgressReporter,
    FakeRunControl,
    FakeRunEventSink,
    FakeRunResources,
    FakeRunSnapshotSink,
    FakeRunStateStore,
    FakeSavePointStore,
    FakeSessionLock,
    FakeSleeper,
    FakeStateBus,
    FakeThreadCatalog,
)

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)

_PROTOCOL_CASES: list[tuple[str, object, type[object]]] = [
    ("Clock", FakeClock(NOW), Clock),
    ("Sleeper", FakeSleeper(FakeClock(NOW)), Sleeper),
    ("AgentGateway", FakeAgentGateway(), AgentGateway),
    ("CapacityProbe", FakeCapacityProbe(), CapacityProbe),
    ("ThreadCatalog", FakeThreadCatalog(), ThreadCatalog),
    ("ProgressReporter", FakeProgressReporter(), ProgressReporter),
    ("AuditLog", FakeAuditLog(), AuditLog),
    ("Notifier", FakeNotifier(), Notifier),
    ("Logger", FakeLogger(), Logger),
    ("RunStateStore", FakeRunStateStore(), RunStateStore),
    ("SessionLock", FakeSessionLock(), SessionLock),
    ("RunControl", FakeRunControl(), RunControl),
    ("RunEventSink", FakeRunEventSink(), RunEventSink),
    ("StateBus", FakeStateBus(), StateBus),
    ("SavePointStore", FakeSavePointStore(), SavePointStore),
    ("RunSnapshotSink", FakeRunSnapshotSink(), RunSnapshotSink),
    ("ApiGateway", FakeApiGateway(), ApiGateway),
    ("RunResources", FakeRunResources(), RunResources),
]


@pytest.mark.parametrize(
    ("fake", "protocol"),
    [(fake, protocol) for _, fake, protocol in _PROTOCOL_CASES],
    ids=[name for name, _, _ in _PROTOCOL_CASES],
)
def test_fake_structurally_satisfies_protocol(fake: object, protocol: type[object]) -> None:
    assert isinstance(fake, protocol)


def test_fake_clock_advance_moves_now_by_delta() -> None:
    clock = FakeClock(NOW)
    clock.advance(timedelta(hours=2))
    assert clock.now() == NOW + timedelta(hours=2)


async def test_fake_sleeper_seven_day_wait_advances_clock_with_zero_wall_time() -> None:
    clock = FakeClock(NOW)
    sleeper = FakeSleeper(clock)
    target = NOW + timedelta(days=7)

    started = monotonic()
    await sleeper.sleep_until(target)
    elapsed = monotonic() - started

    assert clock.now() == target
    assert sleeper.requested == [target]
    assert elapsed < 0.05


async def test_fake_sleeper_does_not_rewind_clock_when_target_is_in_the_past() -> None:
    clock = FakeClock(NOW)
    sleeper = FakeSleeper(clock)
    past = NOW - timedelta(days=1)

    await sleeper.sleep_until(past)

    assert clock.now() == NOW
    assert sleeper.requested == [past]

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import timedelta

import anyio

from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from tests.application import fakes


def test_no_delta_for_the_stall_timeout_cancels_the_run() -> None:
    """A model that stops emitting and never terminates is the stall path with
    no interception point — Cursor exposes no ask-user tool to intercept. The
    watchdog is what makes it survivable."""
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=30), stall_timeout=timedelta(minutes=10), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=11))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 1


def test_a_terminal_run_is_never_cancelled() -> None:
    """run.cancel() on an already-terminal run raises
    UnsupportedRunOperationError. Guard on run.status."""
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="finished")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=1), stall_timeout=timedelta(minutes=1), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=5))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 0


def test_a_delta_resets_the_stall_clock() -> None:
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(hours=2), stall_timeout=timedelta(minutes=10), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=9))
    watchdog.saw_delta()
    clock.advance(timedelta(minutes=9))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 0


def test_turn_timeout_cancels_even_when_deltas_keep_arriving() -> None:
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=5), stall_timeout=timedelta(hours=1), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=4))
    watchdog.saw_delta()
    clock.advance(timedelta(minutes=2))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 1


def test_tick_without_a_started_turn_is_a_noop() -> None:
    clock = fakes.FakeClock()
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=1), stall_timeout=timedelta(minutes=1), clock=clock
    )
    clock.advance(timedelta(minutes=5))
    anyio.run(watchdog.tick)


def test_cancelled_and_error_runs_are_not_cancelled_again() -> None:
    clock = fakes.FakeClock()
    for status in ("cancelled", "error", "expired"):
        run = fakes.FakeRun(status=status)
        watchdog = TurnWatchdog(
            turn_timeout=timedelta(minutes=1), stall_timeout=timedelta(minutes=1), clock=clock
        )
        watchdog.turn_started(run)
        clock.advance(timedelta(minutes=5))
        anyio.run(watchdog.tick)
        assert run.cancel_calls == 0

# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application tests: runner emits snapshot reasons via FakeSnapshotSink."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from claudeloop.application.runner import AutonomousRunner
from claudeloop.domain.budget import Budget
from claudeloop.domain.control import StopCommand
from claudeloop.domain.waiting import WaitPolicyConfig
from tests.application.fakes import (
    CONTINUE_VERDICT,
    DONE_VERDICT,
    FakeAgentGateway,
    FakeAuditLog,
    FakeCapacityProbe,
    FakeClock,
    FakeEventSink,
    FakeNotifier,
    FakeProgressReporter,
    FakeRunControl,
    FakeSavePointStore,
    FakeSessionLock,
    FakeSleeper,
    FakeSnapshotSink,
    FakeStateStore,
    ScriptedTurn,
    available_signals,
    window_exhausted_signals,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def _make(
    *,
    turns: list[ScriptedTurn],
    probes: list,
    run_control: FakeRunControl | None = None,
    wait_policy: WaitPolicyConfig | None = None,
) -> tuple[AutonomousRunner, FakeSnapshotSink]:
    clock = FakeClock(start=NOW)
    snaps = FakeSnapshotSink()
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(turns),
        capacity_probe=FakeCapacityProbe(probes),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=Budget(),
        wait_policy=wait_policy or WaitPolicyConfig(),
        done_marker="TEST_DONE_MARKER",
        run_id="snap-run",
        notifier=FakeNotifier(),
        run_control=run_control or FakeRunControl(),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        snapshot_sink=snaps,
    )
    return runner, snaps


@pytest.mark.asyncio
async def test_runner_emits_started_status_finished() -> None:
    runner, snaps = _make(
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=DONE_VERDICT,
                output_text="done TEST_DONE_MARKER",
                session_id="sess-1",
            )
        ],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="go", continue_prompt="cont")
    assert result.success
    reasons = [r for r, _, _ in snaps.emits]
    assert reasons[0] == "started"
    assert "status" in reasons
    assert reasons[-1] == "finished"
    finished_ctx = snaps.emits[-1][1]
    assert finished_ctx is not None
    assert finished_ctx.get("session_id") == "sess-1"
    assert "model" in finished_ctx


@pytest.mark.asyncio
async def test_runner_turn_without_session_id_still_persists() -> None:
    runner, snaps = _make(
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=DONE_VERDICT,
                output_text="done",
                session_id=None,
            )
        ],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="go", continue_prompt="cont")
    assert result.success
    assert any(r == "finished" for r, _, _ in snaps.emits)


@pytest.mark.asyncio
async def test_runner_emits_waiting_and_stopped() -> None:
    control = FakeRunControl(
        script=[
            [],  # loop start before first turn
            [],  # loop start entering ScheduleProbe
            [],  # first poll inside sleep
            [StopCommand()],  # stop during wait
        ]
    )
    runner, snaps = _make(
        turns=[
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=NOW + timedelta(hours=1)),
                verdict=CONTINUE_VERDICT,
                output_text="rate limited",
                session_id="sess-w",
            )
        ],
        probes=[available_signals()],
        run_control=control,
        wait_policy=WaitPolicyConfig(reset_grace=timedelta(seconds=1)),
    )
    result = await runner.run(initial_prompt="go", continue_prompt="cont")
    assert result.success is False
    reasons = [r for r, _, _ in snaps.emits]
    assert "started" in reasons
    assert "waiting" in reasons
    assert "stopped" in reasons

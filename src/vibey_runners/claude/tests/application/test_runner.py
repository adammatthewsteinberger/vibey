# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import datetime, timedelta, timezone

import pytest

from claudeloop.application.runner import AutonomousRunner
from claudeloop.domain.budget import Budget
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict
from claudeloop.domain.control import (
    PromptDeferredCommand,
    PromptNowCommand,
    StopCommand,
    WindDownCommand,
)
from claudeloop.domain.forecast import WindDownPolicy
from claudeloop.domain.handoff_marker import HandoffMarker
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
    FakeStateStore,
    ScriptedTurn,
    available_signals,
    credits_exhausted_signals,
    window_exhausted_signals,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
_DEFAULT_BUDGET = Budget()
_DEFAULT_WAIT_POLICY = WaitPolicyConfig()


def make_runner(
    *,
    turns: list[ScriptedTurn],
    probes: list,
    budget: Budget = _DEFAULT_BUDGET,
    wait_policy: WaitPolicyConfig = _DEFAULT_WAIT_POLICY,
    run_control: FakeRunControl | None = None,
    notifier: FakeNotifier | None = None,
    save_points: FakeSavePointStore | None = None,
) -> tuple[
    AutonomousRunner,
    FakeAgentGateway,
    FakeAuditLog,
    FakeProgressReporter,
    FakeSleeper,
    FakeNotifier,
    FakeEventSink,
]:
    clock = FakeClock(start=NOW)
    sleeper = FakeSleeper(clock)
    gateway = FakeAgentGateway(turns)
    probe = FakeCapacityProbe(probes)
    audit = FakeAuditLog()
    progress = FakeProgressReporter()
    notifier = notifier or FakeNotifier()
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=audit,
        progress=progress,
        budget=budget,
        wait_policy=wait_policy,
        done_marker="TEST_DONE_MARKER",
        run_id="test-run",
        notifier=notifier,
        run_control=run_control or FakeRunControl(),
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=save_points or FakeSavePointStore(),
    )
    return runner, gateway, audit, progress, sleeper, notifier, events


async def test_preflight_available_then_done_in_one_turn() -> None:
    runner, gateway, _audit, progress, _sleeper, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="do the thing", continue_prompt="continue")
    assert result.success is True
    assert result.reason == "all done"
    assert result.turns_spent == 1
    assert gateway.closed is True
    assert gateway.sent_prompts == ["do the thing"]
    assert progress.finishes == [(True, "all done")]


async def test_continue_verdict_sends_a_second_turn_with_continue_prompt() -> None:
    runner, gateway, _audit, _progress, _sleeper, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert result.turns_spent == 2
    assert gateway.sent_prompts == ["start", "keep going"]


async def test_limit_outranks_a_done_verdict_on_the_same_turn() -> None:
    """The single most important invariant, exercised through the real
    AutonomousRunner rather than just domain.loop directly: a turn that hits
    a rate limit must never be treated as complete, even if it also carries
    a Done-shaped verdict."""
    runner, _gateway, _audit, _progress, sleeper, _n, _e = make_runner(
        turns=[
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=NOW + timedelta(minutes=1)),
                verdict=DONE_VERDICT,
            ),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals(), available_signals()],
        wait_policy=WaitPolicyConfig(reset_grace=timedelta(seconds=1)),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert len(sleeper.wait_log) >= 1
    assert result.turns_spent == 2


async def test_credit_topup_resumes_after_several_failed_probes_end_to_end() -> None:
    notifier = FakeNotifier()
    runner, gateway, _audit, _progress, sleeper, notifier, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[
            credits_exhausted_signals(),
            credits_exhausted_signals(),
            credits_exhausted_signals(),
            credits_exhausted_signals(),
            available_signals(),
        ],
        wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
        notifier=notifier,
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert len(sleeper.wait_log) >= 4
    assert gateway.sent_prompts == ["start"]
    assert any("credits exhausted" in m for m in notifier.messages)


async def test_authentication_failure_is_terminal_and_never_retried() -> None:
    runner, gateway, _audit, progress, sleeper, _n, _e = make_runner(
        turns=[],
        probes=[TurnSignals(assistant_error="authentication_failed")],
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "authentication failed"
    assert sleeper.wait_log == []
    assert gateway.sent_prompts == []
    assert progress.finishes == [(False, "authentication failed")]


async def test_budget_exhaustion_stops_the_run_cleanly() -> None:
    runner, _gateway, _audit, _progress, _sleeper, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
        ],
        probes=[available_signals()],
        budget=Budget(max_turns=2),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "budget exhausted"
    assert result.turns_spent == 2


async def test_dollar_budget_uses_turn_cost() -> None:
    runner, _gateway, _audit, _progress, _sleeper, _n, _e = make_runner(
        turns=[
            ScriptedTurn(
                signals=available_signals(),
                verdict=CONTINUE_VERDICT,
                cost_usd=1.5,
            ),
        ],
        probes=[available_signals()],
        budget=Budget(max_dollars=1.0),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "budget exhausted"
    assert result.dollars_spent == 1.5


async def test_blocked_verdict_fails_with_the_stated_reason() -> None:
    blocked = StructuredVerdict(complete=False, blocked_on="missing MCP credentials")
    runner, _gateway, _audit, _progress, _sleeper, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=blocked)],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "missing MCP credentials"


async def test_audit_log_records_every_phase_transition() -> None:
    runner, _gateway, audit, _progress, _sleeper, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
    )
    await runner.run(initial_prompt="start", continue_prompt="keep going")
    event_types = [e[0] for e in audit.events]
    assert event_types == ["preflight", "turn", "finished"]


async def test_stop_command_ends_run_and_closes_gateway() -> None:
    control = FakeRunControl(script=[[StopCommand()]])
    summaries: list[str] = []
    runner, gateway, _a, _p, _s, _n, events = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
        run_control=control,
    )
    runner._stop_summary_writer = lambda md: summaries.append(md) or "stop.md"
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert "stopped" in result.reason
    assert gateway.closed is True
    assert summaries
    assert any(e[0] == "control.stop" for e in events.events)


async def test_prompt_now_replaces_continue_prompt() -> None:
    control = FakeRunControl(
        script=[
            [],
            [PromptNowCommand(text="injected now")],
        ]
    )
    runner, gateway, _a, _p, _s, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        run_control=control,
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert gateway.sent_prompts == ["start", "injected now"]


async def test_prompt_deferred_applies_at_natural_break() -> None:
    control = FakeRunControl(
        script=[
            [PromptDeferredCommand(text="later please")],
            [],
        ]
    )
    runner, gateway, _a, _p, _s, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        run_control=control,
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert gateway.sent_prompts == ["start", "later please"]


async def test_stop_during_wait_interrupts_sleep() -> None:
    control = FakeRunControl(
        script=[
            [],  # loop start before first turn
            [],  # loop start entering ScheduleProbe
            [],  # first poll inside sleep — allow one chunk
            [StopCommand()],  # second poll inside sleep — stop
        ]
    )
    runner, gateway, _a, _p, sleeper, _n, _e = make_runner(
        turns=[
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=NOW + timedelta(hours=1)),
                verdict=CONTINUE_VERDICT,
            ),
        ],
        probes=[available_signals()],
        run_control=control,
        wait_policy=WaitPolicyConfig(reset_grace=timedelta(seconds=1)),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert "stopped" in result.reason
    assert gateway.closed is True
    assert len(sleeper.wait_log) >= 1


WAIT_ONLY_CONTINUE = StructuredVerdict(complete=False, remaining_work=("Waiting for E2E suite",))


async def test_wait_only_continue_triggers_progress_wait() -> None:
    runner, gateway, _a, _p, sleeper, _n, events = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=WAIT_ONLY_CONTINUE),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        save_points=FakeSavePointStore(reuse_sha=True),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert any(e[0] == "progress.wait" for e in events.events)
    savepoint_events = [e for e in events.events if e[0] == "savepoint"]
    assert savepoint_events
    assert savepoint_events[0][1] is not None
    assert savepoint_events[0][1]["committed"] is False
    assert len(sleeper.wait_log) >= 1
    assert gateway.sent_prompts == ["start", "keep going"]


async def test_first_savepoint_with_commit_skips_progress_wait() -> None:
    """A wait-only Continue that actually committed must not back off."""
    runner, gateway, _a, _p, sleeper, _n, events = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=WAIT_ONLY_CONTINUE),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        save_points=FakeSavePointStore(reuse_sha=False),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert not any(e[0] == "progress.wait" for e in events.events)
    assert gateway.sent_prompts == ["start", "keep going"]


async def test_stop_during_progress_wait() -> None:
    control = FakeRunControl(
        script=[
            [],  # before first turn
            [],  # after turn, entering DelayThenSend
            [],  # first sleep poll
            [StopCommand()],
        ]
    )
    runner, gateway, _a, _p, sleeper, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=WAIT_ONLY_CONTINUE)],
        probes=[available_signals()],
        run_control=control,
        save_points=FakeSavePointStore(reuse_sha=True),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert "progress wait" in result.reason
    assert gateway.closed is True
    assert len(sleeper.wait_log) >= 1


async def test_probe_keeps_waiting_meta_when_still_exhausted() -> None:
    metas: list[dict[str, object]] = []
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe(
            [
                available_signals(),  # preflight
                credits_exhausted_signals(),  # first probe — still exhausted
                available_signals(),  # second probe — restored
            ]
        ),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
        run_id="sticky-meta",
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        meta_updater=lambda **kw: metas.append(dict(kw)),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    waiting_after_probe = [
        m for m in metas if m.get("status") == "waiting" and m.get("waiting_until")
    ]
    assert waiting_after_probe, "probe that stays exhausted must keep waiting meta"


async def test_probe_auth_failure_clears_waiting_without_forcing_active() -> None:
    metas: list[dict[str, object]] = []
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT)]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe(
            [
                available_signals(),
                TurnSignals(assistant_error="authentication_failed"),
            ]
        ),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
        run_id="probe-auth",
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        meta_updater=lambda **kw: metas.append(dict(kw)),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "authentication failed"
    # Finish-after-probe clears waiting_until without stamping status=active over failed.
    finish_clears = [
        m for m in metas if set(m.keys()) == {"waiting_until"} and m["waiting_until"] is None
    ]
    assert finish_clears
    assert any(m.get("status") == "failed" for m in metas)


async def test_empty_zero_cost_turns_increment_streak_then_block() -> None:
    runner, gateway, _a, _p, _s, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=None, output_text="", cost_usd=0.0),
            ScriptedTurn(signals=available_signals(), verdict=None, output_text="", cost_usd=0.0),
            ScriptedTurn(signals=available_signals(), verdict=None, output_text="", cost_usd=0.0),
        ],
        probes=[available_signals()],
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is False
    assert result.reason == "repeated empty model responses"
    assert len(gateway.sent_prompts) == 3


async def test_sticky_credits_survives_available_probe() -> None:
    runner, gateway, _a, _p, sleeper, _n, events = make_runner(
        turns=[
            ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[
            available_signals(),  # preflight
            available_signals(),  # probe after credits wait — sticky still true
        ],
        wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert result.success is True
    assert any(e[0] == "capacity.probe_available" for e in events.events)
    assert len(sleeper.wait_log) >= 1
    assert gateway.sent_prompts == ["start", "keep going"]


async def test_run_exception_marks_meta_failed() -> None:
    class BoomGateway(FakeAgentGateway):
        async def send_turn(self, prompt_text: str):  # type: ignore[override]
            del prompt_text
            raise RuntimeError("boom")

    metas: list[dict[str, object]] = []
    clock = FakeClock(start=NOW)
    gateway = BoomGateway([])
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_id="boom-run",
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        meta_updater=lambda **kw: metas.append(kw),
    )
    with pytest.raises(RuntimeError, match="boom"):
        await runner.run(initial_prompt="start", continue_prompt="keep going")
    assert any(m.get("status") == "failed" for m in metas)


async def test_set_model_updates_probe_model() -> None:
    from claudeloop.domain.control import SetModelCommand

    control = FakeRunControl(
        script=[
            [SetModelCommand(model="high")],
            [],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    probe = FakeCapacityProbe([available_signals()])
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert probe.models  # profile change synced to probe


async def test_a_wind_down_produces_every_artifact_the_marker_names() -> None:
    """The invariant a supervisor depends on: if handoff.json exists, so does
    everything it names. Order matters -- the marker is written last."""
    summaries: list[str] = []
    markers: list[HandoffMarker] = []
    runner, gateway, _a, _p, _s, _n, events = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        # Two turns of headroom with a reserve of two means the very first
        # completed turn is already inside the reserve.
        budget=Budget(max_turns=2, max_dollars=10.0),
    )
    runner._stop_summary_writer = lambda md: summaries.append(md) or "stop-summary.md"
    runner._handoff_marker_writer = markers.append
    runner._wind_down_policy = WindDownPolicy(enabled=True)

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert result.reason.startswith("wind-down:")
    assert gateway.closed is True
    assert summaries, "a wind-down must leave a stop summary"
    assert markers, "a wind-down must leave a handoff marker"

    marker = markers[0]
    assert marker.run_id == runner._run_id
    assert marker.stop_summary_path == "stop-summary.md"
    assert marker.turns_spent >= 1
    assert any(e[0] == "wind_down.finished" for e in events.events)


async def test_a_wind_down_is_not_reported_as_a_completed_run() -> None:
    """A supervisor has to tell "resume me elsewhere" from "this is done"."""
    markers: list[HandoffMarker] = []
    runner, _g, _a, _p, _s, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        budget=Budget(max_turns=2, max_dollars=10.0),
    )
    runner._handoff_marker_writer = markers.append
    runner._wind_down_policy = WindDownPolicy(enabled=True)

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert "wind-down" in result.reason


async def test_a_wind_down_without_a_marker_writer_still_finishes_cleanly() -> None:
    """No writer wired means no marker on disk -- which is the honest signal.
    A supervisor that finds no handoff.json falls back to the reactive path
    rather than resuming from artifacts that were never written."""
    runner, gateway, _a, _p, _s, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        budget=Budget(max_turns=2, max_dollars=10.0),
    )
    runner._wind_down_policy = WindDownPolicy(enabled=True)

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert "wind-down" in result.reason
    assert gateway.closed is True


async def test_a_wind_down_command_lets_the_turn_in_flight_finish() -> None:
    """That is the whole distinction from StopCommand, which ends the run at
    the next poll. The guarantee comes from where the decision is taken --
    decide_after_turn, i.e. after a turn completes -- so a request arriving
    mid-turn is held rather than dropped, and the handoff artifacts describe a
    consistent moment."""
    markers: list[HandoffMarker] = []
    runner, _g, _a, _p, _s, _n, events = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        run_control=FakeRunControl(script=[[WindDownCommand(reason="rotate")]]),
    )
    runner._handoff_marker_writer = markers.append

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert result.reason == "wind-down: operator:rotate"
    assert markers and markers[0].reason == "operator:rotate"
    assert any(e[0] == "control.wind_down" for e in events.events)


async def test_an_operator_wind_down_does_not_need_the_policy_enabled() -> None:
    """It is a decision, not a prediction: no headroom needs to be low, and the
    forecast does not have to be knowable."""
    markers: list[HandoffMarker] = []
    runner, _g, _a, _p, _s, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        run_control=FakeRunControl(script=[[WindDownCommand()]]),
    )
    runner._handoff_marker_writer = markers.append
    assert runner._wind_down_policy.enabled is False

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert "wind-down" in result.reason
    assert markers


async def test_a_wind_down_request_survives_a_poll_outside_a_natural_break() -> None:
    """Dropping it would make the command silently depend on poll timing."""
    markers: list[HandoffMarker] = []
    runner, _g, _a, _p, _s, _n, _e = make_runner(
        turns=[
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ],
        probes=[available_signals()],
        # Arrives on the very first poll, which is not a natural break.
        run_control=FakeRunControl(script=[[WindDownCommand(reason="early")], []]),
    )
    runner._handoff_marker_writer = markers.append

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert "wind-down" in result.reason
    assert markers and markers[0].reason == "operator:early"


async def test_stop_still_beats_a_wind_down_arriving_together() -> None:
    runner, gateway, _a, _p, _s, _n, _e = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        run_control=FakeRunControl(script=[[WindDownCommand(reason="rotate"), StopCommand()]]),
    )
    runner._stop_summary_writer = lambda md: "stop-summary.md"

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert "stopped" in result.reason
    assert "wind-down" not in result.reason
    assert gateway.closed is True


@pytest.mark.asyncio
async def test_wind_down_at_deadline_triggers_wind_down() -> None:
    """A run with --wind-down-at deadline triggers wind-down when the time arrives."""
    clock = FakeClock(start=NOW)
    deadline = clock.now() + timedelta(seconds=5)
    sleeper = FakeSleeper(clock)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
        ]
    )
    probe = FakeCapacityProbe([available_signals()])

    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=probe,
        clock=clock,
        sleeper=sleeper,
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=_DEFAULT_BUDGET,
        wait_policy=_DEFAULT_WAIT_POLICY,
        done_marker="TEST_DONE_MARKER",
        run_id="test-run",
        notifier=FakeNotifier(),
        run_control=FakeRunControl(),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        wind_down_at=deadline,
    )

    # Simulate time passing beyond the deadline
    clock.advance_to(deadline + timedelta(seconds=5))

    result = await runner.run(initial_prompt="start", continue_prompt="continue")

    assert "deadline" in result.reason.lower()


async def test_known_session_id_acquires_lock_before_first_turn() -> None:
    """Resume must lock the known session id before send_turn, not after."""
    clock = FakeClock(start=NOW)
    lock = FakeSessionLock()
    gateway = FakeAgentGateway(
        [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT, session_id="sess-a")]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=_DEFAULT_BUDGET,
        wait_policy=_DEFAULT_WAIT_POLICY,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=lock,
        save_points=FakeSavePointStore(),
        known_session_id="sess-a",
        run_id="test-run",
    )
    result = await runner.run(initial_prompt="resume", continue_prompt="continue")
    assert result.success is True
    assert runner._lock_token is None  # released on finish
    assert gateway.sent_prompts == ["resume"]
    # Lock was held during the run and released cleanly.
    assert "sess-a" not in lock.held
    # A subsequent acquire succeeds only if we released — proves we took it.
    assert lock.acquire("sess-a") is True
    lock.release("sess-a")


async def test_known_session_id_fails_closed_when_lock_held() -> None:
    """A second resume against a locked session must abort without sending a turn."""
    clock = FakeClock(start=NOW)
    lock = FakeSessionLock()
    assert lock.acquire("sess-busy") is True
    gateway = FakeAgentGateway(
        [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT, session_id="sess-busy")]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=_DEFAULT_BUDGET,
        wait_policy=_DEFAULT_WAIT_POLICY,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=lock,
        save_points=FakeSavePointStore(),
        known_session_id="sess-busy",
        run_id="test-run",
    )
    result = await runner.run(initial_prompt="resume", continue_prompt="continue")
    assert result.success is False
    assert "already locked" in result.reason
    assert gateway.sent_prompts == []
    assert gateway.closed is True


async def test_late_lock_contention_after_first_turn_fails_closed() -> None:
    """Fresh runs learn the session id from the first turn; if another runner
    already holds that lock, refuse further turns instead of fail-open."""
    clock = FakeClock(start=NOW)
    lock = FakeSessionLock()
    assert lock.acquire("sess-race") is True
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(
                signals=available_signals(),
                verdict=CONTINUE_VERDICT,
                session_id="sess-race",
            ),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=_DEFAULT_BUDGET,
        wait_policy=_DEFAULT_WAIT_POLICY,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=lock,
        save_points=FakeSavePointStore(),
        run_id="test-run",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="continue")
    assert result.success is False
    assert "already locked" in result.reason
    assert gateway.sent_prompts == ["start"]
    assert gateway.closed is True

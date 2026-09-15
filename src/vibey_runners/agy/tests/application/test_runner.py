# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Application runner tests — fakes only, no wall-clock sleeps, no SDK."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from agyloop.application.runner import AutonomousRunner
from agyloop.domain.budget import Budget
from agyloop.domain.completion import StructuredVerdict
from agyloop.domain.control import (
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    SetCwdCommand,
    StopCommand,
)
from agyloop.domain.forecast import WindDownPolicy
from agyloop.domain.handoff_marker import HandoffMarker
from agyloop.domain.waiting import WaitPolicyConfig, next_pacific_midnight
from agyloop.infrastructure.agent.catalog import RunRegistryCatalog
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
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
    auth_failed_signals,
    available_signals,
    credits_exhausted_signals,
    rpm_window_signals,
    unknown_window_signals,
    window_exhausted_signals,
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)
_DEFAULT_BUDGET = Budget()
_DEFAULT_WAIT_POLICY = WaitPolicyConfig()
_WALL_CLOCK_BUDGET = 0.5


def run[T](coro: Coroutine[Any, Any, T]) -> T:
    """Drive an async test body (pytest-asyncio also collects native async tests)."""
    return asyncio.run(coro)


def make_runner(
    *,
    turns: list[ScriptedTurn],
    probes: list,
    budget: Budget = _DEFAULT_BUDGET,
    wait_policy: WaitPolicyConfig = _DEFAULT_WAIT_POLICY,
    run_control: FakeRunControl | None = None,
    notifier: FakeNotifier | None = None,
    save_points: FakeSavePointStore | None = None,
    run_resources: Any | None = None,
    start: datetime = NOW,
    no_probe: bool = False,
    ramp: int = 0,
) -> tuple[
    AutonomousRunner,
    FakeAgentGateway,
    FakeAuditLog,
    FakeProgressReporter,
    FakeSleeper,
    FakeNotifier,
    FakeEventSink,
    FakeCapacityProbe,
]:
    clock = FakeClock(start=start)
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
        done_marker="AGYLOOP_TASK_FULLY_COMPLETE",
        run_id="test-run",
        notifier=notifier,
        run_control=run_control or FakeRunControl(),
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=save_points or FakeSavePointStore(),
        run_resources=run_resources,
        no_probe=no_probe,
        ramp=ramp,
    )
    return runner, gateway, audit, progress, sleeper, notifier, events, probe


def test_rpm_window_then_available_waits_then_resumes_without_wall_clock_sleep() -> None:
    """Script RPM WindowExhausted then Available — runner waits, then resumes.
    FakeSleeper jumps the clock; a simulated wait must not wall-clock sleep."""

    async def body() -> None:
        runner, gateway, _audit, _progress, sleeper, _n, _e, _p = make_runner(
            turns=[
                ScriptedTurn(signals=rpm_window_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[available_signals(), available_signals()],
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert gateway.sent_prompts == ["start", "keep going"]
        # Two real turns plus the capacity probe that spent the ledger.
        assert result.turns_spent == 3
        assert len(sleeper.wait_log) >= 1
        # RPM is a short window, not an RPD midnight sleep.
        assert all(instant - NOW < timedelta(minutes=2) for instant in sleeper.wait_log)
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_credits_exhausted_probe_cadence_notifies_and_resumes() -> None:
    """Five CreditsExhausted probes then Available — cadence, not sleep-to-reset."""

    async def body() -> None:
        notifier = FakeNotifier()
        cadence = timedelta(seconds=10)
        ceiling = timedelta(seconds=100)
        runner, gateway, _audit, progress, sleeper, notifier, _e, probe = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
            probes=[
                credits_exhausted_signals(),
                credits_exhausted_signals(),
                credits_exhausted_signals(),
                credits_exhausted_signals(),
                credits_exhausted_signals(),
                available_signals(),
            ],
            wait_policy=WaitPolicyConfig(
                credits_probe_interval=cadence,
                credits_probe_ceiling=ceiling,
                credits_backoff_factor=2.0,
            ),
            notifier=notifier,
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert gateway.sent_prompts == ["start"]
        # Preflight + 4 failed reprobes + 1 Available = 6 probe calls, resume on 6th.
        assert probe.calls == 6
        assert len(progress.waits) == 5
        untils = [until for _reason, until in progress.waits]
        intervals = [untils[0] - NOW] + [untils[i] - untils[i - 1] for i in range(1, len(untils))]
        assert intervals[0] == cadence
        assert all(gap <= ceiling for gap in intervals)
        # Cadence backs off; it is not a single sleep-to-reset deadline.
        assert intervals == [cadence, cadence * 2, cadence * 4, cadence * 8, ceiling]
        assert all(until - NOW < timedelta(hours=1) for until in untils)
        assert any("credits exhausted" in m.lower() for m in notifier.messages)
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_rpd_wait_uses_next_pacific_midnight_without_wall_clock_sleep() -> None:
    """RPD wait is Pacific midnight + grace, driven by FakeClock — not wall time."""

    async def body() -> None:
        near_midnight = datetime(2026, 8, 10, 6, 50, tzinfo=UTC)
        midnight = next_pacific_midnight(near_midnight)
        runner, gateway, _audit, _progress, sleeper, _n, _e, probe = make_runner(
            turns=[
                ScriptedTurn(signals=window_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[available_signals(), available_signals()],
            start=near_midnight,
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert gateway.sent_prompts == ["start", "keep going"]
        expected = midnight + timedelta(seconds=60)
        assert sleeper.wait_log
        assert sleeper.wait_log[-1] == expected
        assert probe.calls >= 2
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_no_probe_rpd_skips_probe_chat_and_waits_to_pacific_midnight() -> None:
    """--no-probe: zero probe() calls; sleep to the RPD midnight boundary, then a real turn."""

    async def body() -> None:
        near_midnight = datetime(2026, 8, 10, 6, 50, tzinfo=UTC)
        midnight = next_pacific_midnight(near_midnight)
        runner, gateway, _audit, _progress, sleeper, _n, _e, probe = make_runner(
            turns=[
                ScriptedTurn(signals=window_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[],
            start=near_midnight,
            no_probe=True,
            wait_policy=WaitPolicyConfig(no_probe=True),
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert probe.calls == 0
        assert gateway.sent_prompts == ["start", "keep going"]
        assert sleeper.wait_log[-1] == midnight + timedelta(seconds=60)
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_rpd_window_notifies_on_wait_entry() -> None:
    """§7: WindowExhausted rpd notifies on entry, same loud path as credits."""

    async def body() -> None:
        notifier = FakeNotifier()
        runner, gateway, _audit, _progress, _sleeper, notifier, _e, _p = make_runner(
            turns=[
                ScriptedTurn(signals=window_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[available_signals(), available_signals()],
            notifier=notifier,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert gateway.sent_prompts == ["start", "keep going"]
        assert any("rpd" in m.lower() and "window" in m.lower() for m in notifier.messages)

    run(body())


def test_unknown_window_notifies_on_wait_entry() -> None:
    """§7: WindowExhausted unknown notifies on entry."""

    async def body() -> None:
        notifier = FakeNotifier()
        runner, gateway, _audit, _progress, _sleeper, notifier, _e, _p = make_runner(
            turns=[
                ScriptedTurn(signals=unknown_window_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[available_signals(), available_signals()],
            notifier=notifier,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert gateway.sent_prompts == ["start", "keep going"]
        assert any("unknown" in m.lower() and "window" in m.lower() for m in notifier.messages)

    run(body())


def test_rpd_window_notifies_once_on_entry_not_every_probe() -> None:
    async def body() -> None:
        notifier = FakeNotifier()
        runner, _g, _audit, _progress, _sleeper, notifier, _e, probe = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
            probes=[
                window_exhausted_signals(),
                window_exhausted_signals(),
                available_signals(),
            ],
            notifier=notifier,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert probe.calls == 3
        assert len(notifier.messages) == 1

    run(body())


def test_no_probe_wait_policy_is_delay_then_send_not_probe_skip() -> None:
    """wait_policy.no_probe is the source of truth: sleep then real turn, never probe."""

    async def body() -> None:
        runner, gateway, _audit, _progress, sleeper, _n, events, probe = make_runner(
            turns=[
                ScriptedTurn(signals=window_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[],
            wait_policy=WaitPolicyConfig(no_probe=True),
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert probe.calls == 0
        assert not any(e[0] == "probe" for e in events.events)
        assert gateway.sent_prompts == ["start", "keep going"]
        assert len(sleeper.wait_log) >= 1

    run(body())


def test_no_probe_credits_waits_cadence_skips_probe_and_notifies() -> None:
    """--no-probe credits: cadence wait, real turn instead of probe chat, notify immediately."""

    async def body() -> None:
        notifier = FakeNotifier()
        cadence = timedelta(seconds=10)
        runner, gateway, _audit, progress, sleeper, notifier, _e, probe = make_runner(
            turns=[
                ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[],
            wait_policy=WaitPolicyConfig(
                no_probe=True,
                credits_probe_interval=cadence,
                credits_probe_ceiling=timedelta(seconds=100),
            ),
            notifier=notifier,
            no_probe=True,
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert probe.calls == 0
        assert gateway.sent_prompts == ["start", "keep going"]
        assert len(progress.waits) == 1
        assert progress.waits[0][1] - NOW == cadence
        assert sleeper.wait_log[-1] == NOW + cadence
        assert any("credits exhausted" in m.lower() for m in notifier.messages)
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_quota_rejection_outranks_done_on_the_same_turn() -> None:
    """Capacity outranks Done: a completion claim plus a quota rejection must wait."""

    async def body() -> None:
        runner, gateway, _audit, _progress, sleeper, _n, _e, _p = make_runner(
            turns=[
                ScriptedTurn(signals=rpm_window_signals(), verdict=DONE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[available_signals(), available_signals()],
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert len(sleeper.wait_log) >= 1
        assert gateway.sent_prompts == ["start", "keep going"]
        # Capacity outranked Done: a probe was spent before the real completion turn.
        assert result.turns_spent == 3

    run(body())


def test_preflight_available_then_done_in_one_turn() -> None:
    async def body() -> None:
        runner, gateway, _audit, progress, _sleeper, _n, _e, _p = make_runner(
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

    run(body())


def test_continue_verdict_sends_a_second_turn_with_continue_prompt() -> None:
    async def body() -> None:
        runner, gateway, _audit, _progress, _sleeper, _n, _e, _p = make_runner(
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

    run(body())


def test_authentication_failure_is_terminal_and_never_retried() -> None:
    async def body() -> None:
        runner, gateway, _audit, progress, sleeper, _n, _e, _p = make_runner(
            turns=[],
            probes=[auth_failed_signals()],
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is False
        assert result.reason == "authentication failed"
        assert sleeper.wait_log == []
        assert gateway.sent_prompts == []
        assert progress.finishes == [(False, "authentication failed")]

    run(body())


def test_preflight_persist_preserves_resumed_conversation_id(tmp_path: Path) -> None:
    """Resume preflight persist must not erase a known conversation_id with None."""

    async def body() -> None:
        directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
        original = "conv-existing"
        directory.update_meta(conversation_id=original)
        clock = FakeClock(start=NOW)
        runner = AutonomousRunner(
            agent_gateway=FakeAgentGateway([]),
            capacity_probe=FakeCapacityProbe([credits_exhausted_signals()]),
            clock=clock,
            sleeper=FakeSleeper(clock),
            audit_log=FakeAuditLog(),
            progress=FakeProgressReporter(),
            wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
            run_id=directory.read_meta().run_id,
            event_sink=FakeEventSink(),
            state_store=FakeStateStore(),
            session_lock=FakeSessionLock(),
            save_points=FakeSavePointStore(),
            meta_updater=directory.update_meta,
            run_control=FakeRunControl(script=[[StopCommand()]]),
        )
        result = await runner.run(initial_prompt="resume", continue_prompt="keep going")
        assert result.success is False
        assert directory.read_meta().conversation_id == original
        ref = RunRegistryCatalog().most_recent(str(tmp_path))
        assert ref is not None
        assert ref.session_id == original

    run(body())


def test_budget_exhaustion_stops_the_run_cleanly() -> None:
    async def body() -> None:
        runner, _gateway, _audit, _progress, _sleeper, _n, _e, _p = make_runner(
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

    run(body())


def test_blocked_verdict_fails_with_the_stated_reason() -> None:
    from agyloop.domain.completion import StructuredVerdict

    async def body() -> None:
        blocked = StructuredVerdict(complete=False, blocked_on="missing MCP credentials")
        runner, _gateway, _audit, _progress, _sleeper, _n, _e, _p = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=blocked)],
            probes=[available_signals()],
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is False
        assert result.reason == "missing MCP credentials"

    run(body())


def test_audit_log_records_every_phase_transition() -> None:
    async def body() -> None:
        runner, _gateway, audit, _progress, _sleeper, _n, _e, _p = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
            probes=[available_signals()],
        )
        await runner.run(initial_prompt="start", continue_prompt="keep going")
        event_types = [e[0] for e in audit.events]
        assert event_types == ["preflight", "turn", "finished"]

    run(body())


def test_null_ports_when_optionals_omitted() -> None:
    async def body() -> None:
        clock = FakeClock(start=NOW)
        gateway = FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)]
        )
        runner = AutonomousRunner(
            agent_gateway=gateway,
            capacity_probe=FakeCapacityProbe([available_signals()]),
            clock=clock,
            sleeper=FakeSleeper(clock),
            audit_log=FakeAuditLog(),
            progress=FakeProgressReporter(),
        )
        result = await runner.run(initial_prompt="x", continue_prompt="y")
        assert result.success is True

    run(body())


def test_stop_command_ends_run_and_closes_gateway() -> None:
    async def body() -> None:
        control = FakeRunControl(script=[[StopCommand()]])
        summaries: list[str] = []
        runner, gateway, _a, _p, _s, _n, events, _probe = make_runner(
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

    run(body())


def test_stop_outranks_mixed_mutate_batch() -> None:
    """A poll batch with Stop plus cwd/resource mutates must stop without mutating."""

    class TrackingResources:
        def __init__(self) -> None:
            self.mutates: list[tuple[str, str, str]] = []
            self.cwds: list[str] = []

        def apply_mutate(
            self, *, action: str, kind: str, value: str, name: str | None = None
        ) -> dict[str, object]:
            del name
            self.mutates.append((action, kind, value))
            return {"ok": True}

        def gateway_payload(self) -> dict[str, object]:
            return {}

        def set_permission_mode(self, mode: str) -> None:
            del mode

        def set_cwd(self, path: str) -> None:
            self.cwds.append(path)

    async def body() -> None:
        resources = TrackingResources()
        control = FakeRunControl(
            script=[
                [
                    SetCwdCommand(path="/should-not-apply"),
                    ResourceMutateCommand(action="add", kind="skill", value="nope"),
                    StopCommand(),
                ]
            ]
        )
        runner, gateway, _a, _p, _s, _n, events, _probe = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
            probes=[available_signals()],
            run_control=control,
            run_resources=resources,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is False
        assert "stopped" in result.reason
        assert resources.mutates == []
        assert resources.cwds == []
        assert gateway.cwds == []
        assert gateway.sent_prompts == []
        assert any(e[0] == "control.stop" for e in events.events)

    run(body())


def test_prompt_now_replaces_continue_prompt() -> None:
    async def body() -> None:
        control = FakeRunControl(
            script=[
                [],
                [PromptNowCommand(text="injected now")],
            ]
        )
        runner, gateway, _a, _p, _s, _n, _e, _probe = make_runner(
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

    run(body())


def test_prompt_deferred_applies_at_natural_break() -> None:
    async def body() -> None:
        control = FakeRunControl(
            script=[
                [PromptDeferredCommand(text="later please")],
                [],
            ]
        )
        runner, gateway, _a, _p, _s, _n, _e, _probe = make_runner(
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

    run(body())


def test_sticky_credits_survives_available_probe() -> None:
    async def body() -> None:
        runner, gateway, _a, _p, sleeper, _n, events, _probe = make_runner(
            turns=[
                ScriptedTurn(signals=credits_exhausted_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[
                available_signals(),
                available_signals(),
            ],
            wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert any(e[0] == "capacity.probe_available" for e in events.events)
        assert len(sleeper.wait_log) >= 1
        assert gateway.sent_prompts == ["start", "keep going"]

    run(body())


def test_run_exception_marks_meta_failed() -> None:
    class BoomGateway(FakeAgentGateway):
        async def send_turn(self, prompt_text: str):  # type: ignore[override]
            del prompt_text
            raise RuntimeError("boom")

    async def body() -> None:
        metas: list[dict[str, object]] = []
        clock = FakeClock(start=NOW)
        gateway = BoomGateway([])
        events = FakeEventSink()
        runner = AutonomousRunner(
            agent_gateway=gateway,
            capacity_probe=FakeCapacityProbe([available_signals()]),
            clock=clock,
            sleeper=FakeSleeper(clock),
            audit_log=FakeAuditLog(),
            progress=FakeProgressReporter(),
            run_id="boom-run",
            event_sink=events,
            state_store=FakeStateStore(),
            session_lock=FakeSessionLock(),
            save_points=FakeSavePointStore(),
            meta_updater=lambda **kw: metas.append(kw),
        )
        with pytest.raises(RuntimeError, match="boom"):
            await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert any(m.get("status") == "failed" for m in metas)
        assert any(e[0] == "run.exception" for e in events.events)
        event = next(e for e in events.events if e[0] == "run.exception")
        assert event[1] is not None
        assert event[1]["error"] == "RuntimeError"
        assert "boom" in str(event[1]["detail"])

    run(body())


WAIT_ONLY_CONTINUE = StructuredVerdict(complete=False, remaining_work=("Waiting for E2E suite",))


def test_wait_only_continue_triggers_progress_wait() -> None:
    async def body() -> None:
        runner, gateway, _a, _p, sleeper, _n, events, _probe = make_runner(
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
        assert len(sleeper.wait_log) >= 1
        assert gateway.sent_prompts == ["start", "keep going"]

    run(body())


def test_first_savepoint_with_commit_skips_progress_wait() -> None:
    async def body() -> None:
        runner, gateway, _a, _p, _sleeper, _n, events, _probe = make_runner(
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

    run(body())


def test_stop_during_wait_interrupts_sleep() -> None:
    async def body() -> None:
        control = FakeRunControl(
            script=[
                [],
                [],
                [],
                [StopCommand()],
            ]
        )
        runner, gateway, _a, _p, sleeper, _n, _e, _probe = make_runner(
            turns=[
                ScriptedTurn(
                    signals=rpm_window_signals(),
                    verdict=CONTINUE_VERDICT,
                ),
            ],
            probes=[available_signals()],
            run_control=control,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is False
        assert "stopped" in result.reason
        assert gateway.closed is True
        assert len(sleeper.wait_log) >= 1

    run(body())


def test_stop_during_progress_wait() -> None:
    async def body() -> None:
        control = FakeRunControl(
            script=[
                [],
                [],
                [],
                [StopCommand()],
            ]
        )
        runner, gateway, _a, _p, sleeper, _n, _e, _probe = make_runner(
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

    run(body())


def test_empty_zero_cost_turns_increment_streak_then_block() -> None:
    async def body() -> None:
        runner, gateway, _a, _p, _s, _n, _e, _probe = make_runner(
            turns=[
                ScriptedTurn(
                    signals=available_signals(), verdict=None, output_text="", cost_usd=0.0
                ),
                ScriptedTurn(
                    signals=available_signals(), verdict=None, output_text="", cost_usd=0.0
                ),
                ScriptedTurn(
                    signals=available_signals(), verdict=None, output_text="", cost_usd=0.0
                ),
            ],
            probes=[available_signals()],
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is False
        assert result.reason == "repeated empty model responses"
        assert len(gateway.sent_prompts) == 3

    run(body())


def test_probe_auth_failure_clears_waiting_without_forcing_active() -> None:
    async def body() -> None:
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
                    auth_failed_signals(),
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
        finish_clears = [
            m for m in metas if set(m.keys()) == {"waiting_until"} and m["waiting_until"] is None
        ]
        assert finish_clears
        assert any(m.get("status") == "failed" for m in metas)

    run(body())


def test_ramp_paces_first_n_turns_without_wall_clock_sleep() -> None:
    """--ramp N sleeps 1s before each of the first N turns via FakeSleeper."""

    async def body() -> None:
        runner, gateway, _audit, _progress, sleeper, _n, events, _p = make_runner(
            turns=[
                ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ],
            probes=[],
            no_probe=True,
            wait_policy=WaitPolicyConfig(no_probe=True),
            ramp=2,
        )
        started = time.monotonic()
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        elapsed = time.monotonic() - started
        assert result.success is True
        assert gateway.sent_prompts == ["start", "keep going", "keep going"]
        assert sleeper.wait_log[:2] == [
            NOW + timedelta(seconds=1),
            NOW + timedelta(seconds=2),
        ]
        assert NOW + timedelta(seconds=3) not in sleeper.wait_log
        assert any(item[0] == "ramp.wait" for item in events.events)
        assert elapsed < _WALL_CLOCK_BUDGET

    run(body())


def test_ramp_zero_does_not_insert_pacing_sleeps() -> None:
    async def body() -> None:
        runner, _gateway, _audit, _progress, sleeper, _n, events, _p = make_runner(
            turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
            probes=[],
            no_probe=True,
            wait_policy=WaitPolicyConfig(no_probe=True),
            ramp=0,
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        assert sleeper.wait_log == []
        assert all(item[0] != "ramp.wait" for item in events.events)

    run(body())


def test_turn_completed_cost_usd_matches_ledger_estimate() -> None:
    async def body() -> None:
        runner, _gateway, audit, _progress, _sleeper, _n, events, _p = make_runner(
            turns=[
                ScriptedTurn(
                    signals=available_signals(),
                    verdict=DONE_VERDICT,
                    cost_usd=0.0,
                    prompt_tokens=1_000_000,
                    completion_tokens=0,
                )
            ],
            probes=[],
            no_probe=True,
            wait_policy=WaitPolicyConfig(no_probe=True),
        )
        result = await runner.run(initial_prompt="start", continue_prompt="keep going")
        assert result.success is True
        completed = [payload for kind, payload in events.events if kind == "turn.completed"]
        assert completed
        payload = completed[0]
        assert payload is not None
        assert payload["cost_usd"] == pytest.approx(0.10)
        assert payload["prompt_tokens"] == 1_000_000
        assert payload["completion_tokens"] == 0
        turn_audit = [item for item in audit.events if item[0] == "turn"]
        assert turn_audit
        assert turn_audit[0][1]["cost_usd"] == pytest.approx(0.10)

    run(body())


async def test_a_wind_down_finishes_with_a_marker_rather_than_success() -> None:
    """A supervisor has to tell "resume me elsewhere" from "this is done"."""
    markers: list[HandoffMarker] = []
    runner, gateway, _a, _p, _s, _n, _e, _pr = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        # One turn of headroom against a reserve of two: the first completed
        # turn is already inside the reserve.
        budget=Budget(max_turns=2, max_dollars=10.0),
    )
    runner._handoff_marker_writer = markers.append
    runner._wind_down_policy = WindDownPolicy(enabled=True)

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert result.reason.startswith("wind-down:")
    assert gateway.closed is True
    assert markers, "a wind-down must leave a handoff marker"
    assert markers[0].reason == "turn_reserve"


async def test_a_wind_down_without_a_writer_still_finishes_cleanly() -> None:
    """No writer means no marker, which is the honest signal: a supervisor that
    finds no handoff.json falls back to the reactive path."""
    runner, _g, _a, _p, _s, _n, _e, _pr = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)],
        probes=[available_signals()],
        budget=Budget(max_turns=2, max_dollars=10.0),
    )
    runner._wind_down_policy = WindDownPolicy(enabled=True)

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is False
    assert "wind-down" in result.reason


async def test_the_policy_off_leaves_the_run_untouched() -> None:
    """The predictive path is strictly additive."""
    runner, _g, _a, _p, _s, _n, _e, _pr = make_runner(
        turns=[ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)],
        probes=[available_signals()],
        budget=Budget(max_turns=2, max_dollars=10.0),
    )

    result = await runner.run(initial_prompt="start", continue_prompt="keep going")

    assert result.success is True

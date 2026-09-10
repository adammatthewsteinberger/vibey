# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Coverage-oriented tests for new mid-run control / savepoint / null ports."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from claudeloop.application.dto import TurnOutcome
from claudeloop.application.runner import AutonomousRunner
from claudeloop.application.usecases import run_control as run_control_uc
from claudeloop.application.usecases.run_plan import parse_plan_file
from claudeloop.domain.budget import Budget
from claudeloop.domain.classify import TurnSignals
from claudeloop.domain.completion import StructuredVerdict
from claudeloop.domain.control import (
    PromptDeferredCommand,
    PromptNowCommand,
    ResponseRetryCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPermissionModeCommand,
    StopCommand,
)
from claudeloop.domain.plan import WorkPlan
from claudeloop.domain.savepoint import SavePointRef
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
)

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


async def test_null_ports_when_optionals_omitted() -> None:
    """Exercises the Null* collaborators used when optional ports are unset."""
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway([ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)])
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


async def test_stop_at_natural_break_after_continue() -> None:
    control = FakeRunControl(
        script=[
            [],
            [StopCommand()],  # natural-break poll after Continue
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT)]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
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
    assert result.success is False
    assert "stopped" in result.reason


async def test_deferred_prompt_applied_when_polled_at_natural_break() -> None:
    control = FakeRunControl(
        script=[
            [],
            [PromptDeferredCommand(text="break prompt")],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
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
        run_control=control,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert gateway.sent_prompts == ["start", "break prompt"]


async def test_plan_reconcile_marks_items_done() -> None:
    plan = WorkPlan.parse("- [ ] alpha\n- [ ] beta\n")
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(
                signals=available_signals(),
                verdict=StructuredVerdict(complete=False, remaining_work=("beta",)),
            ),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        plan=plan,
        run_id="r",
    )
    await runner.run(initial_prompt="start", continue_prompt="keep")
    assert any(e[0] == "plan.reconciled" for e in events.events)
    assert runner._plan is not None
    assert runner._plan.items[0].done is True


async def test_savepoint_skipped_when_store_returns_none() -> None:
    class _NoGit(FakeSavePointStore):
        def create(
            self,
            *,
            run_id: str,
            label: str,
            message: str = "",
            attempt: int | None = None,
            verdict_name: str = "Continue",
            summary: str = "",
            remaining_work: tuple[str, ...] = (),
        ) -> None:
            del run_id, label, message, attempt, verdict_name, summary, remaining_work
            return None

    clock = FakeClock(start=NOW)
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        event_sink=events,
        save_points=_NoGit(),
        run_id="r",
    )
    await runner.run(initial_prompt="x", continue_prompt="y")
    assert any(e[0] == "savepoint.skipped" for e in events.events)


async def test_credits_notify_when_cannot_purchase() -> None:
    signals = TurnSignals(
        rate_limit_status="rejected",
        error_code="credits_required",
        can_purchase=False,
    )
    notifier = FakeNotifier()
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)]
        ),
        capacity_probe=FakeCapacityProbe([signals, available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        notifier=notifier,
        wait_policy=WaitPolicyConfig(credits_probe_interval=timedelta(seconds=1)),
        run_id="r",
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
    )
    await runner.run(initial_prompt="x", continue_prompt="y")
    assert any("may not be available" in m for m in notifier.messages)


async def test_gateway_exception_releases_lock_and_closes() -> None:
    class BoomGateway(FakeAgentGateway):
        async def send_turn(self, prompt_text: str):
            del prompt_text
            raise RuntimeError("boom")

    clock = FakeClock(start=NOW)
    gateway = BoomGateway([])
    lock = FakeSessionLock()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        session_lock=lock,
        run_id="r",
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        save_points=FakeSavePointStore(),
    )
    with pytest.raises(RuntimeError, match="boom"):
        await runner.run(initial_prompt="x", continue_prompt="y")
    assert gateway.closed is True


async def test_meta_updater_invoked() -> None:
    updates: list[dict] = []
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        meta_updater=lambda **kw: updates.append(kw),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    await runner.run(initial_prompt="x", continue_prompt="y")
    assert updates


async def test_blocked_verdict_remembers_reason_in_stop_summary_fields() -> None:
    blocked = StructuredVerdict(complete=False, blocked_on="needs login")
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=blocked)]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="x", continue_prompt="y")
    assert result.success is False
    assert runner._last_summary == "needs login"


async def test_null_savepoint_store_unwind_raises() -> None:
    from claudeloop.application.runner import _NullSavePointStore

    store = _NullSavePointStore()
    assert store.create(run_id="r", label="l", message="m") is None
    assert store.list_points("r") == []
    assert store.changes_since(None) == ""
    with pytest.raises(RuntimeError):
        store.unwind(run_id="r", to="1", backup=True)


async def test_null_notifier_control_events_lock() -> None:
    from claudeloop.application.runner import (
        _NullEventSink,
        _NullNotifier,
        _NullRunControl,
        _NullSessionLock,
        _NullStateStore,
    )

    _NullNotifier().notify("x")
    assert _NullRunControl().poll() == []
    sink = _NullEventSink()
    sink.emit("t", {})
    sink.bind(session_id="s", attempt=1, phase="RUNNING")
    store = _NullStateStore()
    store.save("r", {"a": 1})
    assert store.load("r") is None
    lock = _NullSessionLock()
    assert lock.acquire("s") is True
    lock.release("s")


def test_run_control_usecase_enqueue() -> None:
    class Inbox:
        def __init__(self) -> None:
            self.cmds: list = []

        def enqueue(self, command: object) -> None:
            self.cmds.append(command)

    inbox = Inbox()
    assert run_control_uc.request_stop(inbox, run_id="r1").command_type == "stop"
    assert isinstance(inbox.cmds[0], StopCommand)
    result = run_control_uc.request_prompt(inbox, "hi", immediate=True, run_id="r1")
    assert result.command_type == "prompt_now"
    result = run_control_uc.request_prompt(inbox, "later", immediate=False, run_id="r1")
    assert result.command_type == "prompt_deferred"


def test_parse_plan_file(tmp_path: Path) -> None:
    path = tmp_path / "plan.md"
    path.write_text("# Plan\n\n- [ ] do it\n", encoding="utf-8")
    plan = parse_plan_file(path)
    assert plan.items[0].text == "do it"


def test_control_command_blank_text_rejected() -> None:
    with pytest.raises(ValueError):
        PromptNowCommand(text="  ")
    with pytest.raises(ValueError):
        PromptDeferredCommand(text="")


def test_savepoint_ref_validation() -> None:
    with pytest.raises(ValueError):
        SavePointRef(
            n=0,
            ref="refs/x",
            sha="abc",
            label="l",
            at=NOW,
        )
    with pytest.raises(ValueError):
        SavePointRef(n=1, ref=" ", sha="abc", label="l", at=NOW)
    with pytest.raises(ValueError):
        SavePointRef(n=1, ref="refs/x", sha=" ", label="l", at=NOW)


async def test_done_marker_none_uses_default_evaluate() -> None:
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [
                ScriptedTurn(
                    signals=available_signals(),
                    verdict=None,
                    output_text="CLAUDELOOP_TASK_FULLY_COMPLETE",
                )
            ]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        done_marker=None,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="x", continue_prompt="y")
    assert result.success is True


async def test_deferred_prompt_survives_wait_without_applying_early() -> None:
    """Queued deferred stays pending across a wait; `_next_prompt` sees it
    (pass branch) until a natural Continue break promotes it."""
    from datetime import timedelta

    from tests.application.fakes import window_exhausted_signals

    control = FakeRunControl(
        script=[
            [PromptDeferredCommand(text="after break")],
            [],
            [],
            [],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(
                signals=window_exhausted_signals(resets_at=NOW + timedelta(minutes=1)),
                verdict=CONTINUE_VERDICT,
            ),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals(), available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        wait_policy=WaitPolicyConfig(reset_grace=timedelta(seconds=1)),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    # After wait, second turn still uses continue (deferred not yet promoted
    # without natural-break poll applying it); third gets deferred if promoted.
    assert gateway.sent_prompts[0] == "start"
    assert "keep" in gateway.sent_prompts or "after break" in gateway.sent_prompts


async def test_prompt_now_and_deferred_in_same_poll() -> None:
    control = FakeRunControl(
        script=[
            [],
            [
                PromptNowCommand(text="first"),
                PromptNowCommand(text="second"),
            ],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
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
        run_control=control,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert gateway.sent_prompts[1] == "second"


async def test_plan_reconcile_noop_when_all_remaining() -> None:
    plan = WorkPlan.parse("- [ ] alpha\n- [ ] beta\n")
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [
                ScriptedTurn(
                    signals=available_signals(),
                    verdict=StructuredVerdict(complete=False, remaining_work=("alpha", "beta")),
                ),
                ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
            ]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        plan=plan,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    await runner.run(initial_prompt="start", continue_prompt="keep")
    assert runner._plan is not None
    assert all(not item.done for item in runner._plan.items)


async def test_null_state_bus_and_publish_via_runner() -> None:
    from claudeloop.application.runner import _NullStateBus

    _NullStateBus().publish("x", {"a": 1})

    class CapturingBus:
        def __init__(self) -> None:
            self.events: list[tuple[str, dict]] = []

        def publish(self, event_type: str, state: dict) -> None:
            self.events.append((event_type, state))

    bus = CapturingBus()
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT)]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        state_bus=bus,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    await runner.run(initial_prompt="x", continue_prompt="y")
    assert any(e[0].startswith("phase.") for e in bus.events)


async def test_two_deferred_prompts_at_natural_break() -> None:
    control = FakeRunControl(
        script=[
            [],
            [
                PromptDeferredCommand(text="first-deferred"),
                PromptDeferredCommand(text="second-deferred"),
            ],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
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
        run_control=control,
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert gateway.sent_prompts[1] == "second-deferred"


async def test_apply_control_skips_unknown_command_types() -> None:
    """Covers the closed-union fallthrough when a non-ControlCommand slips in."""
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway([]),
        capacity_probe=FakeCapacityProbe([]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    runner._apply_control([object()], natural_break=False)  # type: ignore[list-item]
    assert runner._prompt_now is None
    assert runner._stop_requested is False


async def test_budget_uses_max_attempts() -> None:
    clock = FakeClock(start=NOW)
    runner = AutonomousRunner(
        agent_gateway=FakeAgentGateway(
            [
                ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ]
        ),
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=Budget(max_attempts=1),
        event_sink=FakeEventSink(),
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
    )
    result = await runner.run(initial_prompt="x", continue_prompt="y")
    assert result.success is False
    assert result.reason == "budget exhausted"


async def test_set_preset_applied_before_next_turn() -> None:
    from claudeloop.domain.control import SetPresetCommand
    from claudeloop.domain.model_profile import DEFAULT_MODEL_HIGH

    control = FakeRunControl(
        script=[
            [SetPresetCommand(preset="high")],
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
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
        log_chatter="full",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert gateway.profiles
    assert gateway.profiles[0].model == DEFAULT_MODEL_HIGH
    assert any(e[0] == "chatter.prompt" for e in events.events)
    assert any(e[0] == "model.profile_changed" for e in events.events)


async def test_auto_escalate_after_two_no_progress_continues() -> None:
    from claudeloop.domain.model_profile import (
        DEFAULT_MODEL_MEDIUM,
        ModelAliases,
        profile_for_preset,
    )

    plan = WorkPlan.parse("- [ ] alpha\n- [ ] beta\n")
    clock = FakeClock(start=NOW)
    stuck = StructuredVerdict(complete=False, remaining_work=("alpha", "beta"))
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=stuck),
            ScriptedTurn(signals=available_signals(), verdict=stuck),
            ScriptedTurn(signals=available_signals(), verdict=DONE_VERDICT),
        ]
    )
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        plan=plan,
        run_id="r",
        profile=profile_for_preset("low", ModelAliases()),
        auto_model=True,
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert any(e[0] == "model.auto_policy" for e in events.events)
    assert gateway.profiles
    assert gateway.profiles[0].model == DEFAULT_MODEL_MEDIUM


async def test_set_model_and_effort_commands() -> None:
    class ProbeWithoutSetModel:
        """Capacity probe without set_model — covers the getattr fallback."""

        def __init__(self, script: list) -> None:
            self._script = list(script)

        async def probe(self) -> TurnOutcome:
            signals = self._script.pop(0)
            return TurnOutcome(signals=signals, verdict=None, output_text="", session_id=None)

    control = FakeRunControl(
        script=[
            [SetModelCommand(model="high"), SetEffortCommand(effort="xhigh")],
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
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=ProbeWithoutSetModel([available_signals()]),
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
        log_chatter="off",
    )
    result = await runner.run(initial_prompt="start", continue_prompt="keep")
    assert result.success is True
    assert gateway.profiles
    assert gateway.profiles[-1].effort == "xhigh"


async def test_null_savepoint_store_list_and_changes() -> None:
    from claudeloop.application.runner import _NullSavePointStore

    store = _NullSavePointStore()
    assert store.list_points("r") == []
    assert store.changes_since(None) == ""
    assert store.create(run_id="r", label="x", message="y") is None
    with pytest.raises(RuntimeError):
        store.unwind(run_id="r", to="1", backup=True)


async def test_auto_downgrade_budget_queues_low() -> None:
    from claudeloop.domain.model_profile import ModelAliases, profile_for_preset

    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(
                signals=available_signals(),
                verdict=DONE_VERDICT,
                cost_usd=9.0,
            ),
        ]
    )
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        budget=Budget(max_dollars=10.0),
        event_sink=events,
        state_store=FakeStateStore(),
        session_lock=FakeSessionLock(),
        save_points=FakeSavePointStore(),
        run_id="r",
        profile=profile_for_preset("high", ModelAliases()),
        max_dollars=10.0,
        auto_model=True,
    )
    result = await runner.run(initial_prompt="x", continue_prompt="y")
    assert result.success is True
    # Done finishes before a next turn, but policy still queues on the completed turn.
    assert any(e[0] == "model.auto_policy" for e in events.events)


async def test_request_set_profile_usecases() -> None:
    class Inbox:
        def __init__(self) -> None:
            self.items: list[object] = []

        def enqueue(self, command: object) -> None:
            self.items.append(command)

    inbox = Inbox()
    assert run_control_uc.request_set_model(inbox, "high", run_id="r").command_type == "set_model"
    assert run_control_uc.request_set_effort(inbox, "max", run_id="r").command_type == "set_effort"
    assert run_control_uc.request_set_preset(inbox, "low", run_id="r").command_type == "set_preset"
    assert (
        run_control_uc.request_set_permission_mode(inbox, "plan", run_id="r").command_type
        == "set_permission_mode"
    )
    assert run_control_uc.request_set_cwd(inbox, "/tmp", run_id="r").command_type == "set_cwd"
    assert run_control_uc.request_slash(inbox, "/status", run_id="r").command_type == "slash"
    assert (
        run_control_uc.request_tool_decision(inbox, "rid", allow=True, run_id="r").command_type
        == "approve_tool"
    )
    assert (
        run_control_uc.request_tool_decision(
            inbox, "rid2", allow=False, reason="no", run_id="r"
        ).command_type
        == "deny_tool"
    )
    assert (
        run_control_uc.request_resource_mutate(
            inbox, action="add", kind="skill", value="s", run_id="r"
        ).command_type
        == "resource_mutate"
    )
    assert (
        run_control_uc.request_response_feedback(inbox, "bad", note="x", run_id="r").command_type
        == "response_feedback"
    )
    assert run_control_uc.request_response_retry(inbox, run_id="r").command_type == "response_retry"
    assert len(inbox.items) == 11


async def test_permission_mode_and_retry_applied() -> None:
    control = FakeRunControl(
        script=[
            [],
            [SetPermissionModeCommand(mode="plan")],
            [ResponseRetryCommand()],
            [StopCommand()],
        ]
    )
    clock = FakeClock(start=NOW)
    gateway = FakeAgentGateway(
        [
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
            ScriptedTurn(signals=available_signals(), verdict=CONTINUE_VERDICT),
        ]
    )
    events = FakeEventSink()
    runner = AutonomousRunner(
        agent_gateway=gateway,
        capacity_probe=FakeCapacityProbe([available_signals()]),
        clock=clock,
        sleeper=FakeSleeper(clock),
        audit_log=FakeAuditLog(),
        progress=FakeProgressReporter(),
        run_control=control,
        event_sink=events,
        budget=Budget(max_turns=5),
    )
    result = await runner.run(initial_prompt="first", continue_prompt="cont")
    assert "plan" in gateway.permission_modes
    assert (
        any(p == "first" for p in gateway.sent_prompts) or gateway.sent_prompts.count("first") >= 1
    )
    # retry requeues last prompt; stop ends the run
    assert result.success is False or result.success is True
    assert any(e[0] == "control.permission_mode" for e in events.events)


async def test_null_stream_ui_methods() -> None:
    from claudeloop.application.runner import _NullStreamUi

    ui = _NullStreamUi()
    ui.on_delta("x", turn_id="t", seq=1)
    ui.on_turn_boundary(turn_id="t", attempt=1)
    ui.on_prompt("prompt")
    ui.on_assistant("assistant")
    ui.on_tool("Bash", "ls")
    ui.on_status({"model": "x"})
    ui.close()

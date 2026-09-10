# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
import pytest

from cursorloop.application import runner as runner_mod
from cursorloop.application.usecases.run_plan import run_from_plan_file
from cursorloop.domain.autonomy import autonomy_preamble
from cursorloop.domain.budget import Budget
from cursorloop.domain.capacity import AuthenticationFailed, Available, CreditsExhausted
from cursorloop.domain.control import Prompt, Stop, WindDown
from cursorloop.domain.faults import Busy, ConfigFault, TransientFault
from cursorloop.domain.forecast import WindDownPolicy
from cursorloop.domain.handoff_marker import HandoffMarker
from cursorloop.domain.plan import WorkPlan
from tests.application import fakes


def test_runner_resumes_on_the_probe_that_finds_a_credit_top_up() -> None:
    """The scenario the whole project exists for: five probes still exhausted,
    the sixth finds capacity, and the run resumes THERE — not at some invented
    deadline, because CreditsExhausted has no deadline to invent."""
    probe = fakes.FakeCapacityProbe(
        [fakes.signals_for(Available())]
        + [fakes.signals_for(CreditsExhausted())] * 5
        + [fakes.signals_for(Available())]
    )
    gateway = fakes.FakeAgentGateway(
        [fakes.turn(capacity=CreditsExhausted()), fakes.turn(done=True, summary="finished")]
    )
    clock, sleeper = fakes.FakeClock(), None
    sleeper = fakes.FakeSleeper(clock)
    runner = fakes.build_runner(gateway=gateway, probe=probe, clock=clock, sleeper=sleeper)

    result = anyio.run(runner.run, "do the work")

    assert result.success is True
    assert probe.calls == 7  # preflight Available + 5 exhausted + restoration
    assert sleeper.real_sleep_calls == 0  # a multi-hour wait, zero wall-clock seconds


def test_notifier_fires_on_entry_to_credits_exhaustion() -> None:
    """A human has to act, so a human has to be told — immediately, not after
    the run eventually gives up."""
    notifier = fakes.FakeNotifier()
    audit = fakes.FakeAuditLog()
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway(
            [fakes.turn(capacity=CreditsExhausted()), fakes.turn(done=True, summary="finished")]
        ),
        probe=fakes.FakeCapacityProbe(
            [
                fakes.signals_for(Available()),
                fakes.signals_for(CreditsExhausted()),
                fakes.signals_for(Available()),
            ]
        ),
        notifier=notifier,
        audit=audit,
    )
    anyio.run(runner.run, "do the work")
    assert any("credit" in message.lower() for message in notifier.messages)
    assert notifier.messages.count(notifier.messages[0]) == 1 or len(notifier.messages) == 1
    assert any(event == "entered_credits_exhausted" for event, _ in audit.events)


def test_busy_error_cancels_the_active_run_then_re_sends_with_force() -> None:
    gateway = fakes.FakeAgentGateway([fakes.busy_turn(), fakes.turn(done=True)])
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert gateway.cancel_calls == 1
    assert gateway.force_flags == [False, True]


def test_transient_fault_retries_then_gives_up_at_the_cap() -> None:
    gateway = fakes.FakeAgentGateway([fakes.transient_turn()] * 10)
    runner = fakes.build_runner(gateway=gateway, max_transient_retries=3)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert gateway.send_calls == 4  # initial + 3 retries


def test_hooks_are_restored_even_when_the_run_fails() -> None:
    hooks = fakes.FakeHookManager()
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway([fakes.blocked_turn("needs prod creds")]), hooks=hooks
    )
    anyio.run(runner.run, "do the work")
    assert hooks.installed_then_restored is True


def test_config_fault_is_terminal_without_retrying() -> None:
    gateway = fakes.FakeAgentGateway([fakes.config_fault_turn("unknown model 'nope'")])
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert "unknown model" in result.reason
    assert gateway.send_calls == 1


def test_preflight_authentication_failure_never_sends_a_turn() -> None:
    gateway = fakes.FakeAgentGateway([])
    probe = fakes.FakeCapacityProbe([fakes.signals_for(AuthenticationFailed("bad key"))])
    runner = fakes.build_runner(gateway=gateway, probe=probe)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert result.reason == "authentication failed"
    assert gateway.send_calls == 0


def test_capacity_restoration_audit_names_the_probe_and_elapsed_wait() -> None:
    audit = fakes.FakeAuditLog()
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway(
            [fakes.turn(capacity=CreditsExhausted()), fakes.turn(done=True, summary="finished")]
        ),
        probe=fakes.FakeCapacityProbe(
            [
                fakes.signals_for(Available()),
                fakes.signals_for(CreditsExhausted()),
                fakes.signals_for(Available()),
            ]
        ),
        clock=clock,
        sleeper=sleeper,
        audit=audit,
    )
    anyio.run(runner.run, "do the work")
    restored = [payload for event, payload in audit.events if event == "capacity_restored"]
    assert restored
    assert "probe_number" in restored[0]
    assert "elapsed_wait_seconds" in restored[0]
    assert restored[0]["elapsed_wait_seconds"] >= 0


def test_wait_only_remaining_work_delays_then_sends() -> None:
    gateway = fakes.FakeAgentGateway(
        [
            fakes.turn(remaining_work=("waiting for CI to finish",)),
            fakes.turn(done=True, summary="finished"),
        ]
    )
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    reporter = fakes.FakeProgressReporter()
    runner = fakes.build_runner(gateway=gateway, clock=clock, sleeper=sleeper, reporter=reporter)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert sleeper.wait_log
    assert gateway.sent_prompts[0] == "do the work"
    assert gateway.sent_prompts[1] == "Continue exactly where you left off."


def test_stop_during_progress_wait_ends_the_run() -> None:
    control = fakes.FakeRunControl(script=[[Stop()]])
    gateway = fakes.FakeAgentGateway([fakes.turn(remaining_work=("waiting for CI to finish",))])
    runner = fakes.build_runner(gateway=gateway, control=control)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert "stopped" in result.reason.lower()


def test_non_stop_control_commands_are_ignored_during_wait() -> None:
    control = fakes.FakeRunControl(script=[[Prompt("nudge")], [Stop()]])
    gateway = fakes.FakeAgentGateway([fakes.turn(capacity=CreditsExhausted())])
    probe = fakes.FakeCapacityProbe([fakes.signals_for(Available())])
    runner = fakes.build_runner(gateway=gateway, probe=probe, control=control)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert "stopped" in result.reason.lower()


def test_probe_config_fault_during_wait_is_terminal() -> None:
    gateway = fakes.FakeAgentGateway([fakes.turn(capacity=CreditsExhausted())])
    probe = fakes.FakeCapacityProbe(
        [
            fakes.signals_for(Available()),
            fakes.signals_for(ConfigFault(detail="probe misconfigured")),
        ]
    )
    result = anyio.run(fakes.build_runner(gateway=gateway, probe=probe).run, "do the work")
    assert result.success is False
    assert "probe misconfigured" in result.reason


def test_plan_remaining_work_marks_finished_checklist_items() -> None:
    plan = WorkPlan.parse("- [ ] alpha\n- [ ] beta\n")
    gateway = fakes.FakeAgentGateway(
        [
            fakes.turn(remaining_work=("beta",)),
            fakes.turn(remaining_work=("unlisted leftover",)),
            fakes.turn(done=True, summary="all done"),
        ]
    )
    runner = fakes.build_runner(gateway=gateway, plan=plan)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert gateway.send_calls == 3


def test_stop_during_credits_wait_ends_the_run() -> None:
    control = fakes.FakeRunControl(script=[[Stop()]])
    gateway = fakes.FakeAgentGateway([fakes.turn(capacity=CreditsExhausted())])
    probe = fakes.FakeCapacityProbe([fakes.signals_for(Available())])
    runner = fakes.build_runner(gateway=gateway, probe=probe, control=control)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert "stopped" in result.reason.lower()


def test_hooks_and_lock_are_released_when_the_gateway_raises() -> None:
    hooks = fakes.FakeHookManager()
    lock = fakes.FakeAgentLock()
    gateway = fakes.FakeAgentGateway([])
    runner = fakes.build_runner(gateway=gateway, hooks=hooks, lock=lock)
    with pytest.raises(IndexError):
        anyio.run(runner.run, "do the work")
    assert hooks.installed_then_restored is True
    assert lock.held == set()
    assert gateway.closed is True


class _RaisingStore:
    def save(self, run_id: str, state: dict[str, Any]) -> None:
        del run_id, state
        raise RuntimeError("disk full")

    def load(self, run_id: str) -> dict[str, Any] | None:
        del run_id
        return None


def test_hooks_and_lock_are_released_when_persist_raises() -> None:
    """A failed store.save must not leave the lock held or hooks installed."""
    hooks = fakes.FakeHookManager()
    lock = fakes.FakeAgentLock()
    gateway = fakes.FakeAgentGateway([fakes.turn(done=True, summary="finished")])
    runner = fakes.build_runner(gateway=gateway, hooks=hooks, lock=lock, store=_RaisingStore())
    with pytest.raises(RuntimeError, match="disk full"):
        anyio.run(runner.run, "do the work")
    assert hooks.installed_then_restored is True
    assert lock.held == set()
    assert gateway.closed is True


def test_lock_held_fails_without_sending() -> None:
    lock = fakes.FakeAgentLock()
    lock.acquire("fake-agent")
    gateway = fakes.FakeAgentGateway([fakes.turn(done=True, summary="finished")])
    runner = fakes.build_runner(gateway=gateway, lock=lock)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert "lock" in result.reason.lower()
    assert gateway.send_calls == 0


def test_continue_then_done_uses_the_continue_prompt() -> None:
    gateway = fakes.FakeAgentGateway(
        [
            fakes.turn(remaining_work=("write the tests",)),
            fakes.turn(done=True, summary="finished"),
        ]
    )
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert gateway.sent_prompts == ["do the work", "Continue exactly where you left off."]
    assert result.turns_spent == 2


def test_run_from_plan_file_prefixes_autonomy_preamble(tmp_path: Path) -> None:
    plan_path = tmp_path / "handoff.md"
    plan_path.write_text("ship the feature\n", encoding="utf-8")
    gateway = fakes.FakeAgentGateway([fakes.turn(done=True, summary="all done")])
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(run_from_plan_file, runner, plan_path)
    assert result.success is True
    assert autonomy_preamble() in gateway.sent_prompts[0]
    assert "ship the feature" in gateway.sent_prompts[0]


def test_early_done_is_reconciled_against_remaining_plan_items() -> None:
    gateway = fakes.FakeAgentGateway([fakes.turn(done=True, summary="too soon")])
    plan = WorkPlan.parse("- [ ] alpha\n- [ ] beta\n")
    runner = fakes.build_runner(gateway=gateway, plan=plan, budget=Budget(max_turns=1))
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert result.reason == "budget exhausted"
    assert gateway.send_calls == 1


def test_unknown_turn_cost_is_passed_as_none_not_zero() -> None:
    gateway = fakes.FakeAgentGateway(
        [fakes.turn(done=True, summary="finished", tokens=10, cost_usd=None)]
    )
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert result.cost_pending is True
    assert result.tokens_spent == 10
    assert result.dollars_spent == 0.0


def test_credits_notify_once_per_waiting_episode_not_per_probe() -> None:
    notifier = fakes.FakeNotifier()
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway(
            [fakes.turn(capacity=CreditsExhausted()), fakes.turn(done=True, summary="finished")]
        ),
        probe=fakes.FakeCapacityProbe(
            [fakes.signals_for(Available())]
            + [fakes.signals_for(CreditsExhausted())] * 3
            + [fakes.signals_for(Available())]
        ),
        notifier=notifier,
    )
    anyio.run(runner.run, "do the work")
    credit_messages = [m for m in notifier.messages if "credit" in m.lower()]
    assert len(credit_messages) == 1


def test_preflight_config_fault_is_terminal() -> None:
    probe = fakes.FakeCapacityProbe([fakes.signals_for(ConfigFault(detail="bad mcp"))])
    gateway = fakes.FakeAgentGateway([])
    result = anyio.run(fakes.build_runner(gateway=gateway, probe=probe).run, "do the work")
    assert result.success is False
    assert "bad mcp" in result.reason
    assert gateway.send_calls == 0


def test_preflight_transient_then_available_retries_the_probe() -> None:
    probe = fakes.FakeCapacityProbe(
        [
            fakes.signals_for(TransientFault(kind="network", attempt_hint=1)),
            fakes.signals_for(Busy(agent_id="", active_run_id=None)),
            fakes.signals_for(Available()),
        ]
    )
    gateway = fakes.FakeAgentGateway([fakes.turn(done=True, summary="finished")])
    result = anyio.run(fakes.build_runner(gateway=gateway, probe=probe).run, "do the work")
    assert result.success is True
    assert probe.calls == 3
    assert gateway.cancel_calls == 1


def test_preflight_transient_gives_up_at_the_cap() -> None:
    probe = fakes.FakeCapacityProbe(
        [fakes.signals_for(TransientFault(kind="network", attempt_hint=1))] * 5
    )
    gateway = fakes.FakeAgentGateway([])
    result = anyio.run(
        fakes.build_runner(gateway=gateway, probe=probe, max_transient_retries=0).run,
        "do the work",
    )
    assert result.success is False
    assert probe.calls == 1
    assert gateway.send_calls == 0


def test_transient_backoff_applies_bounded_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retries must jitter the exponential delay, not sleep a deterministic 1+2+4."""
    monkeypatch.setattr(runner_mod.random, "uniform", lambda _a, _b: 0.5)
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    started = clock.now()
    gateway = fakes.FakeAgentGateway([fakes.transient_turn()] * 10)
    runner = fakes.build_runner(
        gateway=gateway, clock=clock, sleeper=sleeper, max_transient_retries=3
    )
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    elapsed = (clock.now() - started).total_seconds()
    # base delays 1+2+4 plus 0.5s jitter each = 8.5; without jitter this is 7.0
    assert elapsed == pytest.approx(8.5)
    assert sleeper.real_sleep_calls == 0


def test_busy_probe_script_terminates_without_hanging() -> None:
    """A stuck AgentBusyError on the probe path must cap and back off, not busy-loop."""
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    probe = fakes.FakeCapacityProbe([fakes.signals_for(Busy(agent_id="", active_run_id=None))] * 20)
    gateway = fakes.FakeAgentGateway([])
    runner = fakes.build_runner(
        gateway=gateway,
        probe=probe,
        clock=clock,
        sleeper=sleeper,
        max_transient_retries=3,
    )
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert probe.calls == 4  # initial + 3 retries
    assert sleeper.real_sleep_calls == 0
    assert sleeper.wait_log


def test_busy_send_script_terminates_without_hanging() -> None:
    """A stuck AgentBusyError on send must cancel, force-retry with backoff, then cap."""
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    gateway = fakes.FakeAgentGateway([fakes.busy_turn()] * 20)
    runner = fakes.build_runner(
        gateway=gateway, clock=clock, sleeper=sleeper, max_transient_retries=3
    )
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert gateway.send_calls == 4  # initial + 3 retries
    assert gateway.cancel_calls == 4
    assert gateway.force_flags == [False, True, True, True]
    assert sleeper.real_sleep_calls == 0
    assert sleeper.wait_log


async def test_a_wind_down_finishes_with_a_marker_rather_than_success() -> None:
    """A supervisor has to tell "resume me elsewhere" from "this is done"."""
    markers: list[HandoffMarker] = []
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway(
            [fakes.turn(done=False), fakes.turn(done=True, summary="done")]
        ),
        # One turn of headroom against a reserve of two: the first completed
        # turn is already inside the reserve.
        budget=Budget(max_turns=2, max_cost_usd=10.0),
        handoff_marker_writer=markers.append,
        wind_down_policy=WindDownPolicy(enabled=True),
    )

    result = await runner.run(initial_prompt="start")

    assert result.success is False
    assert result.reason.startswith("wind-down:")
    assert markers, "a wind-down must leave a handoff marker"
    assert markers[0].reason == "turn_reserve"


async def test_a_wind_down_without_a_writer_still_finishes_cleanly() -> None:
    """No writer means no marker, which is the honest signal: a supervisor that
    finds no handoff.json falls back to the reactive path."""
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway(
            [fakes.turn(done=False), fakes.turn(done=True, summary="done")]
        ),
        budget=Budget(max_turns=2, max_cost_usd=10.0),
        wind_down_policy=WindDownPolicy(enabled=True),
    )

    result = await runner.run(initial_prompt="start")

    assert result.success is False
    assert "wind-down" in result.reason


async def test_wind_down_during_progress_wait_ends_the_run() -> None:
    """Wind-down control command during a DelayThenSend wait should finish the run."""
    gateway = fakes.FakeAgentGateway([fakes.turn(done=False, remaining_work=("waiting for CI",))])
    control = fakes.FakeRunControl(script=[[], [WindDown(reason="test wind-down")]])
    runner = fakes.build_runner(gateway=gateway, control=control)

    result = await runner.run(initial_prompt="start")

    assert result.success is False
    assert "wind-down" in result.reason.lower()
    assert "operator request" in result.reason


async def test_wind_down_during_capacity_wait_ends_the_run() -> None:
    """Wind-down control command during a ScheduleProbe wait should finish the run."""
    probe = fakes.FakeCapacityProbe(
        [fakes.signals_for(Available())]
        + [fakes.signals_for(CreditsExhausted())] * 2
        + [fakes.signals_for(Available())]
    )
    gateway = fakes.FakeAgentGateway([fakes.turn(capacity=CreditsExhausted())])
    control = fakes.FakeRunControl(script=[[], [WindDown(reason="capacity wait wind-down")]])
    runner = fakes.build_runner(gateway=gateway, probe=probe, control=control)

    result = await runner.run(initial_prompt="start")

    assert result.success is False
    assert "wind-down" in result.reason.lower()
    assert "operator request" in result.reason


async def test_the_policy_off_leaves_the_run_untouched() -> None:
    """The predictive path is strictly additive."""
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway([fakes.turn(done=True, summary="done")]),
        budget=Budget(max_turns=2, max_cost_usd=10.0),
    )

    result = await runner.run(initial_prompt="start")

    assert result.success is True

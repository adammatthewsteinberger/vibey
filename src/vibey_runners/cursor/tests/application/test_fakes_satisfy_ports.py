# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import anyio
import pytest

from cursorloop.application import ports
from cursorloop.application.dto import ProbeResult, RunResult, TurnOutcome
from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.classify import TurnSignals, classify
from cursorloop.domain.completion import StructuredVerdict
from cursorloop.domain.faults import Busy, ConfigFault, TransientFault
from cursorloop.domain.model_profile import SHIPPED_PRESETS
from tests.application import fakes


def test_every_fake_structurally_satisfies_its_protocol() -> None:
    """Protocol conformance is structural, so a drifted fake fails silently at
    runtime and only shows up as a confusing test failure later. Assert it."""
    assert isinstance(fakes.FakeClock(), ports.Clock)
    assert isinstance(fakes.FakeSleeper(fakes.FakeClock()), ports.Sleeper)
    assert isinstance(fakes.FakeAgentGateway([]), ports.AgentGateway)
    assert isinstance(fakes.FakeCapacityProbe([]), ports.CapacityProbe)
    assert isinstance(fakes.FakeHookManager(), ports.HookManager)
    assert isinstance(fakes.FakeNotifier(), ports.Notifier)
    assert isinstance(fakes.FakeAuditLog(), ports.AuditLog)
    assert isinstance(fakes.FakeRunStateStore(), ports.RunStateStore)
    assert isinstance(fakes.FakeAgentLock(), ports.AgentLock)
    assert isinstance(fakes.FakeUsageReader(), ports.UsageReader)
    assert isinstance(fakes.FakeProgressReporter(), ports.ProgressReporter)
    assert isinstance(fakes.FakeLogger(), ports.Logger)
    assert isinstance(fakes.FakeRunControl(), ports.RunControl)


def test_fake_sleeper_advances_the_fake_clock_without_real_sleeping() -> None:
    """This is what makes a simulated seven-day wait run in microseconds."""
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    target = clock.now().replace(year=clock.now().year + 1)

    anyio.run(sleeper.sleep_until, target)
    assert clock.now() == target
    assert sleeper.total_simulated_seconds > 0
    assert sleeper.real_sleep_calls == 0


def test_fake_clock_is_settable_and_refuses_to_run_backwards() -> None:
    start = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    clock = fakes.FakeClock(start)
    later = start.replace(hour=13)
    clock.advance_to(later)
    assert clock.now() == later
    with pytest.raises(ValueError, match="monotonic"):
        clock.advance_to(start)


def test_fake_clock_advance_is_monotonic() -> None:
    start = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    clock = fakes.FakeClock(start)
    clock.advance(timedelta(minutes=11))
    assert clock.now() == start.replace(hour=12, minute=11)
    with pytest.raises(ValueError, match="monotonic"):
        clock.advance(timedelta(minutes=-1))


def test_fake_run_records_cancel_calls() -> None:
    run = fakes.FakeRun(status="running")
    run.cancel()
    assert run.cancel_calls == 1
    assert run.status == "cancelled"
    finished = fakes.FakeRun(status="finished")
    finished.cancel()
    assert finished.cancel_calls == 1
    assert finished.status == "finished"


def test_fake_sleeper_does_not_rewind_the_clock_for_a_past_instant() -> None:
    start = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    clock = fakes.FakeClock(start)
    sleeper = fakes.FakeSleeper(clock)
    anyio.run(sleeper.sleep_until, start.replace(hour=11))
    assert clock.now() == start
    assert sleeper.total_simulated_seconds == 0


async def test_fake_agent_gateway_replays_scripted_turn_outcomes() -> None:
    first = TurnOutcome(
        signals=TurnSignals(),
        verdict=None,
        output_text="one",
        agent_id="agent-1",
        run_id="run-1",
        tokens=10,
        cost_usd=None,
        cost_pending=True,
    )
    second = TurnOutcome(
        signals=TurnSignals(run_status="finished"),
        verdict=StructuredVerdict(complete=True, summary="done"),
        output_text="two",
        agent_id="agent-1",
        run_id="run-2",
        tokens=20,
        cost_usd=0.02,
        cost_pending=False,
    )
    gateway = fakes.FakeAgentGateway([first, second], agent_id="agent-1")

    assert gateway.agent_id() == "agent-1"
    assert await gateway.send_turn("do work") is first
    assert await gateway.send_turn("continue", force=True) is second
    assert gateway.sent_prompts == ["do work", "continue"]
    assert gateway.force_flags == [False, True]
    await gateway.set_profile(SHIPPED_PRESETS["composer"])
    await gateway.set_cwd("/repo")
    assert await gateway.cancel_active_run() is True
    await gateway.close()
    assert gateway.closed is True
    assert gateway.cwds == ["/repo"]
    assert gateway.profiles == [SHIPPED_PRESETS["composer"]]
    with pytest.raises(IndexError):
        await gateway.send_turn("runaway")


async def test_fake_capacity_probe_replays_scripted_turn_signals() -> None:
    available = TurnSignals(run_status="finished")
    exhausted = TurnSignals(error_type="RateLimitError", is_retryable=False)
    probe = fakes.FakeCapacityProbe([exhausted, available])

    first = await probe.probe()
    second = await probe.probe()
    assert first.signals is exhausted
    assert second.signals is available
    assert first.cost_pending is True
    assert first.cost_usd is None
    with pytest.raises(IndexError):
        await probe.probe()


def test_fake_hook_manager_installs_and_restores() -> None:
    hooks = fakes.FakeHookManager()
    assert hooks.is_installed() is False
    assert hooks.restore() is False
    hooks.install()
    assert hooks.is_installed() is True
    assert hooks.restore() is True
    assert hooks.is_installed() is False
    assert hooks.installed_then_restored is True


def test_fake_notifier_records_messages() -> None:
    notifier = fakes.FakeNotifier()
    notifier.notify("credits exhausted")
    assert notifier.messages == ["credits exhausted"]


def test_fake_audit_log_records_events() -> None:
    audit = fakes.FakeAuditLog()
    audit.record("entered_credits_exhausted", {"probe": 1})
    assert audit.events == [("entered_credits_exhausted", {"probe": 1})]


def test_fake_run_state_store_round_trips_state() -> None:
    store = fakes.FakeRunStateStore()
    assert store.load("missing") is None
    store.save("run-1", {"phase": "waiting"})
    assert store.load("run-1") == {"phase": "waiting"}


def test_fake_agent_lock_is_exclusive_per_agent() -> None:
    lock = fakes.FakeAgentLock()
    assert lock.acquire("agent-1") is True
    assert lock.acquire("agent-1") is False
    assert lock.acquire("agent-2") is True
    lock.release("agent-1")
    assert lock.acquire("agent-1") is True


def test_signals_for_maps_capacity_and_faults_to_classify_inputs() -> None:
    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    assert isinstance(classify(fakes.signals_for(CreditsExhausted()), now=now), CreditsExhausted)
    assert isinstance(classify(fakes.signals_for(Available()), now=now), Available)
    assert isinstance(
        classify(fakes.signals_for(Busy(agent_id="", active_run_id=None)), now=now), Busy
    )
    assert isinstance(
        classify(fakes.signals_for(TransientFault(kind="network", attempt_hint=1)), now=now),
        TransientFault,
    )
    assert isinstance(classify(fakes.signals_for(ConfigFault(detail="nope")), now=now), ConfigFault)
    assert isinstance(
        classify(fakes.signals_for(AuthenticationFailed("bad key")), now=now),
        AuthenticationFailed,
    )
    window = classify(
        fakes.signals_for(WindowExhausted("rate_limit", None)),
        now=now,
    )
    assert isinstance(window, WindowExhausted)
    scheduled = classify(
        fakes.signals_for(WindowExhausted("rate_limit", now)),
        now=now,
    )
    assert isinstance(scheduled, WindowExhausted)
    with pytest.raises(TypeError, match="unsupported"):
        fakes.signals_for(object())  # type: ignore[arg-type]


async def test_fake_usage_reader_returns_none_when_cost_is_unknown() -> None:
    reader = fakes.FakeUsageReader()
    assert await reader.billed_cost_usd() is None
    assert await reader.turn_tokens("run-1") == 0
    known = fakes.FakeUsageReader(tokens=42, billed_cost_usd=1.25)
    assert await known.turn_tokens("run-9") == 42
    assert await known.billed_cost_usd() == 1.25


def test_turn_outcome_propagates_cost_pending_from_unknown_usage() -> None:
    outcome = TurnOutcome(
        signals=TurnSignals(),
        verdict=None,
        output_text="",
        agent_id="agent-1",
        run_id="run-1",
        tokens=100,
        cost_usd=None,
        cost_pending=True,
    )
    assert outcome.cost_usd is None
    assert outcome.cost_pending is True
    settled = TurnOutcome(
        signals=TurnSignals(),
        verdict=None,
        output_text="",
        agent_id="agent-1",
        run_id="run-1",
        tokens=100,
        cost_usd=0.04,
        cost_pending=False,
        raw_events=({"type": "usage"},),
    )
    assert settled.cost_pending is False
    assert settled.cost_usd == 0.04


def test_probe_and_run_result_dtos_carry_cost_pending() -> None:
    at = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    probe = ProbeResult(signals=TurnSignals(), at=at)
    assert probe.at == at
    result = RunResult(
        success=True,
        reason="done",
        agent_id="agent-1",
        turns_spent=2,
        tokens_spent=30,
        dollars_spent=0.05,
        cost_pending=True,
    )
    assert result.cost_pending is True
    assert result.agent_id == "agent-1"

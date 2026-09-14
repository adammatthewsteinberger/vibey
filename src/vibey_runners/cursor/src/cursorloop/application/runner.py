# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""AutonomousRunner — executes domain.loop Decisions against ports.

Contains NO capacity or completion logic of its own. classify / evaluate /
decide_* answer those questions; this module only performs the I/O they
decided was needed.
"""

from __future__ import annotations

import contextlib
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal, assert_never

from cursorloop.application.dto import RunResult, TurnOutcome
from cursorloop.application.ports import (
    AgentGateway,
    AgentLock,
    AuditLog,
    CapacityProbe,
    Clock,
    HookManager,
    Logger,
    Notifier,
    ProgressReporter,
    RunControl,
    RunStateStore,
    Sleeper,
)
from cursorloop.domain.budget import Budget, BudgetLedger
from cursorloop.domain.capacity import Available, CapacityState, CreditsExhausted
from cursorloop.domain.classify import classify
from cursorloop.domain.completion import (
    DEFAULT_DONE_MARKER,
    CompletionVerdict,
    Continue,
    evaluate,
    reconcile,
)
from cursorloop.domain.control import Stop, WindDown
from cursorloop.domain.faults import Busy, ConfigFault, TransientFault
from cursorloop.domain.forecast import (
    BurnRate,
    CapacityForecast,
    WindDownPolicy,
    forecast,
    should_wind_down,
)
from cursorloop.domain.handoff_marker import HandoffMarker
from cursorloop.domain.loop import (
    Decision,
    DelayThenSend,
    Finish,
    RunProbe,
    RunState,
    ScheduleProbe,
    SendTurn,
    WindDownAndFinish,
    decide_after_probe,
    decide_after_turn,
    decide_preflight,
    decide_progress_delay,
    start,
)
from cursorloop.domain.plan import WorkPlan
from cursorloop.domain.waiting import (
    DEFAULT_PROGRESS_WAIT_CONFIG,
    DEFAULT_WAIT_POLICY_CONFIG,
    ProgressWaitConfig,
    WaitPolicyConfig,
)

_SLEEP_CHUNK = timedelta(seconds=5)
_CONTINUE_PROMPT = "Continue exactly where you left off."
_BACKOFF_CEILING_SECONDS = 8.0
_JITTER_SECONDS = 1.0


@dataclass
class RunnerContext:
    """All ports and config the autonomous runner needs."""

    gateway: AgentGateway
    probe: CapacityProbe
    clock: Clock
    sleeper: Sleeper
    reporter: ProgressReporter
    audit: AuditLog
    notifier: Notifier
    logger: Logger
    hooks: HookManager
    lock: AgentLock
    store: RunStateStore
    control: RunControl
    budget: Budget = field(default_factory=Budget)
    wait_policy: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG
    progress_wait: ProgressWaitConfig = DEFAULT_PROGRESS_WAIT_CONFIG
    max_transient_retries: int = 8
    run_id: str = "anonymous"
    plan: WorkPlan | None = None
    continue_prompt: str = _CONTINUE_PROMPT
    done_marker: str = DEFAULT_DONE_MARKER
    handoff_marker_writer: Callable[[HandoffMarker], object] | None = None
    wind_down_policy: WindDownPolicy = field(default_factory=WindDownPolicy)


class AutonomousRunner:
    def __init__(self, ctx: RunnerContext) -> None:
        self._gateway = ctx.gateway
        self._probe = ctx.probe
        self._clock = ctx.clock
        self._sleeper = ctx.sleeper
        self._reporter = ctx.reporter
        self._audit = ctx.audit
        self._notifier = ctx.notifier
        self._log = ctx.logger.bind(run_id=ctx.run_id, component="runner")
        self._hooks = ctx.hooks
        self._lock = ctx.lock
        self._store = ctx.store
        self._control = ctx.control
        self._budget = ctx.budget
        self._wait_policy = ctx.wait_policy
        self._progress_wait = ctx.progress_wait
        self._max_transient_retries = ctx.max_transient_retries
        self._run_id = ctx.run_id
        self._plan = ctx.plan
        self._continue_prompt = ctx.continue_prompt
        self._done_marker = ctx.done_marker
        self._handoff_marker_writer = ctx.handoff_marker_writer
        self._wind_down_policy = ctx.wind_down_policy
        self._first_turn = True
        self._credits_notified = False
        self._last_capacity: CapacityState | None = None
        self._wait_probe_count = 0
        self._empty_turn_streak = 0
        self._progress_wait_streak = 0
        self._attempt = 0
        self._started_at: datetime | None = None

    def attach_plan(self, plan: WorkPlan) -> None:
        self._plan = plan

    async def run(self, initial_prompt: str) -> RunResult:
        state = start(BudgetLedger(budget=self._budget))
        agent_id = self._gateway.agent_id()
        result: RunResult | None = None
        acquired = False
        self._started_at = self._clock.now()
        self._first_turn = True
        self._log.info("run.started", prompt_len=len(initial_prompt))
        try:
            self._hooks.install()
            if not self._lock.acquire(agent_id):
                result = self._finish(state, Finish(success=False, reason="lock held"), agent_id)
                return result
            acquired = True

            classified = await self._until_capacity()
            if isinstance(classified, Finish):
                decision: Decision = classified
            else:
                self._maybe_notify_credits(classified)
                state, decision = decide_preflight(
                    state,
                    classified,
                    now=self._clock.now(),
                    config=self._wait_policy,
                )
                self._persist(state)

            while True:
                if isinstance(decision, SendTurn):
                    state, decision = await self._do_send(state, initial_prompt)
                elif isinstance(decision, DelayThenSend):
                    self._log.info("progress.wait", until=decision.at.isoformat())
                    interrupt = await self._sleep_interruptible(decision.at)
                    if interrupt == "stop":
                        decision = Finish(success=False, reason="stopped by operator")
                        continue
                    if interrupt == "wind_down":
                        decision = Finish(success=False, reason="wind-down: operator request")
                        continue
                    decision = SendTurn()
                elif isinstance(decision, ScheduleProbe):
                    self._reporter.waiting(reason=state.phase.name, until=decision.at)
                    self._log.info(
                        "waiting.scheduled",
                        until=decision.at.isoformat(),
                        probe_count=state.probe_count,
                    )
                    interrupt = await self._sleep_interruptible(decision.at)
                    if interrupt == "stop":
                        decision = Finish(success=False, reason="stopped by operator")
                        continue
                    if interrupt == "wind_down":
                        decision = Finish(success=False, reason="wind-down: operator request")
                        continue
                    decision = RunProbe()
                elif isinstance(decision, RunProbe):
                    state, decision = await self._do_probe(state)
                elif isinstance(decision, WindDownAndFinish):
                    return self._finish_wound_down(state, decision, agent_id)
                elif isinstance(decision, Finish):
                    result = self._finish(state, decision, agent_id)
                    return result
                else:
                    assert_never(decision)  # pragma: no cover - Decision union is exhaustive
        except BaseException as exc:
            self._log.error("run.exception", error=type(exc).__name__, detail=str(exc)[:500])
            raise
        finally:
            with contextlib.suppress(Exception):
                self._persist(state)
            if acquired:
                self._lock.release(agent_id)
            self._hooks.restore()
            with contextlib.suppress(Exception):
                await self._gateway.close()
            if result is not None:
                self._reporter.finished(success=result.success, reason=result.reason)

    async def _do_send(self, state: RunState, initial_prompt: str) -> tuple[RunState, Decision]:
        prompt = self._next_prompt(initial_prompt)
        self._attempt += 1
        self._reporter.turn_sent(attempt=self._attempt)
        state = RunState(
            phase=state.phase,
            ledger=state.ledger.spend_attempt(),
            started_waiting_at=state.started_waiting_at,
            probe_count=state.probe_count,
            failure_reason=state.failure_reason,
        )
        force = False
        transient = 0
        busy = 0
        while True:
            outcome = await self._gateway.send_turn(prompt, force=force)
            force = False
            classified = classify(outcome.signals, now=self._clock.now())
            if isinstance(classified, Busy):
                await self._gateway.cancel_active_run()
                terminal = self._retry_or_give_up(busy, reason="agent busy")
                if isinstance(terminal, Finish):
                    return state, terminal
                busy = terminal
                force = True
                await self._sleep_backoff(busy)
                continue
            if isinstance(classified, TransientFault):
                terminal = self._transient_or_retry(classified, transient)
                if isinstance(terminal, Finish):
                    return state, terminal
                transient = terminal
                await self._sleep_backoff(transient)
                continue
            if isinstance(classified, ConfigFault):
                return state, Finish(success=False, reason=classified.detail)

            self._last_capacity = classified
            self._maybe_notify_credits(classified)
            verdict = self._verdict_for(outcome)
            now = self._clock.now()
            projection = self._project_capacity(state, capacity=classified, now=now)
            wind_down = (
                should_wind_down(
                    projection, self._wind_down_policy, turns_spent=state.ledger.turns_spent + 1
                )
                if projection is not None
                else None
            )
            state, decision = decide_after_turn(
                state,
                capacity=classified,
                verdict=verdict,
                now=now,
                config=self._wait_policy,
                tokens=outcome.tokens,
                dollars=outcome.cost_usd,
                started_at=self._started_at,
                wind_down=wind_down,
            )
            if (
                isinstance(decision, SendTurn)
                and isinstance(verdict, Continue)
                and isinstance(classified, Available)
            ):
                delayed = decide_progress_delay(
                    verdict=verdict,
                    tree_changed=not bool(verdict.remaining_work),
                    now=self._clock.now(),
                    streak=self._progress_wait_streak,
                    config=self._progress_wait,
                )
                if delayed is not None:
                    decision = delayed
                    self._progress_wait_streak += 1
                else:
                    self._progress_wait_streak = 0
            self._persist(state)
            self._log.debug(
                "decision.after_turn",
                decision=type(decision).__name__,
                phase=state.phase.name,
            )
            return state, decision

    async def _do_probe(self, state: RunState) -> tuple[RunState, Decision]:
        previous = self._last_capacity
        classified = await self._until_capacity()
        if isinstance(classified, Finish):
            return state, classified
        self._wait_probe_count += 1
        now = self._clock.now()
        if (
            previous is not None
            and not isinstance(previous, Available)
            and isinstance(classified, Available)
        ):
            started = state.started_waiting_at or now
            self._audit.record(
                "capacity_restored",
                {
                    "probe_number": self._wait_probe_count,
                    "elapsed_wait_seconds": (now - started).total_seconds(),
                },
            )
            self._log.info(
                "capacity.restored",
                probe_number=self._wait_probe_count,
                elapsed_wait_seconds=(now - started).total_seconds(),
            )
        self._maybe_notify_credits(classified)
        state, decision = decide_after_probe(
            state,
            classified,
            now=now,
            config=self._wait_policy,
            started_at=self._started_at,
        )
        self._persist(state)
        return state, decision

    async def _until_capacity(self) -> CapacityState | Finish:
        transient = 0
        busy = 0
        while True:
            outcome = await self._probe.probe()
            classified = classify(outcome.signals, now=self._clock.now())
            if isinstance(classified, Busy):
                await self._gateway.cancel_active_run()
                terminal = self._retry_or_give_up(busy, reason="agent busy")
                if isinstance(terminal, Finish):
                    return terminal
                busy = terminal
                await self._sleep_backoff(busy)
                continue
            if isinstance(classified, TransientFault):
                terminal = self._retry_or_give_up(
                    transient, reason=f"transient fault: {classified.kind}"
                )
                if isinstance(terminal, Finish):
                    return terminal
                transient = terminal
                await self._sleep_backoff(transient)
                continue
            if isinstance(classified, ConfigFault):
                return Finish(success=False, reason=classified.detail)
            self._last_capacity = classified
            return classified

    def _retry_or_give_up(self, attempt: int, *, reason: str) -> int | Finish:
        if attempt >= self._max_transient_retries:
            return Finish(success=False, reason=reason)
        return attempt + 1

    def _transient_or_retry(self, fault: TransientFault, transient: int) -> int | Finish:
        return self._retry_or_give_up(transient, reason=f"transient fault: {fault.kind}")

    async def _sleep_backoff(self, attempt: int) -> None:
        base = min(float(2 ** (attempt - 1)), _BACKOFF_CEILING_SECONDS)
        jitter = random.uniform(0.0, _JITTER_SECONDS)  # noqa: S311  # nosec B311
        await self._sleeper.sleep_until(self._clock.now() + timedelta(seconds=base + jitter))

    def _verdict_for(self, outcome: TurnOutcome) -> CompletionVerdict:
        verdict = evaluate(
            structured=outcome.verdict,
            output_text=outcome.output_text,
            done_marker=self._done_marker,
            tokens=outcome.tokens,
            empty_turn_streak=self._empty_turn_streak,
        )
        empty = not outcome.output_text.strip() and outcome.tokens <= 0
        if isinstance(verdict, Continue) and empty:
            self._empty_turn_streak += 1
        else:
            self._empty_turn_streak = 0
        return self._apply_plan(verdict)

    def _apply_plan(self, verdict: CompletionVerdict) -> CompletionVerdict:
        if self._plan is None:
            return verdict
        if isinstance(verdict, Continue) and verdict.remaining_work:
            remaining = set(verdict.remaining_work)
            done_texts = frozenset(
                item.text for item in self._plan.items if item.text not in remaining
            )
            self._plan = self._plan.with_items_marked_done(done_texts)
        return reconcile(verdict, self._plan)

    def _next_prompt(self, initial_prompt: str) -> str:
        if self._first_turn:
            self._first_turn = False
            return initial_prompt
        return self._continue_prompt

    def _maybe_notify_credits(self, capacity: CapacityState) -> None:
        if isinstance(capacity, CreditsExhausted):
            if not self._credits_notified:
                self._notifier.notify(
                    "cursorloop: credits exhausted — top up to resume. "
                    "The runner will keep probing."
                )
                self._audit.record(
                    "entered_credits_exhausted",
                    {"can_purchase": capacity.can_purchase},
                )
                self._credits_notified = True
                self._log.warning("credits.exhausted", can_purchase=capacity.can_purchase)
        elif isinstance(capacity, Available):
            self._credits_notified = False

    async def _sleep_interruptible(
        self, until: datetime
    ) -> None | Literal["stop"] | Literal["wind_down"]:
        """Sleep until the given time, checking for control commands.

        Returns None if the wait completed normally, "stop" if a Stop was received,
        or "wind_down" if a WindDown was received.
        """
        while self._clock.now() < until:
            for command in self._control.poll():
                if isinstance(command, Stop):
                    return "stop"
                if isinstance(command, WindDown):
                    return "wind_down"
            now = self._clock.now()
            wake = until if now + _SLEEP_CHUNK > until else now + _SLEEP_CHUNK
            await self._sleeper.sleep_until(wake)
        return None

    def _project_capacity(
        self, state: RunState, *, capacity: CapacityState, now: datetime
    ) -> CapacityForecast | None:
        """Forecast remaining capacity, but only while the vendor says we are
        not already blocked.

        This runner has no utilization producer, so the vendor dimension is
        always unknown and only the budget dimensions carry a number. That is
        the honest forecast for this vendor rather than a fabricated one.
        """
        if not isinstance(capacity, Available):
            return None
        turns = state.ledger.turns_spent + 1
        projection = forecast(
            capacity,
            turns_spent=turns,
            max_turns=self._budget.max_turns,
            dollars_spent=state.ledger.dollars_spent,
            max_dollars=self._budget.max_cost_usd,
            observed=BurnRate(turns=turns, elapsed_seconds=0.0, dollars=state.ledger.dollars_spent),
            capacity_as_of=now,
            now=now,
            policy=self._wind_down_policy,
        )
        self._log.debug(
            "capacity.forecast",
            headroom=projection.binding.fraction,
            source=projection.binding.source,
            turns_until_exhaustion=projection.turns_until_exhaustion,
        )
        return projection

    def _finish_wound_down(
        self, state: RunState, decision: WindDownAndFinish, agent_id: str
    ) -> RunResult:
        """Stop early, on purpose, so a successor can pick the work up.

        Narrower than claudeloop's equivalent on purpose: this runner has no
        save-point or snapshot helpers, and its snapshot sink still discards
        the bundle it is handed. So the marker names the summary it can honestly
        vouch for and nothing more -- a marker pointing at artifacts that were
        never written is worse than a thin one.
        """
        binding = decision.forecast.binding
        marker = HandoffMarker(
            run_id=self._run_id,
            reason=decision.reason,
            produced_at=self._clock.now(),
            headroom=binding.fraction,
            headroom_source=binding.source,
            resets_at=binding.resets_at,
            session_id=agent_id,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
        )
        if self._handoff_marker_writer is not None:
            self._handoff_marker_writer(marker)
        self._audit.record(
            "wind_down",
            {"reason": decision.reason, "headroom": binding.fraction, "source": binding.source},
        )
        self._log.info("run.wound_down", reason=decision.reason, headroom=binding.fraction)
        return self._finish(
            state, Finish(success=False, reason=f"wind-down: {decision.reason}"), agent_id
        )

    def _finish(self, state: RunState, decision: Finish, agent_id: str) -> RunResult:
        self._audit.record(
            "finished",
            {"success": decision.success, "reason": decision.reason, "run_id": self._run_id},
        )
        self._log.info("run.finished", success=decision.success, reason=decision.reason)
        self._persist(state)
        return RunResult(
            success=decision.success,
            reason=decision.reason,
            agent_id=agent_id,
            turns_spent=state.ledger.turns_spent,
            tokens_spent=state.ledger.tokens_spent,
            dollars_spent=state.ledger.dollars_spent,
            cost_pending=state.ledger.cost_pending,
        )

    def _persist(self, state: RunState) -> None:
        self._store.save(
            self._run_id,
            {
                "phase": state.phase.name,
                "turns_spent": state.ledger.turns_spent,
                "tokens_spent": state.ledger.tokens_spent,
                "dollars_spent": state.ledger.dollars_spent,
                "probe_count": state.probe_count,
                "failure_reason": state.failure_reason,
            },
        )


__all__ = ["AutonomousRunner", "RunnerContext"]

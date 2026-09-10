# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""AutonomousRunner — executes domain.loop Decisions against application ports."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Literal, assert_never

from codexloop.application.dto import RunResult, TurnOutcome
from codexloop.application.ports import (
    AgentGateway,
    CapacityProbe,
    Clock,
    Logger,
    Notifier,
    PermissionMode,
    ProgressReporter,
    RunControl,
    RunEventSink,
    RunSnapshotSink,
    RunStateStore,
    SessionLock,
    Sleeper,
    ThreadCatalog,
)
from codexloop.domain.approval import ApprovalPolicy, SandboxMode
from codexloop.domain.budget import Budget, BudgetLedger
from codexloop.domain.capacity import Available, CapacityState, QuotaExhausted
from codexloop.domain.classify import classify
from codexloop.domain.completion import (
    DEFAULT_DONE_MARKER,
    Blocked,
    CompletionEvaluator,
    CompletionVerdict,
    Continue,
)
from codexloop.domain.control import (
    ControlCommand,
    Prompt,
    ResourceMutate,
    SetApproval,
    SetCwd,
    SetEffort,
    SetModel,
    SetSandbox,
    Snapshot,
    Stop,
    WindDownCommand,
)
from codexloop.domain.error_codes import ErrorClass, classify_code
from codexloop.domain.forecast import (
    BurnRate,
    WindDown,
    WindDownPolicy,
    forecast,
    should_wind_down,
)
from codexloop.domain.handoff_marker import HandoffMarker
from codexloop.domain.loop import (
    BackoffUntil,
    Drain,
    Finish,
    LoopOutcome,
    Probe,
    RunLoopStateMachine,
    RunState,
    SendTurn,
    WaitUntil,
    WindDownAndFinish,
)
from codexloop.domain.model_profile import Effort, ModelEffortProfile
from codexloop.domain.plan import WorkPlan
from codexloop.domain.session import Explicit, MostRecent, PlanFile, SessionSelector, ThreadRef
from codexloop.domain.signals import TurnSignals
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig

_FAR_FUTURE = timedelta(days=3650)
_ZERO = timedelta(0)


class _NullLogger:
    """Diagnostics are optional; a run must not require them to be wired."""

    def bind(self, **kwargs: object) -> _NullLogger:
        del kwargs
        return self

    def debug(self, event: str, **kwargs: object) -> None:
        del event, kwargs

    def info(self, event: str, **kwargs: object) -> None:
        del event, kwargs

    def warning(self, event: str, **kwargs: object) -> None:
        del event, kwargs

    def error(self, event: str, **kwargs: object) -> None:
        del event, kwargs


def _discard_artifact(name: str, content: str) -> None:
    del name, content


@dataclass
class RunnerContext:
    """Ports and knobs the runner needs. Unused collaborators may be omitted."""

    clock: Clock
    sleeper: Sleeper
    gateway: AgentGateway
    probe: CapacityProbe
    store: RunStateStore
    control: RunControl
    catalog: ThreadCatalog | None = None
    lock: SessionLock | None = None
    write_artifact: Callable[[str, str], None] | None = None
    notifier: Notifier | None = None
    reporter: ProgressReporter | None = None
    budget: Budget = field(
        default_factory=lambda: Budget(max_turns=None, max_dollars=None, max_wall_clock=None)
    )
    wait_policy: AdaptiveWaitPolicy | None = None
    max_wait: timedelta | None = None
    logger: Logger | None = None
    handoff_marker_writer: Callable[[HandoffMarker], None] | None = None
    snapshot_sink: RunSnapshotSink | None = None
    event_sink: RunEventSink | None = None
    wind_down_policy: WindDownPolicy = field(default_factory=WindDownPolicy)
    run_id: str = "anonymous"
    cwd: str = "."
    model: str = "unknown"
    effort: Effort = Effort.MEDIUM


class AutonomousRunner:
    def __init__(self, ctx: RunnerContext) -> None:
        self._clock = ctx.clock
        self._sleeper = ctx.sleeper
        self._gateway = ctx.gateway
        self._probe = ctx.probe
        self._store = ctx.store
        self._control = ctx.control
        self._catalog = ctx.catalog
        self._lock = ctx.lock
        self._write_artifact = ctx.write_artifact or _discard_artifact
        self._notifier = ctx.notifier
        self._reporter = ctx.reporter
        self._budget = ctx.budget
        self._log = ctx.logger or _NullLogger()
        self._handoff_marker_writer = ctx.handoff_marker_writer
        self._snapshot_sink = ctx.snapshot_sink
        self._event_sink = ctx.event_sink
        self._wind_down_policy = ctx.wind_down_policy
        self._wait_policy = ctx.wait_policy or AdaptiveWaitPolicy(WaitConfig(), rand=lambda: 0.0)
        self._max_wait = ctx.max_wait
        self._run_id = ctx.run_id
        self._cwd = ctx.cwd
        self._model = ctx.model
        self._effort = ctx.effort
        self._approval = ApprovalPolicy.NEVER
        self._sandbox = SandboxMode.WORKSPACE_WRITE
        self._machine = RunLoopStateMachine()
        self._evaluator = CompletionEvaluator()
        self._ledger = BudgetLedger(ctx.budget)
        self._quota_notified = False
        self._queued_prompt: str | None = None

    async def run(self, selector: SessionSelector, plan: str) -> RunResult:
        thread_id = self._thread_id_from(selector)
        plan_text, remaining, first_turn = self._restore(thread_id, plan)
        if plan_text:
            parsed = WorkPlan.parse(plan_text)
            if not remaining:
                remaining = list(parsed.remaining_work)

        locked_id: str | None = None
        if self._lock is not None and thread_id is not None:
            if not self._lock.acquire(thread_id):
                await self._gateway.close()
                return RunResult(success=False, reason="lock", turns=0, thread_id=thread_id)
            locked_id = thread_id

        state = RunState.Preflight
        outcome = LoopOutcome(capacity=Available())
        started = self._clock.now()
        last_mark = started
        deadline = started + (self._max_wait if self._max_wait is not None else _FAR_FUTURE)
        wait_attempt = 0

        try:
            while True:
                controls = list(self._control.poll())
                await self._apply_controls(controls)
                now = self._clock.now()
                last_mark = self._record_elapsed(last_mark, now)

                if state is RunState.Preflight:
                    probed = await self._probe.probe()
                    outcome = LoopOutcome(
                        capacity=probed.outcome,
                        deadline_exceeded=now >= deadline,
                    )
                else:
                    outcome = replace(outcome, deadline_exceeded=now >= deadline)

                state, decision = self._machine.advance(state, outcome, now, self._ledger, controls)

                match decision:
                    case SendTurn():
                        default = plan_text if first_turn else _continuation(remaining)
                        prompt = self._take_prompt(default)
                        first_turn = False
                        turn = await self._gateway.send_turn(prompt)
                        if turn.thread_id:
                            thread_id = turn.thread_id
                            locked_id = self._maybe_lock(thread_id, locked_id)
                        last_mark = self._record_elapsed(last_mark, self._clock.now())
                        self._ledger.record(turns=1, dollars=turn.cost_dollars)
                        capacity, completion = _interpret(turn, self._evaluator)
                        self._report_unknown_code(turn)
                        if isinstance(completion, Continue) and isinstance(capacity, Available):
                            remaining = list(completion.remaining)
                        self._persist(
                            key=thread_id,
                            remaining=remaining,
                            first_turn_done=True,
                            plan_text=plan_text,
                        )
                        self._record_thread(thread_id, started)
                        wait_attempt = 0
                        self._quota_notified = False
                        outcome = LoopOutcome(
                            capacity=capacity,
                            completion=completion,
                            wind_down=self._project_wind_down(capacity),
                        )
                    case Probe():
                        probed = await self._probe.probe()
                        outcome = LoopOutcome(capacity=probed.outcome)
                    case WaitUntil() | BackoffUntil():
                        self._notify_quota_once(outcome.capacity)
                        until = self._wait_policy.next_probe_at(
                            outcome.capacity, self._clock.now(), wait_attempt, deadline
                        )
                        wait_attempt += 1
                        interrupt = await self._sleep_interruptible(until)
                        if interrupt == "stop":
                            # Stop immediately - drain will handle on next poll
                            pass
                        elif interrupt == "wind_down":
                            # Wind-down requested - continue to next poll to process it
                            pass
                    case Drain():
                        self._write_stop_summary(thread_id, remaining)
                        self._persist(
                            key=thread_id,
                            remaining=remaining,
                            first_turn_done=not first_turn,
                            plan_text=plan_text,
                        )
                    case WindDownAndFinish() as wound_down:
                        self._write_stop_summary(thread_id, remaining)
                        self._persist(
                            key=thread_id,
                            remaining=remaining,
                            first_turn_done=not first_turn,
                            plan_text=plan_text,
                            reason=f"wind-down: {wound_down.reason}",
                        )
                        self._write_handoff_marker(wound_down, thread_id, remaining)
                        self._emit_verdict(
                            success=False,
                            reason=f"wind-down: {wound_down.reason}",
                            thread_id=thread_id,
                            remaining=remaining,
                        )
                        return RunResult(
                            success=False,
                            reason=f"wind-down: {wound_down.reason}",
                            turns=self._ledger.turns,
                            thread_id=thread_id,
                        )
                    case Finish() as finish:
                        self._persist(
                            key=thread_id,
                            remaining=remaining,
                            first_turn_done=not first_turn,
                            plan_text=plan_text,
                            reason=finish.reason,
                        )
                        self._emit_verdict(
                            success=finish.success,
                            reason=finish.reason,
                            thread_id=thread_id,
                            remaining=remaining,
                        )
                        return RunResult(
                            success=finish.success,
                            reason=finish.reason,
                            turns=self._ledger.turns,
                            thread_id=thread_id,
                        )
                    case _:  # pragma: no cover — Decision is a closed union
                        assert_never(decision)
        finally:
            if locked_id is not None and self._lock is not None:
                self._lock.release(locked_id)
            await self._gateway.close()

    async def _apply_controls(self, controls: Sequence[ControlCommand]) -> None:
        for command in controls:
            match command:
                case Stop():
                    continue
                case WindDownCommand():
                    continue  # Handled by the state machine, not here
                case Prompt(text=text):
                    self._queued_prompt = text
                case SetModel(model=model):
                    self._model = model
                    profile = ModelEffortProfile(model=model, effort=self._effort)
                    await self._gateway.set_profile(profile)
                case SetEffort(effort=effort):
                    self._effort = effort
                    await self._gateway.set_profile(
                        ModelEffortProfile(model=self._model, effort=effort)
                    )
                case SetApproval(policy=policy):
                    self._approval = policy
                    await self._sync_permissions()
                case SetSandbox(sandbox=sandbox):
                    self._sandbox = sandbox
                    await self._sync_permissions()
                case SetCwd(cwd=cwd):
                    self._cwd = cwd
                    await self._gateway.set_cwd(cwd)
                case Snapshot():
                    self._write_artifact(
                        "snapshot.json",
                        (
                            f'{{"run_id":"{self._run_id}","model":"{self._model}",'
                            f'"effort":"{self._effort.value}","cwd":"{self._cwd}"}}\n'
                        ),
                    )
                case ResourceMutate(payload=payload):
                    await self._gateway.set_session_resources(payload)
                case _:  # pragma: no cover — ControlCommand is a closed union
                    assert_never(command)

    async def _sync_permissions(self) -> None:
        await self._gateway.set_permission_mode(_permission_mode(self._sandbox))
        await self._gateway.set_session_resources(
            {
                "approval_policy": self._approval.value,
                "sandbox_mode": self._sandbox.value,
            }
        )

    def _take_prompt(self, default: str) -> str:
        if self._queued_prompt is None:
            return default
        prompt = self._queued_prompt
        self._queued_prompt = None
        return prompt

    def _thread_id_from(self, selector: SessionSelector) -> str | None:
        match selector:
            case Explicit(thread_id=thread_id):
                return thread_id
            case MostRecent():
                return self._most_recent()
            case PlanFile():
                return None
            case _:  # pragma: no cover — SessionSelector is a closed union
                assert_never(selector)

    def _most_recent(self) -> str | None:
        if self._catalog is None:
            return None
        threads = list(self._catalog.list_threads())
        if not threads:
            return None
        latest = max(threads, key=lambda ref: ref.started_at)
        return latest.thread_id

    def _restore(self, thread_id: str | None, plan: str) -> tuple[str, list[str], bool]:
        if thread_id is None:
            return plan, [], True
        stored = self._store.load(thread_id)
        if stored is None:
            return plan, [], True
        plan_text = str(stored.get("plan_text") or plan)
        remaining_raw = stored.get("remaining_work") or []
        remaining = [str(item) for item in remaining_raw] if isinstance(remaining_raw, list) else []
        first_turn = not bool(stored.get("first_turn_done"))
        turns = _int_field(stored.get("turns"))
        dollars = _float_field(stored.get("dollars"))
        elapsed_s = _float_field(stored.get("elapsed_seconds"))
        if turns or dollars or elapsed_s:
            self._ledger.record(turns=turns, dollars=dollars, elapsed=timedelta(seconds=elapsed_s))
        return plan_text, remaining, first_turn

    def _maybe_lock(self, thread_id: str, locked_id: str | None) -> str | None:
        if self._lock is None or locked_id is not None:
            return locked_id
        if self._lock.acquire(thread_id):
            return thread_id
        return None

    def _record_elapsed(self, last_mark: datetime, now: datetime) -> datetime:
        delta = now - last_mark
        if delta > _ZERO:
            self._ledger.record(elapsed=delta)
        return now

    def _notify_quota_once(self, capacity: CapacityState) -> None:
        if not isinstance(capacity, QuotaExhausted) or self._quota_notified:
            return
        self._quota_notified = True
        if self._notifier is None:
            return
        self._notifier.notify("Quota exhausted", capacity.reason)

    def _report_unknown_code(self, turn: TurnOutcome) -> None:
        if self._reporter is None or turn.signals is None:
            return
        code = turn.signals.error_code
        if code is None:
            return
        if classify_code(code, None) is not ErrorClass.UNKNOWN:
            return
        self._reporter.report(
            "capacity.unknown_code",
            code=code,
            http_status=turn.signals.http_status,
        )

    def _emit_verdict(
        self,
        *,
        success: bool,
        reason: str | None,
        thread_id: str | None,
        remaining: Sequence[str],
    ) -> None:
        """Publish the run's terminal verdict to the event stream.

        The done marker is otherwise purely an INPUT -- the string this
        runner scans for in model output to decide completion. Nothing
        published it, so a reader of events.jsonl could not tell a
        completed run from an abandoned one without parsing meta.json.
        Emitting it on success closes that gap and matches what the rest
        of the loop family already publishes.
        """
        if self._event_sink is None:
            return
        payload: dict[str, object] = {
            "type": "run.verdict",
            "success": success,
            "complete": success,
            "reason": reason,
            "remaining_work": list(remaining),
        }
        if thread_id is not None:
            payload["thread_id"] = thread_id
        if success:
            payload["done_marker"] = DEFAULT_DONE_MARKER
        self._event_sink.emit(payload)

    def _persist(
        self,
        *,
        key: str | None,
        remaining: Sequence[str],
        first_turn_done: bool,
        plan_text: str,
        reason: str | None = None,
    ) -> None:
        run_id = key or self._run_id
        state: dict[str, object] = {
            "thread_id": key,
            "turns": self._ledger.turns,
            "dollars": self._ledger.dollars,
            "elapsed_seconds": self._ledger.elapsed.total_seconds(),
            "remaining_work": list(remaining),
            "first_turn_done": first_turn_done,
            "plan_text": plan_text,
        }
        if reason is not None:
            state["reason"] = reason
        self._store.save(run_id, state)
        # Same state, second destination: the run directory's
        # snapshots/latest.json, which external readers poll on a stable
        # path rather than parsing the event stream. session_id carries the
        # codex thread id so a reader can resume the right conversation.
        if self._snapshot_sink is not None:
            self._snapshot_sink.write({**state, "run_id": run_id, "session_id": key})

    def _record_thread(self, thread_id: str | None, started: datetime) -> None:
        if self._catalog is None or thread_id is None:
            return
        self._catalog.record(
            ThreadRef(
                thread_id=thread_id,
                cwd=self._cwd,
                started_at=started,
                model=self._model,
            )
        )

    def _write_stop_summary(self, thread_id: str | None, remaining: Sequence[str]) -> None:
        items = "\n".join(f"- {item}" for item in remaining) if remaining else "_none_"
        body = (
            "# Stop summary\n\n"
            "**Reason:** stop\n"
            f"**Thread:** `{thread_id or 'unknown'}`\n"
            f"**Turns:** {self._ledger.turns}\n\n"
            "## Remaining work\n\n"
            f"{items}\n"
        )
        self._write_artifact("stop-summary.md", body)

    def _project_wind_down(self, capacity: CapacityState) -> WindDown | None:
        """Forecast remaining capacity, but only while the vendor says we are
        not already blocked.

        Returning None for every non-Available state is what keeps the plan
        windows from ever influencing whether a turn is *sent*: once a real
        rejection lands, the state machine's capacity routing owns it.
        """
        if not isinstance(capacity, Available):
            return None
        now = self._clock.now()
        turns = self._ledger.turns
        projection = forecast(
            capacity,
            turns_spent=turns,
            max_turns=self._budget.max_turns,
            dollars_spent=self._ledger.dollars,
            max_dollars=self._budget.max_dollars,
            observed=BurnRate(
                turns=turns,
                elapsed_seconds=self._ledger.elapsed.total_seconds(),
                dollars=self._ledger.dollars,
            ),
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
        return should_wind_down(projection, self._wind_down_policy, turns_spent=turns)

    def _write_handoff_marker(
        self, decision: WindDownAndFinish, thread_id: str | None, remaining: list[str]
    ) -> None:
        """Written last, after the summary and state it names, so that a marker
        on disk means everything it points at is on disk."""
        if self._handoff_marker_writer is None:
            return
        binding = decision.forecast.binding
        self._handoff_marker_writer(
            HandoffMarker(
                run_id=self._run_id,
                reason=decision.reason,
                produced_at=self._clock.now(),
                headroom=binding.fraction,
                headroom_source=binding.source,
                resets_at=binding.resets_at,
                session_id=thread_id,
                turns_spent=self._ledger.turns,
                dollars_spent=self._ledger.dollars,
                remaining_work=tuple(remaining),
            )
        )

    async def _sleep_interruptible(self, until: datetime) -> None | Literal["stop", "wind_down"]:
        """Sleep until `until`, polling control inbox and returning early on stop/wind-down.

        Returns:
            None: sleep completed normally
            "stop": Stop command received
            "wind_down": WindDownCommand received
        """
        poll_interval = timedelta(seconds=1)

        while True:
            now = self._clock.now()
            if now >= until:
                return None

            # Poll control inbox for interrupts
            controls = self._control.poll()
            for cmd in controls:
                if isinstance(cmd, Stop):
                    return "stop"
                if isinstance(cmd, WindDownCommand):
                    return "wind_down"

            # Apply non-interrupt commands immediately
            await self._apply_controls(controls)

            # Sleep until next poll or target time, whichever is sooner
            next_poll = now + poll_interval
            sleep_until = min(next_poll, until)
            await self._sleeper.sleep_until(sleep_until)


def _permission_mode(sandbox: SandboxMode) -> PermissionMode:
    match sandbox:
        case SandboxMode.READ_ONLY:
            return PermissionMode.READ_ONLY
        case SandboxMode.DANGER_FULL_ACCESS:
            return PermissionMode.FULL_ACCESS
        case SandboxMode.WORKSPACE_WRITE:
            return PermissionMode.AUTONOMOUS
        case _:  # pragma: no cover — exhaustive StrEnum
            assert_never(sandbox)


def _continuation(remaining: Sequence[str]) -> str:
    if remaining:
        items = "\n".join(f"- {name}" for name in remaining)
        body = f"Continue. Remaining work:\n{items}"
    else:
        body = "Continue."
    return (
        f"{body}\n\n"
        "When the entire task is fully complete, output "
        f"{DEFAULT_DONE_MARKER} on its own line."
    )


def _interpret(
    turn: TurnOutcome, evaluator: CompletionEvaluator
) -> tuple[CapacityState, CompletionVerdict]:
    if turn.signals is None:
        return Available(), Continue(remaining=[])
    capacity = classify(turn.signals)
    completion = evaluator.evaluate(turn.signals, capacity)
    if isinstance(capacity, Available) and _is_fatal_turn(turn.signals):
        reason = (
            turn.signals.error_code
            or turn.signals.error_type
            or ("turn_failed" if turn.signals.failed else "fatal")
        )
        return capacity, Blocked(reason=reason)
    return capacity, completion


def _is_fatal_turn(signals: TurnSignals) -> bool:
    if classify_code(signals.error_code, None) is ErrorClass.FATAL:
        return True
    if classify_code(None, signals.error_type) is ErrorClass.FATAL:
        return True
    return signals.failed


def _int_field(value: object) -> int:
    if isinstance(value, int):
        return value
    return 0


def _float_field(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0


__all__ = ["AutonomousRunner", "RunnerContext"]

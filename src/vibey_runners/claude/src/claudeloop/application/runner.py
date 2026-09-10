# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""AutonomousRunner — executes domain.loop's pure Decisions against real ports.

Contains NO capacity or completion logic of its own. Every "is this waitable",
"how long do we wait", "is the task done" question is answered by domain/ before
this class ever sees it; this class only performs the I/O domain/loop.py decided
was needed and feeds the result back in."""

from __future__ import annotations

import contextlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from claudeloop.application.dto import RunResult, TurnOutcome
from claudeloop.application.ports import (
    AgentGateway,
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
    StreamUi,
)
from claudeloop.domain.budget import Budget, BudgetLedger
from claudeloop.domain.capacity import Available, CapacityState, CreditsExhausted
from claudeloop.domain.chatter import chatter_event_payload
from claudeloop.domain.classify import classify
from claudeloop.domain.completion import Blocked, CompletionVerdict, Continue, Done, evaluate
from claudeloop.domain.control import (
    ApproveToolCommand,
    ControlCommand,
    DenyToolCommand,
    PromptDeferredCommand,
    PromptNowCommand,
    ResourceMutateCommand,
    ResponseFeedbackCommand,
    ResponseRetryCommand,
    SetCwdCommand,
    SetEffortCommand,
    SetModelCommand,
    SetPermissionModeCommand,
    SetPresetCommand,
    SlashCommand,
    StopCommand,
    WindDownCommand,
)
from claudeloop.domain.forecast import (
    BurnRate,
    CapacityForecast,
    Headroom,
    WindDown,
    WindDownPolicy,
    forecast,
    should_wind_down,
)
from claudeloop.domain.handoff_marker import HandoffMarker
from claudeloop.domain.loop import (
    DelayThenSend,
    Finish,
    Phase,
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
from claudeloop.domain.model_policy import decide_auto_model
from claudeloop.domain.model_profile import (
    ModelAliases,
    ModelEffortProfile,
    parse_effort,
    resolve_profile,
)
from claudeloop.domain.permission import (
    DEFAULT_USER_PERMISSION_MODE,
    parse_user_permission_mode,
)
from claudeloop.domain.plan import WorkPlan
from claudeloop.domain.slash import parse_slash, slash_to_prompt
from claudeloop.domain.snapshot import SnapshotReason, SnapshotRef
from claudeloop.domain.stop_summary import StopSummaryInput, render_stop_summary
from claudeloop.domain.waiting import (
    DEFAULT_PROGRESS_WAIT_CONFIG,
    DEFAULT_WAIT_POLICY_CONFIG,
    ProgressWaitConfig,
    WaitPolicyConfig,
)

_DEFAULT_BUDGET = Budget()
_SLEEP_CHUNK = timedelta(seconds=5)


class _NullNotifier:
    def notify(self, message: str) -> None:
        del message


class _NullRunControl:
    def poll(self) -> list[ControlCommand]:
        return []


class _NullEventSink:
    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        del event_type, payload

    def bind(
        self,
        *,
        session_id: str | None = None,
        attempt: int | None = None,
        phase: str | None = None,
        trace_id: str | None = None,
        turn_id: str | None = None,
    ) -> None:
        del session_id, attempt, phase, trace_id, turn_id


class _NullStreamUi:
    def on_delta(self, text: str, *, turn_id: str, seq: int) -> None:
        del text, turn_id, seq

    def on_turn_boundary(self, *, turn_id: str, attempt: int) -> None:
        del turn_id, attempt

    def on_prompt(self, text: str) -> None:
        del text

    def on_assistant(self, text: str) -> None:
        del text

    def on_tool(self, name: str, summary: str) -> None:
        del name, summary

    def on_status(self, state: dict[str, Any]) -> None:
        del state

    def close(self) -> None:
        return None


class _NullStateStore:
    def save(self, run_id: str, state: dict[str, Any]) -> None:
        del run_id, state

    def load(self, run_id: str) -> dict[str, Any] | None:
        del run_id
        return None


class _NullSessionLock:
    def acquire(self, session_id: str) -> bool:
        del session_id
        return True

    def release(self, session_id: str) -> None:
        del session_id


class _NullSavePointStore:
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

    def list_points(self, run_id: str) -> list[Any]:
        del run_id
        return []

    def unwind(self, *, run_id: str, to: str, backup: bool) -> Any:
        raise RuntimeError("save points not configured")

    def changes_since(self, since_sha: str | None) -> str:
        del since_sha
        return ""


class _NullStateBus:
    def publish(self, event_type: str, state: dict[str, Any]) -> None:
        del event_type, state


class _NullSnapshotSink:
    def emit(
        self,
        reason: SnapshotReason,
        *,
        context: dict[str, Any] | None = None,
        bundle: bool | None = None,
    ) -> None:
        del reason, context, bundle
        return None


class _NullRunResources:
    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]:
        del action, kind, value, name
        return {}

    def gateway_payload(self) -> dict[str, Any]:
        return {}

    def set_permission_mode(self, mode: str) -> None:
        del mode

    def set_cwd(self, path: str) -> None:
        del path


class _NullLogger:
    def bind(self, **kwargs: Any) -> _NullLogger:
        del kwargs
        return self

    def debug(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def info(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def warning(self, event: str, **kwargs: Any) -> None:
        del event, kwargs

    def error(self, event: str, **kwargs: Any) -> None:
        del event, kwargs


class AutonomousRunner:
    def __init__(
        self,
        *,
        agent_gateway: AgentGateway,
        capacity_probe: CapacityProbe,
        clock: Clock,
        sleeper: Sleeper,
        audit_log: AuditLog,
        progress: ProgressReporter,
        budget: Budget = _DEFAULT_BUDGET,
        wait_policy: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
        progress_wait: ProgressWaitConfig = DEFAULT_PROGRESS_WAIT_CONFIG,
        done_marker: str | None = None,
        run_id: str = "anonymous",
        notifier: Notifier | None = None,
        run_control: RunControl | None = None,
        event_sink: RunEventSink | None = None,
        state_store: RunStateStore | None = None,
        session_lock: SessionLock | None = None,
        save_points: SavePointStore | None = None,
        plan: WorkPlan | None = None,
        stop_summary_writer: Any | None = None,
        handoff_marker_writer: Any | None = None,
        wind_down_policy: WindDownPolicy | None = None,
        wind_down_at: datetime | None = None,
        meta_updater: Any | None = None,
        events_path: str = "",
        state_bus: StateBus | None = None,
        logger: Logger | None = None,
        trace_id: str | None = None,
        profile: ModelEffortProfile | None = None,
        aliases: ModelAliases | None = None,
        auto_model: bool = True,
        log_chatter: str = "summary",
        stream_ui: StreamUi | None = None,
        max_dollars: float | None = None,
        run_resources: RunResources | None = None,
        permission_mode: str = DEFAULT_USER_PERMISSION_MODE,
        snapshot_sink: RunSnapshotSink | None = None,
        known_session_id: str | None = None,
    ) -> None:
        self._gateway = agent_gateway
        self._probe = capacity_probe
        self._clock = clock
        self._sleeper = sleeper
        self._audit = audit_log
        self._progress = progress
        self._budget = budget
        self._wait_policy = wait_policy
        self._progress_wait = progress_wait
        self._done_marker = done_marker
        self._run_id = run_id
        self._notifier = notifier or _NullNotifier()
        self._control = run_control or _NullRunControl()
        self._events = event_sink or _NullEventSink()
        self._state_store = state_store or _NullStateStore()
        self._session_lock = session_lock or _NullSessionLock()
        self._save_points = save_points or _NullSavePointStore()
        self._plan = plan
        self._stop_summary_writer = stop_summary_writer
        self._handoff_marker_writer = handoff_marker_writer
        self._wind_down_policy = wind_down_policy or WindDownPolicy()
        self._wind_down_at = wind_down_at
        self._last_resets_at: datetime | None = None
        self._wind_down_requested: str | None = None
        self._meta_updater = meta_updater
        self._events_path = events_path
        self._state_bus = state_bus or _NullStateBus()
        self._trace_id = trace_id or str(uuid.uuid4())
        self._aliases = aliases or ModelAliases()
        self._profile = profile or resolve_profile(aliases=self._aliases)
        self._auto_model = auto_model
        self._log_chatter = log_chatter
        self._stream_ui = stream_ui or _NullStreamUi()
        self._max_dollars = max_dollars if max_dollars is not None else budget.max_dollars
        self._resources = run_resources or _NullRunResources()
        self._permission_mode = parse_user_permission_mode(permission_mode)
        self._snapshots = snapshot_sink or _NullSnapshotSink()
        self._known_session_id = known_session_id
        self._log = (logger or _NullLogger()).bind(
            run_id=run_id,
            component="runner",
            trace_id=self._trace_id,
        )
        self._prompt_now: str | None = None
        self._prompt_deferred: str | None = None
        self._stop_requested = False
        self._last_summary = ""
        self._last_remaining_work: tuple[str, ...] = ()
        self._last_sent_prompt: str | None = None
        self._last_output_text: str = ""
        self._credits_notified = False
        self._sticky_credits = False
        self._empty_turn_streak = 0
        self._progress_wait_streak = 0
        self._last_savepoint_sha: str | None = None
        self._prev_savepoint_sha: str | None = None
        self._last_tree_changed = True
        self._lock_token: str | None = None
        self._first_savepoint_sha: str | None = None
        self._pending_profile: ModelEffortProfile | None = None
        self._pending_permission_mode: str | None = None
        self._pending_cwd: str | None = None
        self._pending_resources = False
        self._operator_locked = False
        self._consecutive_no_progress = 0
        self._consecutive_progress = 0
        self._budget_downgrade_done = False
        self._delta_seq = 0
        self._last_completion: CompletionVerdict | None = None
        self._last_capacity_name: str | None = None

    async def run(self, *, initial_prompt: str, continue_prompt: str) -> RunResult:
        """Drive one run to completion: send `initial_prompt` first, then
        `continue_prompt` on every subsequent SendTurn (unless an injected
        prompt is pending)."""
        state = start(BudgetLedger(budget=self._budget))
        session_id: str | None = self._known_session_id
        first_turn = True
        attempt = 0
        self._log.info(
            "run.started",
            initial_prompt_len=len(initial_prompt),
            continue_prompt_len=len(continue_prompt),
            model=self._profile.model,
            effort=self._profile.effort,
            preset=self._profile.preset,
        )
        self._events.bind(phase=state.phase.name, trace_id=self._trace_id)
        self._events.emit(
            "run.started",
            {
                "run_id": self._run_id,
                "trace_id": self._trace_id,
                "model": self._profile.model,
                "effort": self._profile.effort,
            },
        )
        self._update_meta(
            model=self._profile.model,
            effort=self._profile.effort,
            preset=self._profile.preset,
        )
        self._emit_snapshot("started", session_id=session_id, attempt=0, state=state)

        try:
            # Resume (and any other path that already knows the Claude session id)
            # must take the advisory lock *before* the first send_turn. Acquiring
            # after the first turn is too late: two `claudeloop resume` processes
            # can both drive the same session and corrupt it. Fail closed when
            # another runner already holds the lock.
            if session_id is not None and not self._acquire_session_lock(session_id):
                return await self._finish_lock_contention(state, session_id=session_id)

            preflight_outcome = await self._probe.probe()
            capacity = self._verdict_capacity(preflight_outcome)
            self._last_capacity_name = type(capacity).__name__
            self._log.info(
                "preflight.completed",
                capacity=type(capacity).__name__,
            )
            state, decision = decide_preflight(
                state,
                capacity,
                now=self._clock.now(),
                config=self._wait_policy,
            )
            self._maybe_notify_credits(capacity)
            self._audit.record(
                "preflight",
                {"phase": state.phase.name, "run_id": self._run_id},
            )
            self._events.emit("preflight", {"phase": state.phase.name})
            self._persist(state, session_id=session_id, attempt=attempt)
            self._log.debug(
                "decision.after_preflight",
                decision=type(decision).__name__,
                phase=state.phase.name,
            )

            while True:
                self._apply_control(self._control.poll(), natural_break=False)
                if self._stop_requested:
                    self._log.info("run.stopping", reason="stopped by operator")
                    return await self._finish_stopped(
                        state, session_id=session_id, reason="stopped by operator"
                    )

                if isinstance(decision, SendTurn):
                    attempt += 1
                    turn_id = str(uuid.uuid4())
                    await self._flush_pending_session_updates()
                    ledger = state.ledger.spend_attempt()
                    state = RunState(
                        phase=state.phase,
                        ledger=ledger,
                        started_waiting_at=state.started_waiting_at,
                        probe_count=state.probe_count,
                        failure_reason=state.failure_reason,
                    )
                    prompt = self._next_prompt(
                        initial_prompt=initial_prompt,
                        continue_prompt=continue_prompt,
                        first_turn=first_turn,
                    )
                    self._last_sent_prompt = prompt
                    first_turn = False
                    self._progress.turn_sent(attempt=attempt)
                    self._events.bind(
                        attempt=attempt,
                        phase=state.phase.name,
                        turn_id=turn_id,
                        trace_id=self._trace_id,
                    )
                    self._stream_ui.on_turn_boundary(turn_id=turn_id, attempt=attempt)
                    self._events.emit("turn.starting", {"prompt_preview": prompt[:200]})
                    self._stream_ui.on_prompt(prompt)
                    self._emit_chatter("chatter.prompt", prompt)
                    self._update_meta(phase=state.phase.name, attempt=attempt)
                    self._log.info(
                        "turn.starting",
                        attempt=attempt,
                        turn_id=turn_id,
                        prompt_len=len(prompt),
                        prompt_preview=prompt[:200],
                        model=self._profile.model,
                        effort=self._profile.effort,
                    )

                    outcome = await self._gateway.send_turn(prompt)
                    self._last_output_text = outcome.output_text or ""
                    session_id = outcome.session_id or session_id
                    if session_id:
                        self._update_meta(session_id=session_id)
                    if (
                        session_id
                        and self._lock_token is None
                        and not self._acquire_session_lock(session_id)
                    ):
                        return await self._finish_lock_contention(state, session_id=session_id)
                    self._events.bind(session_id=session_id)
                    capacity = classify(outcome.signals)
                    self._last_capacity_name = type(capacity).__name__
                    if isinstance(capacity, CreditsExhausted):
                        self._sticky_credits = True
                    elif isinstance(capacity, Available):
                        self._sticky_credits = False
                    verdict = self._completion_verdict(outcome)
                    if (
                        isinstance(verdict, Continue)
                        and not (outcome.output_text or "").strip()
                        and outcome.cost_usd <= 0.0
                        and outcome.verdict is None
                    ):
                        self._empty_turn_streak += 1
                    else:
                        self._empty_turn_streak = 0
                    remaining_before = self._remaining_count()
                    self._remember_verdict(verdict)
                    self._reconcile_plan(verdict)
                    remaining_after = self._remaining_count()
                    self._update_progress_counters(
                        verdict,
                        remaining_before=remaining_before,
                        remaining_after=remaining_after,
                    )
                    self._stream_ui.on_assistant(outcome.output_text)
                    self._emit_chatter("chatter.assistant", outcome.output_text)
                    self._maybe_notify_credits(capacity)
                    self._audit.record(
                        "turn",
                        {
                            "attempt": attempt,
                            "capacity": type(capacity).__name__,
                            "cost_usd": outcome.cost_usd,
                            "run_id": self._run_id,
                            "session_id": session_id,
                            "trace_id": self._trace_id,
                            "turn_id": turn_id,
                            "model": self._profile.model,
                            "effort": self._profile.effort,
                        },
                    )
                    self._events.emit(
                        "turn.completed",
                        {
                            "capacity": type(capacity).__name__,
                            "cost_usd": outcome.cost_usd,
                            "verdict": type(verdict).__name__,
                            "model": self._profile.model,
                            "effort": self._profile.effort,
                        },
                    )
                    self._log.info(
                        "turn.completed",
                        attempt=attempt,
                        turn_id=turn_id,
                        capacity=type(capacity).__name__,
                        verdict=type(verdict).__name__,
                        cost_usd=outcome.cost_usd,
                        session_id=session_id,
                    )

                    self._create_savepoint(
                        label=f"turn-{attempt}",
                        attempt=attempt,
                        verdict=verdict,
                        summary=(
                            outcome.verdict.summary
                            if outcome.verdict is not None
                            else self._last_summary
                        ),
                    )

                    now = self._clock.now()
                    projection = self._project_capacity(state, capacity=capacity, now=now)
                    wind_down = (
                        should_wind_down(
                            projection,
                            self._wind_down_policy,
                            turns_spent=state.ledger.turns_spent + 1,
                        )
                        if projection is not None
                        else None
                    )
                    if (
                        wind_down is None
                        and self._wind_down_at is not None
                        and now >= self._wind_down_at
                    ):
                        # Deadline-driven wind-down.
                        wind_down = WindDown(
                            reason="deadline",
                            forecast=projection
                            or CapacityForecast(
                                binding=Headroom(None, "unknown"),
                                dimensions=(Headroom(None, "unknown"),),
                                turns_until_exhaustion=None,
                                seconds_until_reset=None,
                            ),
                        )
                    if wind_down is None and self._wind_down_requested is not None:
                        # An operator asking for a handoff does not need the
                        # policy enabled, and does not need any headroom to be
                        # low. It is a decision, not a prediction.
                        wind_down = WindDown(
                            reason=f"operator:{self._wind_down_requested}",
                            forecast=projection
                            or CapacityForecast(
                                binding=Headroom(None, "unknown"),
                                dimensions=(Headroom(None, "unknown"),),
                                turns_until_exhaustion=None,
                                seconds_until_reset=None,
                            ),
                        )
                    state, decision = decide_after_turn(
                        state,
                        capacity=capacity,
                        verdict=verdict,
                        now=now,
                        config=self._wait_policy,
                        dollars=outcome.cost_usd,
                        wind_down=wind_down,
                    )
                    if (
                        isinstance(decision, SendTurn)
                        and isinstance(verdict, Continue)
                        and isinstance(capacity, Available)
                    ):
                        delay = decide_progress_delay(
                            verdict=verdict,
                            tree_changed=self._last_tree_changed,
                            now=self._clock.now(),
                            streak=self._progress_wait_streak,
                            config=self._progress_wait,
                        )
                        if delay is not None:
                            decision = delay
                            self._progress_wait_streak += 1
                        else:
                            self._progress_wait_streak = 0
                    self._consider_auto_model(state)
                    self._persist(state, session_id=session_id, attempt=attempt)
                    self._log.debug(
                        "decision.after_turn",
                        decision=type(decision).__name__,
                        phase=state.phase.name,
                    )

                    # Natural break: Continue + about to SendTurn again
                    if isinstance(decision, SendTurn) and isinstance(verdict, Continue):
                        self._apply_control(self._control.poll(), natural_break=True)
                        if self._stop_requested:
                            self._log.info(
                                "run.stopping",
                                reason="stopped by operator",
                                at="natural_break",
                            )
                            return await self._finish_stopped(
                                state,
                                session_id=session_id,
                                reason="stopped by operator",
                            )

                elif isinstance(decision, DelayThenSend):
                    self._events.emit(
                        "progress.wait",
                        {
                            "until": decision.at.isoformat(),
                            "streak": self._progress_wait_streak,
                        },
                    )
                    self._log.info(
                        "progress.wait",
                        until=decision.at.isoformat(),
                        streak=self._progress_wait_streak,
                    )
                    self._update_meta(
                        phase=state.phase.name,
                        attempt=attempt,
                        waiting_until=decision.at.isoformat(),
                    )
                    stopped = await self._sleep_interruptible(decision.at)
                    if stopped:
                        self._log.info(
                            "run.stopping",
                            reason="stopped by operator during progress wait",
                        )
                        return await self._finish_stopped(
                            state,
                            session_id=session_id,
                            reason="stopped by operator during progress wait",
                        )
                    self._update_meta(waiting_until=None)
                    decision = SendTurn()

                elif isinstance(decision, ScheduleProbe):
                    self._progress.waiting(reason=state.phase.name, until=decision.at)
                    self._audit.record(
                        "waiting",
                        {
                            "until": decision.at.isoformat(),
                            "run_id": self._run_id,
                        },
                    )
                    self._events.emit(
                        "waiting",
                        {"until": decision.at.isoformat(), "phase": state.phase.name},
                    )
                    self._log.info(
                        "waiting.scheduled",
                        until=decision.at.isoformat(),
                        phase=state.phase.name,
                        probe_count=state.probe_count,
                    )
                    self._update_meta(
                        status="waiting",
                        phase=state.phase.name,
                        attempt=attempt,
                        waiting_until=decision.at.isoformat(),
                        capacity=self._last_capacity_name,
                    )
                    self._emit_snapshot(
                        "waiting",
                        session_id=session_id,
                        attempt=attempt,
                        state=state,
                        waiting_until=decision.at.isoformat(),
                    )
                    stopped = await self._sleep_interruptible(decision.at)
                    if stopped:
                        self._log.info(
                            "run.stopping",
                            reason="stopped by operator during wait",
                        )
                        return await self._finish_stopped(
                            state,
                            session_id=session_id,
                            reason="stopped by operator during wait",
                        )
                    probe_outcome = await self._probe.probe()
                    capacity = self._verdict_capacity(probe_outcome)
                    self._last_capacity_name = type(capacity).__name__
                    self._maybe_notify_credits(capacity)
                    self._events.emit(
                        "probe",
                        {
                            "capacity": type(capacity).__name__,
                            "sticky_credits": self._sticky_credits,
                        },
                    )
                    self._log.info(
                        "probe.completed",
                        capacity=type(capacity).__name__,
                        sticky_credits=self._sticky_credits,
                    )
                    if isinstance(capacity, Available):
                        # Probe Available alone does not clear sticky credits —
                        # only a successful real turn does. Still attempt SendTurn
                        # so a real top-up can be verified on the run's model.
                        if self._sticky_credits:
                            self._events.emit(
                                "capacity.probe_available",
                                {
                                    "probe_count": state.probe_count,
                                    "sticky_credits": True,
                                },
                            )
                        else:
                            self._events.emit(
                                "capacity.restored",
                                {"probe_count": state.probe_count},
                            )
                            self._log.info(
                                "capacity.restored",
                                probe_count=state.probe_count,
                            )
                    state, decision = decide_after_probe(
                        state,
                        capacity,
                        now=self._clock.now(),
                        config=self._wait_policy,
                    )
                    self._persist(state, session_id=session_id, attempt=attempt)
                    # Persist already derived waiting/failed/finished; only clear the
                    # wait clock and mark active when we are about to send a real turn.
                    if isinstance(decision, SendTurn):
                        self._update_meta(waiting_until=None, status="active")
                    elif isinstance(decision, ScheduleProbe):
                        self._update_meta(
                            waiting_until=decision.at.isoformat(),
                            status="waiting",
                        )
                    else:
                        self._update_meta(waiting_until=None)
                    self._log.debug(
                        "decision.after_probe",
                        decision=type(decision).__name__,
                        phase=state.phase.name,
                    )
                else:
                    # RunProbe is a declared member of domain.loop.Decision but no
                    # decide_* function currently produces it standalone — probing
                    # is folded into the ScheduleProbe branch above (schedule, wait,
                    # then probe). Same unreachable-by-construction pattern as
                    # domain.loop.Phase.PROBING; see that module's own exhaustiveness
                    # asserts for the precedent this follows.
                    if isinstance(decision, WindDownAndFinish):
                        return await self._finish_wound_down(
                            state, session_id=session_id, decision=decision
                        )
                    assert isinstance(decision, Finish)  # nosec B101
                    await self._gateway.close()
                    self._progress.finished(success=decision.success, reason=decision.reason)
                    self._audit.record(
                        "finished",
                        {
                            "success": decision.success,
                            "reason": decision.reason,
                            "run_id": self._run_id,
                            "session_id": session_id,
                        },
                    )
                    self._events.emit(
                        "finished",
                        {"success": decision.success, "reason": decision.reason},
                    )
                    self._log.info(
                        "run.finished",
                        success=decision.success,
                        reason=decision.reason,
                        turns_spent=state.ledger.turns_spent,
                        dollars_spent=state.ledger.dollars_spent,
                        session_id=session_id,
                    )
                    self._update_meta(
                        status="finished" if decision.success else "failed",
                        phase=Phase.COMPLETE.name if decision.success else Phase.FAILED.name,
                        session_id=session_id,
                        capacity=self._last_capacity_name,
                        model=self._profile.model,
                        effort=self._profile.effort,
                        preset=self._profile.preset,
                    )
                    self._persist(state, session_id=session_id, attempt=attempt)
                    self._emit_snapshot(
                        "finished" if decision.success else "failed",
                        session_id=session_id,
                        attempt=attempt,
                        state=state,
                        status="finished" if decision.success else "failed",
                        bundle=True,
                    )
                    self._release_lock()
                    self._stream_ui.close()
                    return RunResult(
                        success=decision.success,
                        reason=decision.reason,
                        session_id=session_id,
                        turns_spent=state.ledger.turns_spent,
                        dollars_spent=state.ledger.dollars_spent,
                    )
        except BaseException as exc:
            self._log.error("run.exception", error=type(exc).__name__, detail=str(exc)[:500])
            with contextlib.suppress(Exception):
                self._update_meta(
                    status="failed",
                    phase=Phase.FAILED.name,
                    capacity=self._last_capacity_name,
                )
            self._release_lock()
            with contextlib.suppress(Exception):  # pragma: no cover - best-effort cleanup
                await self._gateway.close()
            raise

    def _next_prompt(self, *, initial_prompt: str, continue_prompt: str, first_turn: bool) -> str:
        if self._prompt_now is not None:
            prompt = self._prompt_now
            self._prompt_now = None
            self._events.emit("control.prompt_now_applied", {})
            return prompt
        if not first_turn and self._prompt_deferred is not None:
            # Deferred only applied at natural break (Continue path sets it
            # via _apply_control(..., natural_break=True) into _prompt_now).
            pass
        if first_turn:
            return initial_prompt
        return continue_prompt

    def _apply_control(self, commands: list[ControlCommand], *, natural_break: bool) -> None:
        if commands:
            self._log.debug(
                "control.poll",
                count=len(commands),
                natural_break=natural_break,
                types=[type(c).__name__ for c in commands],
            )
        for command in commands:
            if isinstance(command, StopCommand):
                self._stop_requested = True
                self._events.emit("control.stop", {})
                self._log.info("control.stop")
                return
            if isinstance(command, WindDownCommand):
                # Held, not dropped. A soft stop that arrives mid-turn has to
                # survive until the next natural break -- discarding it would
                # make the command silently depend on poll timing.
                self._wind_down_requested = command.reason
                self._events.emit("control.wind_down", {"reason": command.reason})
                self._log.info(
                    "control.wind_down", reason=command.reason, natural_break=natural_break
                )
                continue
            if isinstance(command, PromptNowCommand):
                self._prompt_now = command.text
                self._events.emit("control.prompt_now", {"length": len(command.text)})
                self._log.info("control.prompt_now", length=len(command.text))
                continue
            if isinstance(command, PromptDeferredCommand):
                if natural_break:
                    self._prompt_now = command.text
                    self._prompt_deferred = None
                    self._events.emit(
                        "control.prompt_deferred_applied",
                        {"length": len(command.text)},
                    )
                    self._log.info(
                        "control.prompt_deferred_applied",
                        length=len(command.text),
                    )
                else:
                    self._prompt_deferred = command.text
                    self._events.emit(
                        "control.prompt_deferred_queued",
                        {"length": len(command.text)},
                    )
                    self._log.info(
                        "control.prompt_deferred_queued",
                        length=len(command.text),
                    )
                continue
            if isinstance(command, SetPresetCommand):
                self._queue_profile(
                    resolve_profile(preset=command.preset, aliases=self._aliases),
                    operator=True,
                )
                continue
            if isinstance(command, SetModelCommand):
                self._queue_profile(
                    resolve_profile(
                        model=command.model,
                        effort=self._profile.effort,
                        aliases=self._aliases,
                    ),
                    operator=True,
                )
                continue
            if isinstance(command, SetEffortCommand):
                self._queue_profile(
                    ModelEffortProfile(
                        model=self._profile.model,
                        effort=parse_effort(command.effort),
                        preset=self._profile.preset,
                    ),
                    operator=True,
                )
                continue
            if isinstance(command, SetPermissionModeCommand):
                mode = parse_user_permission_mode(command.mode)
                self._pending_permission_mode = mode
                self._resources.set_permission_mode(mode)
                self._events.emit("control.permission_mode", {"mode": mode})
                self._log.info("control.permission_mode", mode=mode)
                continue
            if isinstance(command, SetCwdCommand):
                self._pending_cwd = command.path
                self._resources.set_cwd(command.path)
                self._events.emit("control.cwd", {"path": command.path})
                self._log.info("control.cwd", path=command.path)
                continue
            if isinstance(command, SlashCommand):
                parsed = parse_slash(command.text)
                self._prompt_now = slash_to_prompt(parsed)
                self._events.emit(
                    "control.slash",
                    {"name": parsed.name, "args": parsed.args},
                )
                self._log.info("control.slash", name=parsed.name)
                continue
            if isinstance(command, ApproveToolCommand):
                ok = self._gateway.resolve_tool_approval(command.request_id, allow=True)
                self._events.emit(
                    "tool.approved",
                    {"request_id": command.request_id, "ok": ok},
                )
                continue
            if isinstance(command, DenyToolCommand):
                ok = self._gateway.resolve_tool_approval(
                    command.request_id, allow=False, reason=command.reason
                )
                self._events.emit(
                    "tool.denied",
                    {
                        "request_id": command.request_id,
                        "reason": command.reason,
                        "ok": ok,
                    },
                )
                continue
            if isinstance(command, ResourceMutateCommand):
                result = self._resources.apply_mutate(
                    action=command.action,
                    kind=command.kind,
                    value=command.value,
                    name=command.name,
                )
                self._pending_resources = True
                fragment = result.get("prompt_fragment")
                if isinstance(fragment, str) and fragment.strip():
                    self._prompt_deferred = (
                        f"{self._prompt_deferred}\n\n{fragment}"
                        if self._prompt_deferred
                        else fragment
                    )
                self._events.emit(
                    "control.resource",
                    {
                        "action": command.action,
                        "kind": command.kind,
                        "result": {k: v for k, v in result.items() if k != "prompt_fragment"},
                    },
                )
                self._log.info(
                    "control.resource",
                    action=command.action,
                    kind=command.kind,
                )
                continue
            if isinstance(command, ResponseFeedbackCommand):
                self._events.emit(
                    "response.feedback",
                    {"verdict": command.verdict, "note": command.note},
                )
                self._audit.record(
                    "response.feedback",
                    {"verdict": command.verdict, "note": command.note},
                )
                continue
            if isinstance(command, ResponseRetryCommand):
                if self._last_sent_prompt:
                    self._prompt_now = self._last_sent_prompt
                    self._events.emit(
                        "response.retry",
                        {"length": len(self._last_sent_prompt)},
                    )
                    self._log.info("response.retry", length=len(self._last_sent_prompt))
                else:
                    self._events.emit("response.retry_empty", {})
                continue

        # Promote deferred → now only at natural break
        if natural_break and self._prompt_deferred is not None and self._prompt_now is None:
            self._prompt_now = self._prompt_deferred
            self._prompt_deferred = None
            self._events.emit("control.prompt_deferred_applied", {})
            self._log.info("control.prompt_deferred_promoted")

    def _queue_profile(self, profile: ModelEffortProfile, *, operator: bool) -> None:
        self._pending_profile = profile
        if operator:
            self._operator_locked = True
        self._events.emit(
            "model.profile_queued",
            {
                "model": profile.model,
                "effort": profile.effort,
                "preset": profile.preset,
                "operator": operator,
            },
        )
        self._log.info(
            "model.profile_queued",
            model=profile.model,
            effort=profile.effort,
            preset=profile.preset,
            operator=operator,
        )

    async def _flush_pending_session_updates(self) -> None:
        await self._flush_pending_profile()
        if self._pending_permission_mode is not None:
            mode = self._pending_permission_mode
            self._pending_permission_mode = None
            await self._gateway.set_permission_mode(mode)
            self._permission_mode = parse_user_permission_mode(mode)
            self._events.emit("permission.mode_changed", {"mode": mode})
            self._log.info("permission.mode_changed", mode=mode)
        if self._pending_cwd is not None:
            cwd = self._pending_cwd
            self._pending_cwd = None
            await self._gateway.set_cwd(cwd)
            if self._meta_updater is not None:
                self._meta_updater(cwd=cwd)
            self._events.emit("cwd.changed", {"cwd": cwd})
            self._log.info("cwd.changed", cwd=cwd)
        if self._pending_resources:
            self._pending_resources = False
            payload = self._resources.gateway_payload()
            await self._gateway.set_session_resources(**payload)
            self._events.emit("session.resources_applied", {"keys": sorted(payload.keys())})

    async def _flush_pending_profile(self) -> None:
        if self._pending_profile is None:
            return
        profile = self._pending_profile
        self._pending_profile = None
        await self._gateway.set_profile(profile)
        self._profile = profile
        set_model = getattr(self._probe, "set_model", None)
        if callable(set_model):
            set_model(profile.model)
        self._events.emit(
            "model.profile_changed",
            {
                "model": profile.model,
                "effort": profile.effort,
                "preset": profile.preset,
            },
        )
        self._log.info(
            "model.profile_changed",
            model=profile.model,
            effort=profile.effort,
            preset=profile.preset,
        )
        self._stream_ui.on_status(
            {
                "model": profile.model,
                "effort": profile.effort,
                "preset": profile.preset,
            }
        )

    def _emit_chatter(self, event_type: str, text: str, **extra: Any) -> None:
        payload = chatter_event_payload(text, mode=self._log_chatter, extra=extra or None)
        if payload is None:
            return
        self._events.emit(event_type, payload)
        log_fn = self._log.debug if self._log_chatter == "full" else self._log.info
        # Console stays on the short preview when present; events keep full text.
        log_payload = dict(payload)
        if "preview" in log_payload and self._log_chatter == "summary":
            log_payload = {
                "preview": log_payload["preview"],
                "length": log_payload.get("length"),
                "truncated": log_payload.get("preview_truncated", log_payload.get("truncated")),
            }
        log_fn(event_type, **log_payload)

    def _remaining_count(self) -> int:
        if self._plan is not None:
            return len(self._plan.remaining_items)
        return len(self._last_remaining_work)

    def _update_progress_counters(
        self,
        verdict: CompletionVerdict,
        *,
        remaining_before: int,
        remaining_after: int,
    ) -> None:
        self._last_completion = verdict
        if isinstance(verdict, Blocked):
            # Blocked escalates via the blocked flag; reset streak counters.
            self._consecutive_no_progress = 0
            self._consecutive_progress = 0
            return
        if self._plan is None:
            self._consecutive_no_progress = 0
            self._consecutive_progress = 0
            return
        made_progress = remaining_after < remaining_before
        if made_progress:
            self._consecutive_progress += 1
            self._consecutive_no_progress = 0
        elif isinstance(verdict, Continue):
            self._consecutive_no_progress += 1
            self._consecutive_progress = 0
        else:
            self._consecutive_no_progress = 0
            self._consecutive_progress = 0

    def _consider_auto_model(self, state: RunState) -> None:
        blocked = isinstance(getattr(self, "_last_completion", None), Blocked)
        decision = decide_auto_model(
            self._profile,
            consecutive_no_progress=self._consecutive_no_progress,
            consecutive_progress=self._consecutive_progress,
            blocked=blocked,
            dollars_spent=state.ledger.dollars_spent,
            max_dollars=self._max_dollars,
            budget_downgrade_done=self._budget_downgrade_done,
            operator_locked=self._operator_locked,
            auto_enabled=self._auto_model,
            aliases=self._aliases,
        )
        if decision.profile is None:
            return
        if decision.reason == "downgrade_budget":
            self._budget_downgrade_done = True
            self._log.info("model.auto_downgrade_budget", dollars_spent=state.ledger.dollars_spent)
        self._consecutive_no_progress = 0
        self._consecutive_progress = 0
        self._queue_profile(decision.profile, operator=False)
        self._events.emit(
            "model.auto_policy",
            {
                "reason": decision.reason,
                "model": decision.profile.model,
                "effort": decision.profile.effort,
                "preset": decision.profile.preset,
            },
        )

    async def _sleep_interruptible(self, until: datetime) -> bool:
        """Chunked sleep; return True if stop was requested."""
        while True:
            self._apply_control(self._control.poll(), natural_break=False)
            if self._stop_requested:
                return True
            now = self._clock.now()
            if now >= until:
                return False
            chunk_end = min(until, now + _SLEEP_CHUNK)
            await self._sleeper.sleep_until(chunk_end)

    async def _finish_stopped(
        self, state: RunState, *, session_id: str | None, reason: str
    ) -> RunResult:
        await self._gateway.close()
        remaining_plan = tuple(
            item.text for item in (self._plan.remaining_items if self._plan else ())
        )
        points = self._save_points.list_points(self._run_id)
        latest = f"#{points[-1].n} `{points[-1].sha[:12]}` — {points[-1].label}" if points else None
        changes = self._save_points.changes_since(self._first_savepoint_sha)
        resume_hint = (
            "Resume with `claudeloop resume` (same Claude session) or re-run the "
            "plan after addressing remaining items. Use "
            f"`claudeloop unwind --to N --run-id {self._run_id}` to revert "
            "worktree save points if needed."
        )
        markdown = render_stop_summary(
            StopSummaryInput(
                run_id=self._run_id,
                session_id=session_id,
                reason=reason,
                turns_spent=state.ledger.turns_spent,
                dollars_spent=state.ledger.dollars_spent,
                last_summary=self._last_summary,
                remaining_plan_items=remaining_plan,
                remaining_work=self._last_remaining_work,
                git_changes=changes,
                latest_savepoint=latest,
                events_path=self._events_path or "(events.jsonl)",
                resume_hint=resume_hint,
            )
        )
        if self._stop_summary_writer is not None:
            path = self._stop_summary_writer(markdown)
            self._events.emit("stop.summary_written", {"path": str(path)})
            self._log.info("stop.summary_written", path=str(path))
        self._progress.finished(success=False, reason=reason)
        self._audit.record(
            "finished",
            {
                "success": False,
                "reason": reason,
                "run_id": self._run_id,
                "session_id": session_id,
            },
        )
        self._events.emit("finished", {"success": False, "reason": reason})
        self._log.info(
            "run.stopped",
            reason=reason,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
            session_id=session_id,
        )
        self._update_meta(
            status="stopped",
            phase=Phase.FAILED.name,
            session_id=session_id,
            capacity=self._last_capacity_name,
            model=self._profile.model,
            effort=self._profile.effort,
            preset=self._profile.preset,
        )
        self._persist(state, session_id=session_id, attempt=0)
        # Persist must not clobber stopped — re-assert after phase-derived status.
        self._update_meta(status="stopped", phase=Phase.FAILED.name)
        self._emit_snapshot(
            "stopped",
            session_id=session_id,
            attempt=0,
            state=state,
            status="stopped",
            bundle=True,
        )
        self._release_lock()
        self._stream_ui.close()
        return RunResult(
            success=False,
            reason=reason,
            session_id=session_id,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
        )

    def _project_capacity(
        self, state: RunState, *, capacity: CapacityState, now: datetime
    ) -> CapacityForecast | None:
        """Forecast remaining capacity, but only while the vendor says we are
        not already blocked.

        Returning None for every non-Available state is what keeps vendor
        utilization from ever influencing whether a turn is *sent*: once a real
        rejection has landed, the reactive path owns it.
        """
        if not isinstance(capacity, Available):
            return None
        turns = state.ledger.turns_spent + 1
        projection = forecast(
            capacity,
            turns_spent=turns,
            max_turns=state.ledger.budget.max_turns,
            dollars_spent=state.ledger.dollars_spent,
            max_dollars=state.ledger.budget.max_dollars,
            observed=BurnRate(
                turns=turns,
                elapsed_seconds=0.0,
                dollars=state.ledger.dollars_spent,
            ),
            capacity_as_of=now,
            capacity_resets_at=self._last_resets_at,
            now=now,
            policy=self._wind_down_policy,
        )
        self._events.emit(
            "capacity.forecast",
            {
                "headroom": projection.binding.fraction,
                "source": projection.binding.source,
                "turns_until_exhaustion": projection.turns_until_exhaustion,
                "seconds_until_reset": projection.seconds_until_reset,
            },
        )
        return projection

    async def _finish_wound_down(
        self, state: RunState, *, session_id: str | None, decision: WindDownAndFinish
    ) -> RunResult:
        """Stop early, on purpose, leaving a successor everything it needs.

        The write order is load-bearing. Save point, then summary, then the
        bundled snapshot, then meta, and only then the marker -- so that if
        handoff.json exists, every artifact it names exists. A process killed
        part-way through leaves no marker at all, and a supervisor falls back to
        the reactive path it used before.
        """
        await self._gateway.close()
        remaining_plan = tuple(
            item.text for item in (self._plan.remaining_items if self._plan else ())
        )
        # 1. save point, so the successor has a commit to branch from
        self._create_savepoint(
            label="handoff",
            attempt=0,
            verdict=Continue(remaining_work=self._last_remaining_work),
        )
        points = self._save_points.list_points(self._run_id)
        latest = points[-1] if points else None

        # 2. stop summary, human-readable
        markdown = render_stop_summary(
            StopSummaryInput(
                run_id=self._run_id,
                session_id=session_id,
                reason=f"wind-down: {decision.reason}",
                turns_spent=state.ledger.turns_spent,
                dollars_spent=state.ledger.dollars_spent,
                last_summary=self._last_summary,
                remaining_plan_items=remaining_plan,
                remaining_work=self._last_remaining_work,
                git_changes=self._save_points.changes_since(self._first_savepoint_sha),
                latest_savepoint=(
                    f"#{latest.n} `{latest.sha[:12]}` — {latest.label}" if latest else None
                ),
                events_path=self._events_path or "(events.jsonl)",
                resume_hint=(
                    "This run wound down before its capacity ran out. Resume it "
                    f"with `claudeloop resume` or hand the work to another runner "
                    f"using runs/{self._run_id}/handoff.json."
                ),
            )
        )
        summary_path: str | None = None
        if self._stop_summary_writer is not None:
            summary_path = str(self._stop_summary_writer(markdown))

        # 3. meta + bundled snapshot
        self._update_meta(
            status="handoff",
            phase=Phase.HANDOFF.name,
            session_id=session_id,
            capacity=self._last_capacity_name,
            model=self._profile.model,
            effort=self._profile.effort,
            preset=self._profile.preset,
        )
        self._persist(state, session_id=session_id, attempt=0)
        self._update_meta(status="handoff", phase=Phase.HANDOFF.name)
        snapshot = self._emit_snapshot(
            "handoff",
            session_id=session_id,
            attempt=0,
            state=state,
            status="handoff",
            bundle=True,
        )

        # 4. the marker, last, once everything above is on disk
        binding = decision.forecast.binding
        marker = HandoffMarker(
            run_id=self._run_id,
            reason=decision.reason,
            produced_at=self._clock.now(),
            headroom=binding.fraction,
            headroom_source=binding.source,
            resets_at=binding.resets_at,
            snapshot_path=snapshot.path if snapshot else None,
            bundle_path=snapshot.bundle_path if snapshot else None,
            stop_summary_path=summary_path,
            savepoint_ref=latest.ref if latest else None,
            savepoint_sha=latest.sha if latest else None,
            session_id=session_id,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
            remaining_work=self._last_remaining_work,
        )
        if self._handoff_marker_writer is not None:
            self._handoff_marker_writer(marker)

        self._progress.finished(success=False, reason=f"wind-down: {decision.reason}")
        self._events.emit(
            "wind_down.finished",
            {"reason": decision.reason, "headroom": binding.fraction, "source": binding.source},
        )
        self._log.info(
            "run.wound_down",
            reason=decision.reason,
            headroom=binding.fraction,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
            session_id=session_id,
        )
        self._release_lock()
        self._stream_ui.close()
        return RunResult(
            success=False,
            reason=f"wind-down: {decision.reason}",
            session_id=session_id,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
        )

    def _remember_verdict(self, verdict: CompletionVerdict) -> None:
        if isinstance(verdict, Done):
            self._last_summary = verdict.summary
            self._last_remaining_work = ()
        elif isinstance(verdict, Continue):
            self._last_remaining_work = verdict.remaining_work
        else:
            self._last_summary = getattr(verdict, "reason", self._last_summary)

    def _reconcile_plan(self, verdict: CompletionVerdict) -> None:
        if self._plan is None or not isinstance(verdict, Continue):
            return
        # Items not listed in remaining_work are treated as done.
        remaining = frozenset(verdict.remaining_work)
        done_texts = frozenset(
            item.text for item in self._plan.items if item.text not in remaining and not item.done
        )
        if done_texts:
            self._plan = self._plan.with_items_marked_done(done_texts)
            self._events.emit(
                "plan.reconciled",
                {"marked_done": sorted(done_texts)},
            )

    def _create_savepoint(
        self,
        *,
        label: str,
        attempt: int,
        verdict: CompletionVerdict,
        summary: str = "",
    ) -> None:
        remaining: tuple[str, ...] = ()
        if isinstance(verdict, Done):
            summary = summary or verdict.summary
        elif isinstance(verdict, Continue):
            remaining = verdict.remaining_work
            summary = summary or self._last_summary
        else:
            # CompletionVerdict is the closed union {Done, Continue, Blocked};
            # both other members are handled above, so this is exhaustive.
            assert isinstance(verdict, Blocked)  # nosec B101
            summary = summary or verdict.reason
        self._prev_savepoint_sha = self._last_savepoint_sha
        point = self._save_points.create(
            run_id=self._run_id,
            label=label,
            attempt=attempt,
            verdict_name=type(verdict).__name__,
            summary=summary,
            remaining_work=remaining,
        )
        if point is None:
            self._last_tree_changed = True
            self._events.emit("savepoint.skipped", {"reason": "not a git repository"})
            self._log.debug("savepoint.skipped", reason="not a git repository")
            return
        if self._first_savepoint_sha is None:
            self._first_savepoint_sha = point.sha
        self._last_savepoint_sha = point.sha
        # Prefer the store's commit bit (git: has_staged). Falling back to SHA
        # compare only when a baseline exists avoids marking the first ref-only
        # savepoint as committed=True just because prev was None.
        committed = point.committed
        self._last_tree_changed = committed
        self._events.emit(
            "savepoint",
            {
                "n": point.n,
                "sha": point.sha,
                "ref": point.ref,
                "label": point.label,
                "committed": committed,
            },
        )
        self._log.info(
            "savepoint.created",
            n=point.n,
            sha=point.sha,
            ref=point.ref,
            label=point.label,
            committed=committed,
        )

    def _maybe_notify_credits(self, capacity: CapacityState) -> None:
        if isinstance(capacity, CreditsExhausted) and not self._credits_notified:
            purchase = (
                "You can purchase more credits."
                if capacity.can_purchase
                else ("Purchasing credits may not be available on this account.")
            )
            self._notifier.notify(
                "claudeloop: credits exhausted — top up the Anthropic account "
                f"to resume. {purchase} The runner will keep probing."
            )
            self._credits_notified = True
            self._events.emit("notify.credits_exhausted", {"can_purchase": capacity.can_purchase})
            self._log.warning(
                "credits.exhausted",
                can_purchase=capacity.can_purchase,
            )

    def _persist(self, state: RunState, *, session_id: str | None, attempt: int) -> None:
        status = (
            "finished"
            if state.phase.name in {"COMPLETE"}
            else (
                "failed"
                if state.phase.name == "FAILED"
                else ("waiting" if state.phase.name == "WAITING" else "active")
            )
        )
        snapshot = {
            "phase": state.phase.name,
            "session_id": session_id,
            "attempt": attempt,
            "turns_spent": state.ledger.turns_spent,
            "dollars_spent": state.ledger.dollars_spent,
            "probe_count": state.probe_count,
            "started_waiting_at": (
                state.started_waiting_at.isoformat() if state.started_waiting_at else None
            ),
            "status": status,
            "model": self._profile.model,
            "effort": self._profile.effort,
            "preset": self._profile.preset,
            "capacity": self._last_capacity_name,
        }
        self._state_store.save(self._run_id, snapshot)
        self._state_bus.publish(f"phase.{state.phase.name.lower()}", snapshot)
        meta_kwargs: dict[str, Any] = {
            "phase": state.phase.name,
            "attempt": attempt,
            "session_id": session_id,
            "model": self._profile.model,
            "effort": self._profile.effort,
            "preset": self._profile.preset,
            "capacity": self._last_capacity_name,
        }
        # Never clobber an explicit operator stop (or other non-derived status)
        # by forcing status="active" on every persist.
        if status != "active":
            meta_kwargs["status"] = status
        self._update_meta(**meta_kwargs)
        self._emit_snapshot(
            "status",
            session_id=session_id,
            attempt=attempt,
            state=state,
            status=status,
        )

    def _emit_snapshot(
        self,
        reason: SnapshotReason,
        *,
        session_id: str | None,
        attempt: int,
        state: RunState,
        status: str | None = None,
        waiting_until: str | None = None,
        bundle: bool | None = None,
    ) -> SnapshotRef | None:
        remaining_plan = tuple(
            item.text for item in (self._plan.remaining_items if self._plan else ())
        )
        context: dict[str, Any] = {
            "session_id": session_id,
            "attempt": attempt,
            "phase": state.phase.name,
            "status": status
            or (
                "finished"
                if state.phase.name == "COMPLETE"
                else (
                    "failed"
                    if state.phase.name == "FAILED"
                    else ("waiting" if state.phase.name == "WAITING" else "active")
                )
            ),
            "turns_spent": state.ledger.turns_spent,
            "dollars_spent": state.ledger.dollars_spent,
            "probe_count": state.probe_count,
            "started_waiting_at": (
                state.started_waiting_at.isoformat() if state.started_waiting_at else None
            ),
            "waiting_until": waiting_until,
            "model": self._profile.model,
            "effort": self._profile.effort,
            "preset": self._profile.preset,
            "capacity": self._last_capacity_name,
            "remaining_plan_items": list(remaining_plan),
            "remaining_work": list(self._last_remaining_work),
            "max_turns": self._budget.max_turns,
            "max_dollars": self._max_dollars,
            "max_attempts": self._budget.max_attempts,
        }
        return self._snapshots.emit(reason, context=context, bundle=bundle)

    def _update_meta(self, **kwargs: Any) -> None:
        if self._meta_updater is not None:
            self._meta_updater(**kwargs)

    def _acquire_session_lock(self, session_id: str) -> bool:
        """Take the advisory lock for ``session_id``. Returns False when another
        runner already holds it — callers must fail closed rather than continue."""
        if not self._session_lock.acquire(session_id):
            self._log.warning("session.lock_busy", session_id=session_id)
            return False
        self._lock_token = session_id
        self._log.info("session.lock_acquired", session_id=session_id)
        return True

    async def _finish_lock_contention(self, state: RunState, *, session_id: str) -> RunResult:
        reason = (
            f"session {session_id} is already locked by another claudeloop runner; "
            "refusing to drive it concurrently"
        )
        with contextlib.suppress(Exception):
            await self._gateway.close()
        self._progress.finished(success=False, reason=reason)
        self._audit.record(
            "finished",
            {
                "success": False,
                "reason": reason,
                "run_id": self._run_id,
                "session_id": session_id,
            },
        )
        self._events.emit("finished", {"success": False, "reason": reason})
        self._log.info(
            "run.failed",
            reason=reason,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
            session_id=session_id,
        )
        self._update_meta(
            status="failed",
            phase=Phase.FAILED.name,
            session_id=session_id,
            capacity=self._last_capacity_name,
            model=self._profile.model,
            effort=self._profile.effort,
            preset=self._profile.preset,
        )
        self._persist(state, session_id=session_id, attempt=0)
        self._emit_snapshot(
            "failed",
            session_id=session_id,
            attempt=0,
            state=state,
            status="failed",
            bundle=True,
        )
        self._release_lock()
        self._stream_ui.close()
        return RunResult(
            success=False,
            reason=reason,
            session_id=session_id,
            turns_spent=state.ledger.turns_spent,
            dollars_spent=state.ledger.dollars_spent,
        )

    def _release_lock(self) -> None:
        if self._lock_token is not None:
            self._session_lock.release(self._lock_token)
            self._log.info("session.lock_released", session_id=self._lock_token)
            self._lock_token = None

    def _verdict_capacity(self, outcome: TurnOutcome) -> CapacityState:
        return classify(outcome.signals)

    def _completion_verdict(self, outcome: TurnOutcome) -> CompletionVerdict:
        kwargs: dict[str, Any] = {
            "cost_usd": outcome.cost_usd,
            "empty_turn_streak": self._empty_turn_streak,
        }
        if self._done_marker:
            kwargs["done_marker"] = self._done_marker
        return evaluate(structured=outcome.verdict, output_text=outcome.output_text, **kwargs)


__all__ = ["AutonomousRunner", "RunState", "Phase"]

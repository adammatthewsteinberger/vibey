# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""OpenTelemetry tracing and metrics instrumentation (Milestone 8 task 8.3)."""

from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase


@dataclass(slots=True)
class Span:
    span_id: str
    name: str
    parent_id: str | None = None
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime | None = None
    attributes: dict[str, object] = field(default_factory=dict)
    events: list[dict[str, object]] = field(default_factory=list)
    status: str = "OK"

    @property
    def duration(self) -> timedelta:
        if self.end_time is None:
            return datetime.now(UTC) - self.start_time
        return self.end_time - self.start_time

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, object] | None = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.now(UTC).isoformat(),
                "attributes": attributes or {},
            }
        )

    def finish(self, status: str = "OK") -> None:
        self.status = status
        self.end_time = datetime.now(UTC)


class TelemetryTracer:
    def __init__(self) -> None:
        self._spans: list[Span] = []
        self._active_stack: list[Span] = []

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        parent_id: str | None = None,
        attributes: dict[str, object] | None = None,
    ) -> Iterator[Span]:
        current_parent = parent_id or (
            self._active_stack[-1].span_id if self._active_stack else None
        )
        span = Span(
            span_id=uuid4().hex[:16],
            name=name,
            parent_id=current_parent,
            attributes=dict(attributes or {}),
        )
        self._active_stack.append(span)
        try:
            yield span
            span.finish("OK")
        except Exception as exc:
            span.finish("ERROR")
            span.set_attribute("error.type", type(exc).__name__)
            span.set_attribute("error.message", str(exc))
            raise
        finally:
            self._active_stack.pop()
            self._spans.append(span)

    @contextmanager
    def trace_job(
        self,
        *,
        project_id: UUID,
        cycle: int,
        phase: Phase,
        job_kind: str,
        engine_id: EngineId | str | None = None,
        effort: Effort | str | None = None,
        **extra_attributes: object,
    ) -> Iterator[Span]:
        attrs: dict[str, object] = {
            "project_id": str(project_id),
            "cycle": cycle,
            "phase": phase.value,
            "job_kind": job_kind,
        }
        if engine_id is not None:
            attrs["engine_id"] = (
                engine_id.value if isinstance(engine_id, EngineId) else str(engine_id)
            )
        if effort is not None:
            attrs["effort"] = (
                effort.name.lower() if isinstance(effort, Effort) else str(effort).lower()
            )

        attrs.update(extra_attributes)
        with self.start_span(f"job:{job_kind}", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_turn(
        self,
        *,
        engine_id: EngineId | str | None = None,
        turn_number: int | None = None,
        **extra_attributes: object,
    ) -> Iterator[Span]:
        attrs: dict[str, object] = {}
        if engine_id is not None:
            attrs["engine_id"] = (
                engine_id.value if isinstance(engine_id, EngineId) else str(engine_id)
            )
        if turn_number is not None:
            attrs["turn_number"] = turn_number
        attrs.update(extra_attributes)
        with self.start_span("turn", attributes=attrs) as span:
            yield span

    @contextmanager
    def trace_handoff(
        self,
        *,
        from_engine: EngineId | str | None = None,
        to_engine: EngineId | str | None = None,
        **extra_attributes: object,
    ) -> Iterator[Span]:
        attrs: dict[str, object] = {}
        if from_engine is not None:
            attrs["from_engine"] = (
                from_engine.value if isinstance(from_engine, EngineId) else str(from_engine)
            )
        if to_engine is not None:
            attrs["to_engine"] = (
                to_engine.value if isinstance(to_engine, EngineId) else str(to_engine)
            )
        attrs.update(extra_attributes)
        with self.start_span("handoff", attributes=attrs) as span:
            yield span

    def get_finished_spans(self) -> list[Span]:
        return list(self._spans)

    def clear(self) -> None:
        self._spans.clear()
        self._active_stack.clear()


class TelemetryMetrics:
    def __init__(self) -> None:
        self._selections: dict[UUID, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._queue_latencies: dict[UUID, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._phase_durations: dict[UUID, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._handoff_failures: dict[UUID, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._cost_spend: dict[UUID, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def record_engine_selection(self, project_id: UUID, engine_id: EngineId | str) -> None:
        key = engine_id.value if isinstance(engine_id, EngineId) else str(engine_id)
        self._selections[project_id][key] += 1

    def record_queue_latency(
        self, project_id: UUID, phase: Phase | str, job_kind: str, latency_seconds: float
    ) -> None:
        self._queue_latencies[project_id][job_kind].append(latency_seconds)

    def record_phase_duration(
        self, project_id: UUID, cycle: int, phase: Phase | str, duration_seconds: float
    ) -> None:
        p_str = phase.value if isinstance(phase, Phase) else str(phase)
        self._phase_durations[project_id][p_str].append(duration_seconds)

    def record_handoff_gate_failure(self, project_id: UUID, rule_id: str) -> None:
        self._handoff_failures[project_id][rule_id] += 1

    def record_cost_spend(
        self,
        project_id: UUID,
        cycle: int,
        phase: Phase | str,
        engine_id: EngineId | str,
        cost_usd: float,
    ) -> None:
        eng_str = engine_id.value if isinstance(engine_id, EngineId) else str(engine_id)
        self._cost_spend[project_id][eng_str] += cost_usd

    def export_metrics(self, project_id: UUID) -> dict[str, object]:
        return {
            "engine_selections": dict(self._selections.get(project_id, {})),
            "queue_latencies": dict(self._queue_latencies.get(project_id, {})),
            "phase_durations": dict(self._phase_durations.get(project_id, {})),
            "handoff_gate_failures": dict(self._handoff_failures.get(project_id, {})),
            "cost_spend": dict(self._cost_spend.get(project_id, {})),
        }


def calculate_rotation_fairness(selections: Mapping[str, int], weights: Mapping[str, int]) -> float:
    """Calculates Jain's Fairness Index over weighted selection ratios.

    Returns a score in [0.0, 1.0], where 1.0 is perfectly fair relative
    to declared rotation weights.
    """
    keys = set(selections.keys()) | set(weights.keys())
    if not keys:
        return 1.0

    ratios: list[float] = []
    for k in keys:
        w = float(weights.get(k, 1))
        if w <= 0:
            w = 1.0
        x = float(selections.get(k, 0))
        ratios.append(x / w)

    total_ratio = sum(ratios)
    if total_ratio == 0:
        return 1.0

    sum_sq = sum(r * r for r in ratios)
    n = len(ratios)
    fairness = (total_ratio * total_ratio) / (n * sum_sq)
    return min(max(fairness, 0.0), 1.0)

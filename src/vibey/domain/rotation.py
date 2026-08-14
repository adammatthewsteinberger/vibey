"""Engine rotation: eligibility filtering and nginx's Smooth Weighted Round
Robin over the eligible set (ADR-0005)."""

from collections.abc import Sequence
from dataclasses import dataclass, replace

from vibey.domain.circuit import Circuit, CircuitState
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineDescriptor, EngineId, JobRequirement
from vibey.domain.errors import NoEligibleEngine


@dataclass(frozen=True, slots=True)
class EngineRuntime:
    engine_id: EngineId
    descriptor: EngineDescriptor
    circuit: Circuit
    installed: bool
    conformance_ok: bool
    auth_valid: bool


@dataclass(frozen=True, slots=True)
class Candidate:
    engine_id: EngineId
    base_weight: int
    current: int
    order: int
    health_factor: float
    fidelity_factor: float
    cost_factor: float
    affinity_factor: float

    @property
    def effective_weight(self) -> int:
        return max(
            0,
            round(
                self.base_weight
                * self.health_factor
                * self.fidelity_factor
                * self.cost_factor
                * self.affinity_factor
            ),
        )


@dataclass(frozen=True, slots=True)
class Selection:
    engine_id: EngineId
    candidates: tuple[Candidate, ...]  # updated SWRR state


def eligible(
    runtimes: Sequence[EngineRuntime],
    *,
    requirement: JobRequirement,
    allow_list: frozenset[EngineId] | None = None,
) -> tuple[EngineRuntime, ...]:
    result = []
    for runtime in runtimes:
        if not runtime.installed or not runtime.conformance_ok or not runtime.auth_valid:
            continue
        if runtime.circuit.state is CircuitState.OPEN:
            continue
        if runtime.engine_id in requirement.excluded:
            continue
        if allow_list is not None and runtime.engine_id not in allow_list:
            continue
        if not requirement.capabilities <= runtime.descriptor.capabilities:
            continue
        result.append(runtime)
    return tuple(result)


def health_factor(circuit: Circuit) -> float:
    if circuit.state is CircuitState.OPEN:
        return 0.0
    if circuit.state is CircuitState.HALF_OPEN:
        return 0.5
    return max(0.0, 1.0 - circuit.ewma_failure)


def fidelity_factor(descriptor: EngineDescriptor, requested: Effort) -> float:
    return 0.7 if descriptor.saturates_at(requested) else 1.0


def cost_factor(descriptor: EngineDescriptor, *, median_cost: float, enabled: bool) -> float:
    if not enabled or median_cost <= 0:
        return 1.0
    engine_cost = descriptor.cost_per_mtok_in + descriptor.cost_per_mtok_out
    ratio = median_cost / engine_cost if engine_cost > 0 else 1.0
    return min(1.5, max(0.5, ratio))


def affinity_factor(*, holds_warm_session: bool, rotation_forced: bool) -> float:
    if rotation_forced:
        return 1.0
    return 1.2 if holds_warm_session else 1.0


def select(candidates: Sequence[Candidate]) -> Selection:
    """Smooth Weighted Round Robin (nginx's algorithm).

    Requires each candidate's engine_id to be unique in the input -- there
    are only four known engines, and the rotator never offers the same one
    twice in a single selection round.
    """
    if not candidates:
        raise NoEligibleEngine("no candidates to select from")

    engine_ids = [c.engine_id for c in candidates]
    if len(set(engine_ids)) != len(engine_ids):
        raise ValueError("select() requires unique engine_id per candidate")

    if all(c.effective_weight == 0 for c in candidates):
        raise NoEligibleEngine("every candidate has effective_weight 0")

    total_weight = sum(c.effective_weight for c in candidates)
    bumped = {c.engine_id: c.current + c.effective_weight for c in candidates}

    winner = max(candidates, key=lambda c: (bumped[c.engine_id], -c.order))
    bumped[winner.engine_id] -= total_weight

    updated = tuple(replace(c, current=bumped[c.engine_id]) for c in candidates)
    return Selection(engine_id=winner.engine_id, candidates=updated)

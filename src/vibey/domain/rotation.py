# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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
        raw = (
            self.base_weight
            * self.health_factor
            * self.fidelity_factor
            * self.cost_factor
            * self.affinity_factor
        )
        if raw <= 0:
            return 0
        # A positive weight must never round down to zero: a half-open
        # probe on a base_weight-1 engine is 1 * 0.25 = 0.25, and round()
        # made it 0 -- so the probe could never fire and the engine stayed
        # open forever (caught by the unattended validation run, where
        # forced rotation then had no candidate left at all).
        return max(1, round(raw))


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
    """1.0 closed, 0.25 half-open, 0.0 open; closed decays on recent failures.

    Half-open is deliberately a quarter, not a half (ADR-0005): the circuit is
    being *tested*, so it should win a round only when the alternatives are
    genuinely worse -- not on even footing with a healthy engine.
    """
    if circuit.state is CircuitState.OPEN:
        return 0.0
    if circuit.state is CircuitState.HALF_OPEN:
        return 0.25
    return max(0.0, 1.0 - circuit.ewma_failure)


def fidelity_factor(descriptor: EngineDescriptor, requested: Effort) -> float:
    """1.0 at the requested tier, 0.7 one tier below, 0.5 two or more below.

    An engine that saturates far below what was asked for is a worse answer
    than one that just misses, so the penalty has to have more than one step.
    """
    achieved = descriptor.invoke(requested).achieved
    shortfall = int(requested) - int(achieved)
    if shortfall <= 0:
        return 1.0
    return 0.7 if shortfall == 1 else 0.5


def cost_factor(descriptor: EngineDescriptor, *, median_cost: float, enabled: bool) -> float:
    if not enabled or median_cost <= 0:
        return 1.0
    engine_cost = descriptor.cost_per_mtok_in + descriptor.cost_per_mtok_out
    ratio = median_cost / engine_cost if engine_cost > 0 else 1.0
    return min(1.5, max(0.5, ratio))


def affinity_factor(*, holds_warm_session: bool, rotation_forced: bool) -> float:
    """2.0 for a warm session, unless rotation is forced (ADR-0005).

    This is what makes an ordinary retry stay put. Rotating on every retry
    means a handoff on every retry: maximum cost, maximum chance the no-loss
    gate has to work, zero benefit. It has to outweigh normal health and cost
    variation to actually hold the session, which a 1.2 nudge does not.
    """
    if rotation_forced:
        return 1.0
    return 2.0 if holds_warm_session else 1.0


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

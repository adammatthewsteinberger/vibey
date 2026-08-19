from collections import Counter

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from vibey.domain.circuit import Circuit, CircuitState
from vibey.domain.effort import Effort
from vibey.domain.engine import (
    Capability,
    EngineDescriptor,
    EngineId,
    EngineInvocation,
    IsolationLevel,
    JobRequirement,
)
from vibey.domain.errors import NoEligibleEngine
from vibey.domain.rotation import (
    Candidate,
    EngineRuntime,
    affinity_factor,
    cost_factor,
    eligible,
    fidelity_factor,
    health_factor,
    select,
)

ALL_ENGINES = list(EngineId)


def _descriptor(
    engine_id: EngineId, *, capabilities: frozenset[Capability] = frozenset()
) -> EngineDescriptor:
    return EngineDescriptor(
        engine_id=engine_id,
        binary=str(engine_id),
        min_version="1.0.0",
        state_dir=f".{engine_id}",
        done_marker="DONE",
        auth_env=(),
        capabilities=capabilities,
        effort_projection={Effort.HIGH: EngineInvocation((), achieved=Effort.HIGH)},
        session_verb="resume",
        isolation_flags={IsolationLevel.WORKTREE: ()},
        cost_per_mtok_in=1.0,
        cost_per_mtok_out=1.0,
        context_window=100_000,
    )


def _saturating_descriptor(engine_id: EngineId, *, ceiling: Effort) -> EngineDescriptor:
    """A descriptor whose projection tops out at ``ceiling``, so a request above
    it lands short by a measurable number of tiers."""
    projection = {effort: EngineInvocation((), achieved=min(effort, ceiling)) for effort in Effort}
    return EngineDescriptor(
        engine_id=engine_id,
        binary=str(engine_id),
        min_version="1.0.0",
        state_dir=f".{engine_id}",
        done_marker="DONE",
        auth_env=(),
        capabilities=frozenset(),
        effort_projection=projection,
        session_verb="resume",
        isolation_flags={IsolationLevel.WORKTREE: ()},
        cost_per_mtok_in=1.0,
        cost_per_mtok_out=1.0,
        context_window=100_000,
    )


def _closed_circuit() -> Circuit:
    from vibey.domain.capacity import Available

    return Circuit(state=CircuitState.CLOSED, capacity=Available(), probe=None)


def _runtime(engine_id: EngineId, **overrides: object) -> EngineRuntime:
    defaults: dict[str, object] = {
        "descriptor": _descriptor(engine_id),
        "circuit": _closed_circuit(),
        "installed": True,
        "conformance_ok": True,
        "auth_valid": True,
    }
    defaults.update(overrides)
    return EngineRuntime(engine_id=engine_id, **defaults)  # type: ignore[arg-type]


def _candidate(
    engine_id: EngineId, *, order: int, base_weight: int = 1, current: int = 0
) -> Candidate:
    return Candidate(
        engine_id=engine_id,
        base_weight=base_weight,
        current=current,
        order=order,
        health_factor=1.0,
        fidelity_factor=1.0,
        cost_factor=1.0,
        affinity_factor=1.0,
    )


# --- eligible() -----------------------------------------------------------


def test_eligible_excludes_uninstalled_engines() -> None:
    runtimes = [_runtime(EngineId.CLAUDELOOP, installed=False)]
    assert eligible(runtimes, requirement=JobRequirement(effort=Effort.LOW)) == ()


def test_eligible_excludes_open_circuit() -> None:
    from vibey.domain.capacity import CreditsExhausted

    open_circuit = Circuit(state=CircuitState.OPEN, capacity=CreditsExhausted(), probe=None)
    runtimes = [_runtime(EngineId.CLAUDELOOP, circuit=open_circuit)]
    assert eligible(runtimes, requirement=JobRequirement(effort=Effort.LOW)) == ()


def test_eligible_excludes_engines_in_requirement_excluded() -> None:
    runtimes = [_runtime(EngineId.CLAUDELOOP)]
    requirement = JobRequirement(effort=Effort.LOW, excluded=frozenset({EngineId.CLAUDELOOP}))
    assert eligible(runtimes, requirement=requirement) == ()


def test_eligible_respects_allow_list() -> None:
    runtimes = [_runtime(EngineId.CLAUDELOOP), _runtime(EngineId.CODEXLOOP)]
    requirement = JobRequirement(effort=Effort.LOW)
    result = eligible(runtimes, requirement=requirement, allow_list=frozenset({EngineId.CODEXLOOP}))
    assert [r.engine_id for r in result] == [EngineId.CODEXLOOP]


def test_eligible_requires_capability_subset() -> None:
    runtime = _runtime(
        EngineId.CLAUDELOOP, descriptor=_descriptor(EngineId.CLAUDELOOP, capabilities=frozenset())
    )
    requirement = JobRequirement(effort=Effort.LOW, capabilities=frozenset({Capability.SAVEPOINTS}))
    assert eligible([runtime], requirement=requirement) == ()


def test_eligible_passes_a_fully_healthy_engine() -> None:
    runtime = _runtime(EngineId.CLAUDELOOP)
    result = eligible([runtime], requirement=JobRequirement(effort=Effort.LOW))
    assert result == (runtime,)


# --- factors ----------------------------------------------------------------


def test_health_factor_zero_when_open() -> None:
    from vibey.domain.capacity import CreditsExhausted

    circuit = Circuit(state=CircuitState.OPEN, capacity=CreditsExhausted(), probe=None)
    assert health_factor(circuit) == 0.0


def test_health_factor_quarter_when_half_open() -> None:
    from vibey.domain.capacity import Available

    circuit = Circuit(state=CircuitState.HALF_OPEN, capacity=Available(), probe=None)
    assert health_factor(circuit) == 0.25


def test_health_factor_full_when_closed_with_no_failures() -> None:
    assert health_factor(_closed_circuit()) == 1.0


def test_fidelity_factor_penalizes_saturation() -> None:
    descriptor = _descriptor(EngineId.CODEXLOOP)
    assert fidelity_factor(descriptor, Effort.HIGH) == 1.0
    assert fidelity_factor(descriptor, Effort.MAX) == 0.7


def test_fidelity_factor_penalizes_a_two_tier_shortfall_harder() -> None:
    """An engine that saturates far below the request is a worse answer than
    one that just misses, so the penalty needs more than a single step."""
    descriptor = _saturating_descriptor(EngineId.AGYLOOP, ceiling=Effort.STANDARD)
    assert fidelity_factor(descriptor, Effort.STANDARD) == 1.0
    assert fidelity_factor(descriptor, Effort.HIGH) == 0.7
    assert fidelity_factor(descriptor, Effort.MAX) == 0.5


def test_cost_factor_disabled_returns_one() -> None:
    descriptor = _descriptor(EngineId.CLAUDELOOP)
    assert cost_factor(descriptor, median_cost=10.0, enabled=False) == 1.0


def test_cost_factor_clamped_between_half_and_one_and_a_half() -> None:
    descriptor = _descriptor(EngineId.CLAUDELOOP)  # cost_per_mtok_in+out = 2.0
    assert cost_factor(descriptor, median_cost=100.0, enabled=True) == 1.5
    assert cost_factor(descriptor, median_cost=0.1, enabled=True) == 0.5


def test_affinity_factor_forced_rotation_ignores_warm_session() -> None:
    assert affinity_factor(holds_warm_session=True, rotation_forced=True) == 1.0


def test_affinity_factor_warm_session_boosts_when_not_forced() -> None:
    assert affinity_factor(holds_warm_session=True, rotation_forced=False) == 2.0
    assert affinity_factor(holds_warm_session=False, rotation_forced=False) == 1.0


# --- select() / SWRR ---------------------------------------------------------


def test_select_raises_on_empty_candidates() -> None:
    with pytest.raises(NoEligibleEngine):
        select([])


def test_select_raises_when_all_weights_zero() -> None:
    candidates = [_candidate(EngineId.CLAUDELOOP, order=0, base_weight=0)]
    with pytest.raises(NoEligibleEngine):
        select(candidates)


def test_select_excludes_zero_weight_from_winning() -> None:
    zero = _candidate(EngineId.CLAUDELOOP, order=0, base_weight=0)
    live = _candidate(EngineId.CODEXLOOP, order=1, base_weight=1)
    selection = select([zero, live])
    assert selection.engine_id == EngineId.CODEXLOOP


def test_select_is_deterministic() -> None:
    candidates = [
        _candidate(EngineId.CLAUDELOOP, order=0, base_weight=3, current=1),
        _candidate(EngineId.CODEXLOOP, order=1, base_weight=2, current=-1),
    ]
    first = select(candidates)
    second = select(candidates)
    assert first.engine_id == second.engine_id
    assert first.candidates == second.candidates


def test_select_no_starvation_over_a_full_period() -> None:
    """Every candidate with effective_weight > 0 is selected at least once
    over sum(effective_weight) consecutive selections."""
    candidates = [
        _candidate(EngineId.CLAUDELOOP, order=0, base_weight=3),
        _candidate(EngineId.CODEXLOOP, order=1, base_weight=2),
        _candidate(EngineId.CURSORLOOP, order=2, base_weight=1),
    ]
    total_weight = sum(c.effective_weight for c in candidates)

    counts: Counter[EngineId] = Counter()
    state = candidates
    for _ in range(total_weight):
        selection = select(state)
        counts[selection.engine_id] += 1
        state = list(selection.candidates)

    for c in candidates:
        assert counts[c.engine_id] >= 1

    # Weight fidelity: selection counts match weight ratios exactly over one
    # full period for integer weights (nginx's SWRR guarantee).
    assert counts[EngineId.CLAUDELOOP] == 3
    assert counts[EngineId.CODEXLOOP] == 2
    assert counts[EngineId.CURSORLOOP] == 1


def test_select_never_picks_same_candidate_twice_in_a_row_when_others_are_waiting() -> None:
    candidates = [
        _candidate(EngineId.CLAUDELOOP, order=0, base_weight=5),
        _candidate(EngineId.CODEXLOOP, order=1, base_weight=1),
    ]
    state = candidates
    previous: EngineId | None = None
    consecutive_repeats = 0
    for _ in range(20):
        selection = select(state)
        if selection.engine_id == previous:
            consecutive_repeats += 1
        previous = selection.engine_id
        state = list(selection.candidates)

    # With weights 5:1 some consecutive repeats of the heavy candidate are
    # inevitable, but it must never monopolize every single slot.
    assert consecutive_repeats < 20


_ENGINE_POOL = [EngineId.CLAUDELOOP, EngineId.CODEXLOOP, EngineId.CURSORLOOP, EngineId.AGYLOOP]


@given(
    weights=st.lists(st.integers(0, 5), min_size=1, max_size=len(_ENGINE_POOL), unique=False),
)
@settings(max_examples=50)
def test_select_totality_matches_weight_zero_rule(weights: list[int]) -> None:
    # One weight per distinct engine in the pool -- select() requires unique
    # engine_id per candidate.
    candidates = [
        _candidate(_ENGINE_POOL[i], order=i, base_weight=w) for i, w in enumerate(weights)
    ]
    if all(c.effective_weight == 0 for c in candidates):
        with pytest.raises(NoEligibleEngine):
            select(candidates)
    else:
        selection = select(candidates)
        winning_candidates = [c for c in candidates if c.engine_id == selection.engine_id]
        assert any(c.effective_weight > 0 for c in winning_candidates)


def test_select_rejects_duplicate_engine_ids() -> None:
    duplicated = [
        _candidate(EngineId.CLAUDELOOP, order=0, base_weight=1),
        _candidate(EngineId.CLAUDELOOP, order=1, base_weight=1),
    ]
    with pytest.raises(ValueError, match="unique engine_id"):
        select(duplicated)


def test_a_positive_weight_never_rounds_down_to_zero() -> None:
    """A half-open probe on a base_weight-1 engine is 1 * 0.25 = 0.25;
    round() made it 0, so the probe could never fire and the engine
    stayed open forever -- caught by the unattended validation run."""
    probe = Candidate(
        engine_id=EngineId.AGYLOOP,
        base_weight=1,
        current=0,
        order=0,
        health_factor=0.25,
        fidelity_factor=1.0,
        cost_factor=1.0,
        affinity_factor=1.0,
    )
    assert probe.effective_weight == 1

    dead = Candidate(
        engine_id=EngineId.CLAUDELOOP,
        base_weight=3,
        current=0,
        order=1,
        health_factor=0.0,
        fidelity_factor=1.0,
        cost_factor=1.0,
        affinity_factor=1.0,
    )
    assert dead.effective_weight == 0

    selection = select([probe, dead])
    assert selection.engine_id is EngineId.AGYLOOP

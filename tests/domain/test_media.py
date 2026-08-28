# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from collections import Counter

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from vibey.domain.errors import NoEligibleEngine
from vibey.domain.media import (
    MediaCandidate,
    MediaProviderDescriptor,
    MediaProviderRuntime,
    MediaRequirement,
    eligible,
    select,
)
from vibey.domain.visual import MediaModality


def _descriptor(provider_id: str, **overrides: object) -> MediaProviderDescriptor:
    defaults: dict[str, object] = {
        "provider_id": provider_id,
        "modalities": frozenset({MediaModality.IMAGE}),
        "reference_input_limit": 4,
        "output_formats": frozenset({"png"}),
        "region": "local",
        "retention_policy": "ephemeral",
        "safety_policy": "default",
        "cost_per_unit": 0.0,
        "long_running": False,
        "external": False,
    }
    defaults.update(overrides)
    return MediaProviderDescriptor(**defaults)  # type: ignore[arg-type]


def _runtime(provider_id: str, **overrides: object) -> MediaProviderRuntime:
    descriptor = overrides.pop("descriptor", None) or _descriptor(provider_id)
    circuit_open = overrides.pop("circuit_open", False)
    return MediaProviderRuntime(descriptor=descriptor, circuit_open=circuit_open)  # type: ignore[arg-type]


def _candidate(  # type: ignore[no-untyped-def]
    provider_id: str, *, order: int, base_weight: int = 1, current: int = 0
):
    return MediaCandidate(
        provider_id=provider_id, base_weight=base_weight, current=current, order=order
    )


# --- eligible() -----------------------------------------------------------


def test_eligible_excludes_open_circuit() -> None:
    runtimes = [_runtime("p1", circuit_open=True)]
    assert eligible(runtimes, requirement=MediaRequirement(modality=MediaModality.IMAGE)) == ()


def test_eligible_excludes_providers_missing_the_modality() -> None:
    audio_only = _descriptor("p1", modalities=frozenset({MediaModality.AUDIO}))
    runtimes = [_runtime("p1", descriptor=audio_only)]
    assert eligible(runtimes, requirement=MediaRequirement(modality=MediaModality.IMAGE)) == ()


def test_eligible_excludes_external_unless_allowed() -> None:
    runtimes = [_runtime("p1", descriptor=_descriptor("p1", external=True))]
    assert eligible(runtimes, requirement=MediaRequirement(modality=MediaModality.IMAGE)) == ()
    allowed = eligible(
        runtimes, requirement=MediaRequirement(modality=MediaModality.IMAGE, allow_external=True)
    )
    assert allowed == tuple(runtimes)


def test_eligible_excludes_over_cost_providers() -> None:
    runtimes = [_runtime("p1", descriptor=_descriptor("p1", cost_per_unit=5.0))]
    requirement = MediaRequirement(modality=MediaModality.IMAGE, max_cost_per_unit=1.0)
    assert eligible(runtimes, requirement=requirement) == ()


def test_eligible_passes_a_fully_healthy_local_provider() -> None:
    runtime = _runtime("p1")
    result = eligible([runtime], requirement=MediaRequirement(modality=MediaModality.IMAGE))
    assert result == (runtime,)


def test_eligible_an_image_provider_can_also_serve_video_independently() -> None:
    both = _descriptor("p1", modalities=frozenset({MediaModality.IMAGE, MediaModality.VIDEO}))
    runtime = _runtime("p1", descriptor=both)
    assert eligible([runtime], requirement=MediaRequirement(modality=MediaModality.IMAGE)) == (
        runtime,
    )
    assert eligible([runtime], requirement=MediaRequirement(modality=MediaModality.VIDEO)) == (
        runtime,
    )
    assert eligible([runtime], requirement=MediaRequirement(modality=MediaModality.AUDIO)) == ()


# --- select() / SWRR --------------------------------------------------------


def test_select_raises_on_empty_candidates() -> None:
    with pytest.raises(NoEligibleEngine):
        select([])


def test_select_raises_when_all_weights_zero() -> None:
    with pytest.raises(NoEligibleEngine):
        select([_candidate("p1", order=0, base_weight=0)])


def test_select_is_deterministic() -> None:
    candidates = [
        _candidate("p1", order=0, base_weight=3, current=1),
        _candidate("p2", order=1, base_weight=2, current=-1),
    ]
    first = select(candidates)
    second = select(candidates)
    assert first.provider_id == second.provider_id
    assert first.candidates == second.candidates


def test_select_no_starvation_over_a_full_period() -> None:
    candidates = [
        _candidate("p1", order=0, base_weight=3),
        _candidate("p2", order=1, base_weight=2),
        _candidate("p3", order=2, base_weight=1),
    ]
    total_weight = sum(c.effective_weight for c in candidates)

    counts: Counter[str] = Counter()
    state = candidates
    for _ in range(total_weight):
        selection = select(state)
        counts[selection.provider_id] += 1
        state = list(selection.candidates)

    for c in candidates:
        assert counts[c.provider_id] >= 1
    assert counts["p1"] == 3
    assert counts["p2"] == 2
    assert counts["p3"] == 1


def test_select_never_picks_same_candidate_twice_in_a_row_when_others_are_waiting() -> None:
    candidates = [
        _candidate("heavy", order=0, base_weight=5),
        _candidate("light", order=1, base_weight=1),
    ]
    state = candidates
    previous: str | None = None
    consecutive_repeats = 0
    for _ in range(20):
        selection = select(state)
        if selection.provider_id == previous:
            consecutive_repeats += 1
        previous = selection.provider_id
        state = list(selection.candidates)

    assert consecutive_repeats < 20


_PROVIDER_POOL = ["p1", "p2", "p3", "p4"]


@given(weights=st.lists(st.integers(0, 5), min_size=1, max_size=len(_PROVIDER_POOL)))
@settings(max_examples=50)
def test_select_totality_matches_weight_zero_rule(weights: list[int]) -> None:
    candidates = [
        _candidate(_PROVIDER_POOL[i], order=i, base_weight=w) for i, w in enumerate(weights)
    ]
    if all(c.effective_weight == 0 for c in candidates):
        with pytest.raises(NoEligibleEngine):
            select(candidates)
    else:
        selection = select(candidates)
        winners = [c for c in candidates if c.provider_id == selection.provider_id]
        assert any(c.effective_weight > 0 for c in winners)


def test_select_rejects_duplicate_provider_ids() -> None:
    duplicated = [
        _candidate("p1", order=0, base_weight=1),
        _candidate("p1", order=1, base_weight=1),
    ]
    with pytest.raises(ValueError, match="unique provider_id"):
        select(duplicated)
